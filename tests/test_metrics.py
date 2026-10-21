"""
Automated Unit Tests for Metric Computation & Delivery Gap Logic
supply_chain_delivery_analysis
"""

import sys
import os
import unittest
import pandas as pd
import numpy as np

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from src.metrics import (
    compute_kpi_summary,
    compute_shipping_mode_metrics,
    compute_regional_delay_index,
    compute_customer_segment_metrics
)
from src.data_cleaning import validate_and_clean_data


class TestSupplyChainMetrics(unittest.TestCase):

    def setUp(self):
        # Create a controlled synthetic test dataset with known ground truth
        # Row 1: Real=4, Sched=4 -> Gap=0 (Exact on-time)
        # Row 2: Real=2, Sched=4 -> Gap=-2 (Early)
        # Row 3: Real=5, Sched=4 -> Gap=1 (Delayed, gap=1)
        # Row 4: Real=6, Sched=4 -> Gap=2 (Delayed, gap=2)
        # Row 5: Real=2, Sched=1 -> Gap=1 (Delayed, gap=1)
        self.sample_data = pd.DataFrame({
            'Days for shipping (real)': [4.0, 2.0, 5.0, 6.0, 2.0],
            'Days for shipment (scheduled)': [4.0, 4.0, 4.0, 4.0, 1.0],
            'Late_delivery_risk': [0, 0, 1, 1, 1],
            'Delivery Status': ['Shipping on time', 'Advance shipping', 'Late delivery', 'Late delivery', 'Late delivery'],
            'Shipping Mode': ['Standard Class', 'Standard Class', 'Standard Class', 'Standard Class', 'First Class'],
            'Market': ['Europe', 'Europe', 'LATAM', 'LATAM', 'USCA'],
            'Order Region': ['Western Europe', 'Western Europe', 'South America', 'South America', 'Central America'],
            'Customer Segment': ['Consumer', 'Consumer', 'Corporate', 'Corporate', 'Home Office']
        })
        self.clean_df, _ = validate_and_clean_data(self.sample_data)

    def test_delivery_gap_calculation(self):
        """Verify delivery gap = Real - Scheduled."""
        expected_gaps = [0.0, -2.0, 1.0, 2.0, 1.0]
        np.testing.assert_array_equal(self.clean_df['Delivery_Gap'].values, expected_gaps)

    def test_delivery_outcomes(self):
        """Verify outcome categorical assignment."""
        expected_outcomes = ['On Schedule', 'Early', 'Delayed', 'Delayed', 'Delayed']
        self.assertListEqual(self.clean_df['Delivery_Outcome'].tolist(), expected_outcomes)

    def test_kpi_summary(self):
        """Verify KPI formulas independently."""
        kpis = compute_kpi_summary(self.clean_df)
        
        # Total = 5
        self.assertEqual(kpis['total_shipments'], 5)
        # Delayed = 3 (rows 3, 4, 5) -> 3/5 = 60.0%
        self.assertEqual(kpis['delay_rate'], 60.0)
        # On-Time = 2 (rows 1, 2) -> 2/5 = 40.0%
        self.assertEqual(kpis['ontime_rate'], 40.0)
        # Exact on-time = 1 (row 1) -> 1/5 = 20.0%
        self.assertEqual(kpis['exact_ontime_rate'], 20.0)
        # Early = 1 (row 2) -> 1/5 = 20.0%
        self.assertEqual(kpis['early_rate'], 20.0)
        # Avg delay among delayed = (1 + 2 + 1) / 3 = 4 / 3 = 1.33
        self.assertAlmostEqual(kpis['avg_delay_days'], 1.33, places=2)
        # Avg signed gap = (0 - 2 + 1 + 2 + 1) / 5 = 2 / 5 = 0.40
        self.assertAlmostEqual(kpis['avg_delivery_gap'], 0.40, places=2)
        # Late delivery risk = 3/5 = 60.0%
        self.assertEqual(kpis['late_risk_rate'], 60.0)

    def test_empty_dataframe_handling(self):
        """Ensure empty filtered DataFrames return zeroed metrics without crashing."""
        empty_df = pd.DataFrame(columns=self.clean_df.columns)
        kpis = compute_kpi_summary(empty_df)
        self.assertEqual(kpis['total_shipments'], 0)
        self.assertEqual(kpis['delay_rate'], 0.0)
        self.assertEqual(kpis['avg_delay_days'], 0.0)
        self.assertEqual(kpis['avg_delivery_gap'], 0.0)

    def test_regional_delay_index(self):
        """Verify RDI formula: Regional Delay Rate / Baseline Delay Rate."""
        rdi_df = compute_regional_delay_index(self.clean_df, 'Market')
        # Baseline delay rate = 60%
        # LATAM has 2 shipments, both delayed -> 100% delay rate -> RDI = 1.0 / 0.6 = 1.667
        latam_row = rdi_df[rdi_df['Market'] == 'LATAM'].iloc[0]
        self.assertAlmostEqual(latam_row['Regional Delay Index'], 1.667, places=2)


if __name__ == '__main__':
    unittest.main()
