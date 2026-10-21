"""
Key Performance Indicators and Metrics Definition Module
supply_chain_delivery_analysis

Defines standardized, rigorous KPI calculation functions:
- On-Time Delivery Rate (distinguishing early and exact-on-schedule)
- Delay Rate and Severity (Average Delay among delayed shipments)
- Average Signed Delivery Gap
- Late-Delivery Risk Rate
- Shipping Mode Performance Metrics
- Regional Delay Index (RDI)
- Customer Segment Logistics Breakdown

All metrics use explicit, documented denominators and defensively guard against
empty datasets or division-by-zero errors.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np


def compute_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes global delivery performance KPIs from the provided (or filtered) DataFrame.
    
    Metric Definitions:
    - Total Shipments (N): Total valid records in current scope.
    - On-Time Rate (%): (Shipments with Delivery Gap <= 0) / N * 100.
    - Exact On-Time Rate (%): (Shipments with Delivery Gap == 0) / N * 100.
    - Early Delivery Rate (%): (Shipments with Delivery Gap < 0) / N * 100.
    - Delay Rate (%): (Shipments with Delivery Gap > 0) / N * 100.
    - Average Delay (days): Sum of positive delivery gaps / Number of delayed shipments.
      Denominator: Number of delayed shipments (strictly > 0 days).
    - Average Delivery Gap (days): Sum of signed delivery gaps / N.
      Denominator: Total shipments in current scope.
    - Late-Delivery Risk Rate (%): (Records with Late_delivery_risk == 1) / N * 100.
    
    Args:
        df: Cleaned supply chain DataFrame.
        
    Returns:
        Dict[str, Any]: Calculated KPI values and breakdown counts.
    """
    total_shipments = len(df)
    
    if total_shipments == 0:
        return {
            'total_shipments': 0,
            'ontime_rate': 0.0,
            'exact_ontime_rate': 0.0,
            'early_rate': 0.0,
            'delay_rate': 0.0,
            'avg_delay_days': 0.0,
            'avg_delivery_gap': 0.0,
            'delayed_count': 0,
            'ontime_count': 0,
            'exact_ontime_count': 0,
            'early_count': 0,
            'late_risk_rate': 0.0,
            'late_risk_count': 0,
            'has_risk_field': 'Late_delivery_risk' in df.columns
        }
        
    # Vectorized counts
    is_delayed = df['Delivery_Gap'] > 0
    is_exact_ontime = df['Delivery_Gap'] == 0
    is_early = df['Delivery_Gap'] < 0
    is_ontime = df['Delivery_Gap'] <= 0
    
    delayed_count = int(is_delayed.sum())
    exact_ontime_count = int(is_exact_ontime.sum())
    early_count = int(is_early.sum())
    ontime_count = int(is_ontime.sum())
    
    # Rates
    ontime_rate = (ontime_count / total_shipments) * 100.0
    exact_ontime_rate = (exact_ontime_count / total_shipments) * 100.0
    early_rate = (early_count / total_shipments) * 100.0
    delay_rate = (delayed_count / total_shipments) * 100.0
    
    # Average delay among delayed deliveries (denominator: delayed_count)
    if delayed_count > 0:
        avg_delay_days = float(df.loc[is_delayed, 'Delivery_Gap'].mean())
    else:
        avg_delay_days = 0.0
        
    # Average signed delivery gap across all deliveries (denominator: total_shipments)
    avg_delivery_gap = float(df['Delivery_Gap'].mean())
    
    # Late delivery risk rate
    if 'Late_delivery_risk' in df.columns:
        late_risk_count = int((df['Late_delivery_risk'] == 1).sum())
        late_risk_rate = (late_risk_count / total_shipments) * 100.0
        has_risk_field = True
    else:
        late_risk_count = 0
        late_risk_rate = 0.0
        has_risk_field = False
        
    return {
        'total_shipments': total_shipments,
        'ontime_rate': round(ontime_rate, 2),
        'exact_ontime_rate': round(exact_ontime_rate, 2),
        'early_rate': round(early_rate, 2),
        'delay_rate': round(delay_rate, 2),
        'avg_delay_days': round(avg_delay_days, 2),
        'avg_delivery_gap': round(avg_delivery_gap, 2),
        'delayed_count': delayed_count,
        'ontime_count': ontime_count,
        'exact_ontime_count': exact_ontime_count,
        'early_count': early_count,
        'late_risk_rate': round(late_risk_rate, 2),
        'late_risk_count': late_risk_count,
        'has_risk_field': has_risk_field
    }


def compute_shipping_mode_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes comparative logistics performance across Shipping Modes.
    
    Avoids ranking modes solely by averages by including total shipment volume,
    volume share, and exact count denominators.
    """
    if len(df) == 0:
        return pd.DataFrame()
        
    total_volume = len(df)
    
    grouped = df.groupby('Shipping Mode', as_index=False).apply(
        lambda g: pd.Series({
            'Shipment Volume': len(g),
            'Volume Share (%)': round(len(g) / total_volume * 100.0, 2),
            'On-Time Rate (%)': round((g['Delivery_Gap'] <= 0).mean() * 100.0, 2),
            'Exact On-Time (%)': round((g['Delivery_Gap'] == 0).mean() * 100.0, 2),
            'Early Rate (%)': round((g['Delivery_Gap'] < 0).mean() * 100.0, 2),
            'Delay Rate (%)': round((g['Delivery_Gap'] > 0).mean() * 100.0, 2),
            'Avg Delay (days)': round(g.loc[g['Delivery_Gap'] > 0, 'Delivery_Gap'].mean(), 2) if (g['Delivery_Gap'] > 0).any() else 0.0,
            'Avg Delivery Gap (days)': round(g['Delivery_Gap'].mean(), 2),
            'Late Risk Rate (%)': round((g['Late_delivery_risk'] == 1).mean() * 100.0, 2) if 'Late_delivery_risk' in g.columns else np.nan,
            'Scheduled Days': f"{g['Days for shipment (scheduled)'].min():.0f}-{g['Days for shipment (scheduled)'].max():.0f}" if g['Days for shipment (scheduled)'].nunique() > 1 else f"{g['Days for shipment (scheduled)'].iloc[0]:.0f}",
            'Real Days (Min-Max)': f"{g['Days for shipping (real)'].min():.0f}-{g['Days for shipping (real)'].max():.0f}"
        }),
        include_groups=False
    )
    
    return grouped.sort_values(by='Shipment Volume', ascending=False).reset_index(drop=True)


def compute_regional_delay_index(df: pd.DataFrame, region_col: str = 'Order Region') -> pd.DataFrame:
    """
    Calculates the Regional Delay Index (RDI) for geographical dimensions.
    
    Transparent Formula:
    RDI = (Regional Delay Rate) / (Baseline Overall Delay Rate)
    
    Interpretation:
    - RDI > 1.00: Region suffers higher delay frequency than overall organization average.
    - RDI = 1.00: Regional delivery punctuality matches the baseline exactly.
    - RDI < 1.00: Region performs better (fewer delays) than overall average.
    """
    if len(df) == 0:
        return pd.DataFrame()
        
    total_records = len(df)
    overall_delayed = (df['Delivery_Gap'] > 0).sum()
    baseline_delay_rate = (overall_delayed / total_records) if total_records > 0 else 0.0
    
    if region_col not in df.columns:
        raise KeyError(f"Column '{region_col}' not found in DataFrame.")
        
    grouped = df.groupby(region_col, as_index=False).apply(
        lambda g: pd.Series({
            'Total Shipments': len(g),
            'Delayed Shipments': int((g['Delivery_Gap'] > 0).sum()),
            'Delay Rate (%)': round((g['Delivery_Gap'] > 0).mean() * 100.0, 2),
            'On-Time Rate (%)': round((g['Delivery_Gap'] <= 0).mean() * 100.0, 2),
            'Avg Delay (days)': round(g.loc[g['Delivery_Gap'] > 0, 'Delivery_Gap'].mean(), 2) if (g['Delivery_Gap'] > 0).any() else 0.0,
            'Avg Delivery Gap (days)': round(g['Delivery_Gap'].mean(), 2),
            'Regional Delay Index': round(((g['Delivery_Gap'] > 0).mean() / baseline_delay_rate), 3) if baseline_delay_rate > 0 else 1.00
        }),
        include_groups=False
    )
    
    return grouped.sort_values(by='Regional Delay Index', ascending=False).reset_index(drop=True)


def compute_customer_segment_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluates logistics performance across customer segments (Consumer, Corporate, Home Office).
    """
    if len(df) == 0:
        return pd.DataFrame()
        
    total_volume = len(df)
    
    grouped = df.groupby('Customer Segment', as_index=False).apply(
        lambda g: pd.Series({
            'Shipment Volume': len(g),
            'Volume Share (%)': round(len(g) / total_volume * 100.0, 2),
            'Delay Rate (%)': round((g['Delivery_Gap'] > 0).mean() * 100.0, 2),
            'On-Time Rate (%)': round((g['Delivery_Gap'] <= 0).mean() * 100.0, 2),
            'Avg Delay (days)': round(g.loc[g['Delivery_Gap'] > 0, 'Delivery_Gap'].mean(), 2) if (g['Delivery_Gap'] > 0).any() else 0.0,
            'Avg Delivery Gap (days)': round(g['Delivery_Gap'].mean(), 2),
            'Late Risk Rate (%)': round((g['Late_delivery_risk'] == 1).mean() * 100.0, 2) if 'Late_delivery_risk' in g.columns else np.nan
        }),
        include_groups=False
    )
    
    return grouped.sort_values(by='Shipment Volume', ascending=False).reset_index(drop=True)
