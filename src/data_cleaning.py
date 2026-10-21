"""
Data Cleaning, Validation, and Preprocessing Module
supply_chain_delivery_analysis

Handles dataset loading, validation, missing-value imputation, data-type conversion,
delivery gap calculation, and identification of data quality nuances.
"""

import os
from typing import Dict, Any, Tuple
import pandas as pd
import numpy as np


# Recommended column mapping for supply chain analysis
KEY_NUMERIC_COLS = [
    'Days for shipping (real)',
    'Days for shipment (scheduled)',
    'Benefit per order',
    'Sales per customer',
    'Order Item Discount',
    'Order Item Discount Rate',
    'Order Item Product Price',
    'Order Item Profit Ratio',
    'Order Item Quantity',
    'Sales',
    'Order Item Total',
    'Order Profit Per Order',
    'Product Price'
]

PII_COLUMNS = [
    'Customer Fname',
    'Customer Lname',
    'Customer Street',
    'Customer Zipcode'
]

REDUNDANT_PAIRS = [
    ('Sales per customer', 'Order Item Total'),
    ('Benefit per order', 'Order Profit Per Order'),
    ('Product Price', 'Order Item Product Price'),
    ('Customer Id', 'Order Customer Id')
]


def load_raw_data(filepath: str) -> pd.DataFrame:
    """
    Loads raw supply chain CSV file with fallback encoding support.
    
    Args:
        filepath: Path to the raw CSV dataset.
        
    Returns:
        pd.DataFrame: Loaded raw dataset.
        
    Raises:
        FileNotFoundError: If the specified file does not exist.
        ValueError: If file cannot be decoded with standard encodings.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"Dataset not found at: {filepath}. Please ensure the CSV is placed in data/."
        )
    
    encodings = ['latin1', 'iso-8859-1', 'cp1252', 'utf-8']
    for enc in encodings:
        try:
            df = pd.read_csv(filepath, encoding=enc, low_memory=False)
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise RuntimeError(f"Error reading {filepath} with encoding {enc}: {e}")
            
    raise ValueError(f"Unable to decode {filepath} using standard encodings: {encodings}")


def validate_and_clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans, validates, and computes delivery metrics on the raw dataset.
    
    Cleaning steps:
    1. Validates presence of critical shipping fields.
    2. Imputes minor missing values in Customer fields (documented).
    3. Converts shipping days to float and validates non-negative bounds.
    4. Computes signed Delivery Gap: Real - Scheduled.
    5. Categorizes Delivery Outcomes: Early, On Schedule, Delayed.
    6. Verifies Late_delivery_risk encoding (0 or 1).
    7. Documents data quality checks and redundant column pairs.
    
    Args:
        df: Raw pandas DataFrame.
        
    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned DataFrame and Data Quality summary report.
    """
    # Create working copy without mutating original
    clean_df = df.copy()
    
    total_raw_rows = len(clean_df)
    total_raw_cols = len(clean_df.columns)
    
    # 1. Missing value assessment
    missing_counts = clean_df.isnull().sum()
    missing_report = {col: int(cnt) for col, cnt in missing_counts.items() if cnt > 0}
    
    # Impute documented missing values
    if 'Customer Lname' in clean_df.columns:
        clean_df['Customer Lname'] = clean_df['Customer Lname'].fillna('Unknown')
        
    if 'Customer Zipcode' in clean_df.columns:
        clean_df['Customer Zipcode'] = clean_df['Customer Zipcode'].fillna(0).astype(str)
        
    # 2. Check for exact duplicate rows
    duplicate_count = int(clean_df.duplicated().sum())
    
    # 3. Validate shipping day columns
    if 'Days for shipping (real)' not in clean_df.columns or 'Days for shipment (scheduled)' not in clean_df.columns:
        raise KeyError("Dataset is missing mandatory shipping day columns: 'Days for shipping (real)' or 'Days for shipment (scheduled)'")
        
    clean_df['Days for shipping (real)'] = pd.to_numeric(clean_df['Days for shipping (real)'], errors='coerce')
    clean_df['Days for shipment (scheduled)'] = pd.to_numeric(clean_df['Days for shipment (scheduled)'], errors='coerce')
    
    # Check for invalid/impossible negative days
    invalid_shipping_mask = (clean_df['Days for shipping (real)'] < 0) | (clean_df['Days for shipment (scheduled)'] < 0)
    invalid_shipping_count = int(invalid_shipping_mask.sum())
    
    # 4. Compute Delivery Gap
    # Delivery Gap = Actual Shipping Days - Scheduled Shipping Days
    clean_df['Delivery_Gap'] = clean_df['Days for shipping (real)'] - clean_df['Days for shipment (scheduled)']
    
    # 5. Define Delivery Outcome Categories
    # Gap > 0 -> Delayed
    # Gap == 0 -> On Schedule
    # Gap < 0 -> Early
    conditions = [
        clean_df['Delivery_Gap'] > 0,
        clean_df['Delivery_Gap'] == 0,
        clean_df['Delivery_Gap'] < 0
    ]
    choices = ['Delayed', 'On Schedule', 'Early']
    clean_df['Delivery_Outcome'] = np.select(conditions, choices, default='Unknown')
    
    # Binary indicator flags for high-performance vectorized metric aggregation
    clean_df['Is_Delayed'] = (clean_df['Delivery_Gap'] > 0).astype(int)
    clean_df['Is_On_Time'] = (clean_df['Delivery_Gap'] <= 0).astype(int)
    clean_df['Is_Exact_On_Time'] = (clean_df['Delivery_Gap'] == 0).astype(int)
    clean_df['Is_Early'] = (clean_df['Delivery_Gap'] < 0).astype(int)
    
    # 6. Verify Late_delivery_risk field
    has_risk_field = 'Late_delivery_risk' in clean_df.columns
    if has_risk_field:
        clean_df['Late_delivery_risk'] = pd.to_numeric(clean_df['Late_delivery_risk'], errors='coerce').fillna(0).astype(int)
        risk_distribution = clean_df['Late_delivery_risk'].value_counts().to_dict()
    else:
        risk_distribution = {}
        
    # 7. Standardize text categories
    cat_columns = ['Shipping Mode', 'Customer Segment', 'Market', 'Order Region', 'Delivery Status', 'Type', 'Order Status']
    for col in cat_columns:
        if col in clean_df.columns:
            clean_df[col] = clean_df[col].astype(str).str.strip()
            
    # Compile comprehensive data quality summary
    quality_report = {
        'total_rows': total_raw_rows,
        'total_cols': total_raw_cols,
        'duplicate_rows': duplicate_count,
        'missing_values': missing_report,
        'invalid_shipping_records': invalid_shipping_count,
        'has_late_delivery_risk': has_risk_field,
        'risk_distribution': risk_distribution,
        'date_columns_present': False,  # APL_Logistics.csv contains 40 columns without date/timestamp fields
        'redundant_columns': REDUNDANT_PAIRS,
        'pii_columns': [c for c in PII_COLUMNS if c in clean_df.columns]
    }
    
    return clean_df, quality_report


if __name__ == '__main__':
    data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'APL_Logistics.csv')
    print(f"Testing data cleaning pipeline on: {data_file}")
    raw_df = load_raw_data(data_file)
    cleaned_df, report = validate_and_clean_data(raw_df)
    print("Cleaned DataFrame Shape:", cleaned_df.shape)
    print("Quality Report:", report)
