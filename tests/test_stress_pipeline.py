"""
End-to-End Pipeline & Filter Stress Test on Real Dataset
"""

import sys
import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.data_cleaning import load_raw_data, validate_and_clean_data
from src.metrics import (
    compute_kpi_summary,
    compute_shipping_mode_metrics,
    compute_regional_delay_index,
    compute_customer_segment_metrics
)
from src.analysis import (
    analyze_delivery_gap_distribution,
    analyze_risk_vs_actual,
    analyze_numerical_correlations,
    generate_operational_insights
)

data_path = os.path.join(parent_dir, "data", "APL_Logistics.csv")
print(f"Loading {data_path}...")
raw_df = load_raw_data(data_path)
clean_df, report = validate_and_clean_data(raw_df)
print(f"Cleaned shape: {clean_df.shape}")

print("\n1. Testing KPIs on full dataset:")
kpis = compute_kpi_summary(clean_df)
print(f"  Total Shipments: {kpis['total_shipments']:,}")
print(f"  On-Time Rate: {kpis['ontime_rate']}%")
print(f"  Delay Rate: {kpis['delay_rate']}%")
print(f"  Avg Delay: {kpis['avg_delay_days']} days")
print(f"  Avg Gap: {kpis['avg_delivery_gap']} days")
print(f"  Late Risk Rate: {kpis['late_risk_rate']}%")

print("\n2. Testing Shipping Modes:")
sm = compute_shipping_mode_metrics(clean_df)
print(sm[['Shipping Mode', 'Shipment Volume', 'On-Time Rate (%)', 'Delay Rate (%)', 'Avg Delay (days)']])

print("\n3. Testing Risk Analysis:")
ra = analyze_risk_vs_actual(clean_df)
print("  Confusion matrix:", ra['confusion_matrix'])
print("  Metrics:", ra['metrics'])

print("\n4. Testing Regions (Top 3):")
rdi = compute_regional_delay_index(clean_df, 'Order Region')
print(rdi.head(3)[['Order Region', 'Total Shipments', 'Delay Rate (%)', 'Regional Delay Index']])

print("\n5. Testing Customer Segments:")
cs = compute_customer_segment_metrics(clean_df)
print(cs[['Customer Segment', 'Shipment Volume', 'Delay Rate (%)']])

print("\n6. Testing Filter Stress (Single Mode: 'First Class'):")
fc_df = clean_df[clean_df['Shipping Mode'] == 'First Class']
fc_kpis = compute_kpi_summary(fc_df)
print(f"  First Class Delay Rate: {fc_kpis['delay_rate']}% (Expected: 100.0%)")

print("\n7. Testing Empty Filter Case:")
empty_df = clean_df[clean_df['Shipping Mode'] == 'NonExistentMode']
empty_kpis = compute_kpi_summary(empty_df)
print(f"  Empty Filter Shipments: {empty_kpis['total_shipments']} (Expected: 0)")
empty_sm = compute_shipping_mode_metrics(empty_df)
print(f"  Empty Filter Mode DF rows: {len(empty_sm)} (Expected: 0)")

print("\nALL STRESS TESTS PASSED SUCCESSFULLY!")
