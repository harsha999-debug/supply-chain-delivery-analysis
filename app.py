"""
Global Supply Chain Delivery Performance & Delay Risk Dashboard
Unified Mentor Machine Learning Fellowship Project

A production-grade, interactive Streamlit analytics platform for diagnosing
delivery performance, transit delay risk, and logistics efficiency.
"""

import os
import sys
from typing import Dict, Any, List
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path so src modules import reliably
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.data_cleaning import load_raw_data, validate_and_clean_data, PII_COLUMNS
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

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Supply Chain Delivery Performance Dashboard",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern UI design
st.markdown("""
<style>
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 12px;
    }
    .metric-card-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-card-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-card-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 6px;
    }
    .badge-delayed {
        color: #b91c1c;
        background-color: #fee2e2;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .badge-ontime {
        color: #15803d;
        background-color: #dcfce7;
        padding: 2px 8px;
        border-radius: 4px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        font-weight: 600;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Cached Data Loading & Cleaning
# ---------------------------------------------------------
@st.cache_data(show_spinner="Loading and validating supply chain dataset...")
def get_clean_dataset():
    data_dir = os.path.join(current_dir, "data")
    candidates = [
        os.path.join(data_dir, "APL_Logistics.parquet"),
        os.path.join(data_dir, "APL_Logistics.csv"),
        os.path.join(data_dir, "APL_Logistics.csv.gz")
    ]
    data_path = None
    for cand in candidates:
        if os.path.exists(cand):
            data_path = cand
            break
            
    if not data_path and os.path.exists(data_dir):
        # Fallback search for any parquet or csv in data/
        files = [f for f in os.listdir(data_dir) if f.endswith(('.parquet', '.csv', '.csv.gz'))]
        if files:
            data_path = os.path.join(data_dir, files[0])
            
    if not data_path:
        return None, {"error": "Dataset file not found in data/ directory."}
            
    raw_df = load_raw_data(data_path)
    clean_df, quality_report = validate_and_clean_data(raw_df)
    return clean_df, quality_report


df_master, quality_report = get_clean_dataset()

if df_master is None:
    st.error("⚠️ **Dataset Not Found**")
    st.info("Please place `APL_Logistics.csv` (or your supply chain dataset) inside the `data/` folder and reload the dashboard.")
    st.stop()


# ---------------------------------------------------------
# Sidebar Filters & Control Panel
# ---------------------------------------------------------
st.sidebar.title("🎛️ Filter Controls")
st.sidebar.caption("Filter records dynamically across all modules.")

# Reset Filters Button
if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
    for key in list(st.session_state.keys()):
        if key.startswith("filter_"):
            del st.session_state[key]
    st.rerun()

# 1. Shipping Mode
available_modes = sorted(df_master['Shipping Mode'].unique().tolist())
selected_modes = st.sidebar.multiselect(
    "Shipping Mode",
    options=available_modes,
    default=available_modes,
    key="filter_mode"
)

# 2. Market
available_markets = sorted(df_master['Market'].unique().tolist())
selected_markets = st.sidebar.multiselect(
    "Market",
    options=available_markets,
    default=available_markets,
    key="filter_market"
)

# 3. Order Region (cascading from selected markets)
if selected_markets:
    available_regions = sorted(df_master[df_master['Market'].isin(selected_markets)]['Order Region'].unique().tolist())
else:
    available_regions = sorted(df_master['Order Region'].unique().tolist())
    
selected_regions = st.sidebar.multiselect(
    "Order Region",
    options=available_regions,
    default=available_regions,
    key="filter_region"
)

# 4. Customer Segment
available_segments = sorted(df_master['Customer Segment'].unique().tolist())
selected_segments = st.sidebar.multiselect(
    "Customer Segment",
    options=available_segments,
    default=available_segments,
    key="filter_segment"
)

# 5. Delivery Status
available_statuses = sorted(df_master['Delivery Status'].unique().tolist())
selected_statuses = st.sidebar.multiselect(
    "Delivery Status",
    options=available_statuses,
    default=available_statuses,
    key="filter_status"
)

# 6. Late Delivery Risk Filter
risk_choice = st.sidebar.radio(
    "Late Delivery Risk Filter",
    options=["All Records", "Late Delivery Risk = 1", "Late Delivery Risk = 0"],
    index=0,
    key="filter_risk"
)

# 7. Delivery Outcome Tier
outcome_options = ["All Outcomes", "Early (< 0 days)", "On Schedule (0 days)", "Delayed (> 0 days)"]
selected_outcome = st.sidebar.selectbox(
    "Delivery Outcome Filter",
    options=outcome_options,
    index=0,
    key="filter_outcome"
)


# ---------------------------------------------------------
# Data Filtering Execution
# ---------------------------------------------------------
mask = pd.Series(True, index=df_master.index)

if selected_modes:
    mask &= df_master['Shipping Mode'].isin(selected_modes)
else:
    mask &= False

if selected_markets:
    mask &= df_master['Market'].isin(selected_markets)
else:
    mask &= False

if selected_regions:
    mask &= df_master['Order Region'].isin(selected_regions)
else:
    mask &= False

if selected_segments:
    mask &= df_master['Customer Segment'].isin(selected_segments)
else:
    mask &= False

if selected_statuses:
    mask &= df_master['Delivery Status'].isin(selected_statuses)
else:
    mask &= False

if risk_choice == "Late Delivery Risk = 1":
    mask &= (df_master['Late_delivery_risk'] == 1)
elif risk_choice == "Late Delivery Risk = 0":
    mask &= (df_master['Late_delivery_risk'] == 0)

if selected_outcome == "Early (< 0 days)":
    mask &= (df_master['Delivery_Gap'] < 0)
elif selected_outcome == "On Schedule (0 days)":
    mask &= (df_master['Delivery_Gap'] == 0)
elif selected_outcome == "Delayed (> 0 days)":
    mask &= (df_master['Delivery_Gap'] > 0)

df_filtered = df_master[mask].copy()
remaining_count = len(df_filtered)
total_master_count = len(df_master)
pct_remaining = (remaining_count / total_master_count * 100.0) if total_master_count > 0 else 0.0

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Filtered Scope:** `{remaining_count:,}` / `{total_master_count:,}` records (`{pct_remaining:.1f}%`)")
if remaining_count == 0:
    st.sidebar.warning("⚠️ No records match the active filter criteria. Adjust or reset filters above.")


# ---------------------------------------------------------
# Header & Methodology Expander
# ---------------------------------------------------------
st.title("📦 Global Supply Chain Delivery Performance & Delay Risk Analytics")
st.markdown(
    "**Unified Mentor Machine Learning Fellowship** | Fellow: **Harsha Vardhan** (`UMID010926107863`) | "
    "Empirical Logistics, Delay Risk & SLA Diagnostics Platform"
)

with st.expander("ℹ️ **Business Problem, Methodology & Data Architecture (Click to Expand)**"):
    col_a, col_b = st.columns([1, 1])
    with col_a:
        st.markdown("""
        ### The Business Challenge
        In global multi-market supply chains, delivering on scheduled shipping commitments is foundational for customer satisfaction, brand equity, and operational margin. This dashboard evaluates **180,519 fulfillment records** from `APL_Logistics.csv` to diagnose:
        - Actual physical transit time versus promised scheduled shipping days.
        - Commercial shipping mode SLAs and bottlenecks.
        - Global market and regional delay disparities.
        - The relationship between recorded `Late_delivery_risk` and actual delivery outcomes.
        """)
    with col_b:
        st.markdown("""
        ### Rigorous Metric Definitions
        - **Delivery Gap:** `Actual Shipping Days - Scheduled Shipping Days`
          - `Gap > 0`: Delayed | `Gap == 0`: Exactly On Schedule | `Gap < 0`: Early
        - **On-Time Rate:** Percentage with `Delivery Gap <= 0` (Early + Exact).
        - **Delay Rate:** Percentage with `Delivery Gap > 0`.
        - **Average Delay:** Mean positive gap among delayed shipments (in shipping days).
        - **Regional Delay Index (RDI):** `Regional Delay Rate / Overall Baseline Delay Rate (57.28%)`.
        - **Date Limitation Note:** The dataset contains 40 features without date/timestamp columns. Temporal trend charts are intentionally excluded to maintain scientific integrity.
        """)


# Handle empty dataset view
if remaining_count == 0:
    st.warning("⚠️ **Zero records match your current filter selection.** Please broaden your filters in the sidebar or click 'Reset All Filters'.")
    st.stop()


# ---------------------------------------------------------
# Compute Core Analytics on Filtered Data
# ---------------------------------------------------------
kpis = compute_kpi_summary(df_filtered)
gap_analysis = analyze_delivery_gap_distribution(df_filtered)
risk_analysis = analyze_risk_vs_actual(df_filtered)
mode_df = compute_shipping_mode_metrics(df_filtered)
region_df = compute_regional_delay_index(df_filtered, 'Order Region')
market_df = compute_regional_delay_index(df_filtered, 'Market')
segment_df = compute_customer_segment_metrics(df_filtered)
correlations_df = analyze_numerical_correlations(df_filtered)
insights = generate_operational_insights(df_filtered)


# ---------------------------------------------------------
# Dashboard Navigation Tabs
# ---------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 1. Delivery Overview",
    "🎯 2. Delay Risk Diagnostic",
    "🚚 3. Shipping Mode SLAs",
    "🌍 4. Regional & Market Analysis",
    "👥 5. Customer Segments",
    "💡 6. Quality & Strategy"
])


# =========================================================
# TAB 1: DELIVERY OVERVIEW (MODULE 1)
# =========================================================
with tab1:
    st.subheader("Global Delivery Performance Overview")
    st.caption("High-level key performance indicators, outcome distribution, and delivery gap metrics.")
    
    # KPI Row 1
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Total Valid Shipments</div>
            <div class="metric-card-value">{kpis['total_shipments']:,}</div>
            <div class="metric-card-sub">{kpis['total_shipments']/total_master_count*100:.1f}% of full dataset</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">On-Time Delivery Rate</div>
            <div class="metric-card-value" style="color: #16a34a;">{kpis['ontime_rate']:.2f}%</div>
            <div class="metric-card-sub">Exact: <b>{kpis['exact_ontime_rate']:.1f}%</b> | Early: <b>{kpis['early_rate']:.1f}%</b></div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Delay Rate</div>
            <div class="metric-card-value" style="color: #dc2626;">{kpis['delay_rate']:.2f}%</div>
            <div class="metric-card-sub">{kpis['delayed_count']:,} delayed shipments</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Avg Delay (Delayed Only)</div>
            <div class="metric-card-value" style="color: #ea580c;">+{kpis['avg_delay_days']:.2f} <span style="font-size: 1rem;">days</span></div>
            <div class="metric-card-sub">Denominator: {kpis['delayed_count']:,} delayed orders</div>
        </div>
        """, unsafe_allow_html=True)

    # KPI Row 2
    kpi_col5, kpi_col6, kpi_col7, kpi_col8 = st.columns(4)
    
    with kpi_col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Average Signed Gap</div>
            <div class="metric-card-value">{kpis['avg_delivery_gap']:+.2f} <span style="font-size: 1rem;">days</span></div>
            <div class="metric-card-sub">Across all early, on-time & late orders</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col6:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Late-Delivery Risk Rate</div>
            <div class="metric-card-value" style="color: #7c3aed;">{kpis['late_risk_rate']:.2f}%</div>
            <div class="metric-card-sub">{kpis['late_risk_count']:,} records tagged with Risk = 1</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col7:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Early Shipments</div>
            <div class="metric-card-value" style="color: #0d9488;">{kpis['early_count']:,}</div>
            <div class="metric-card-sub">{kpis['early_rate']:.2f}% arrived ahead of schedule</div>
        </div>
        """, unsafe_allow_html=True)
        
    with kpi_col8:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-card-title">Exact On-Time Shipments</div>
            <div class="metric-card-value" style="color: #0284c7;">{kpis['exact_ontime_count']:,}</div>
            <div class="metric-card-sub">{kpis['exact_ontime_rate']:.2f}% arrived on target day</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Visualizations Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("##### 🥧 Delivery Outcome Distribution")
        outcome_df = pd.DataFrame({
            'Outcome': ['Early (< 0 days)', 'Exact On-Schedule (0 days)', 'Delayed (> 0 days)'],
            'Count': [kpis['early_count'], kpis['exact_ontime_count'], kpis['delayed_count']],
            'Color': ['#10b981', '#3b82f6', '#ef4444']
        })
        fig_pie = px.pie(
            outcome_df,
            values='Count',
            names='Outcome',
            color='Outcome',
            color_discrete_map={
                'Early (< 0 days)': '#10b981',
                'Exact On-Schedule (0 days)': '#3b82f6',
                'Delayed (> 0 days)': '#ef4444'
            },
            hole=0.45
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with chart_col2:
        st.markdown("##### 📊 Delivery Gap vs Delivery Status Breakdown")
        status_gap_df = df_filtered.groupby(['Delivery Status', 'Delivery_Outcome']).size().reset_index(name='Count')
        fig_bar = px.bar(
            status_gap_df,
            x='Delivery Status',
            y='Count',
            color='Delivery_Outcome',
            color_discrete_map={
                'Early': '#10b981',
                'On Schedule': '#3b82f6',
                'Delayed': '#ef4444'
            },
            barmode='stack'
        )
        fig_bar.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            xaxis_title="System Delivery Status",
            yaxis_title="Shipment Volume",
            legend_title="Calculated Outcome"
        )
        st.plotly_chart(fig_bar, use_container_width=True)
        
    st.info(
        "📌 **Analytical Note on Temporal Trends:** As confirmed in the data validation phase, "
        "`APL_Logistics.csv` has 40 features and does not contain calendar timestamps or date columns "
        "(e.g., `order date (DateOrders)` / `shipping date (DateOrders)`). Per instructions, temporal trend "
        "charts are omitted rather than generating synthetic dates."
    )


# =========================================================
# TAB 2: DELAY RISK DIAGNOSTIC (MODULE 2)
# =========================================================
with tab2:
    st.subheader("Delay Risk & Gap Severity Diagnostic")
    st.caption("Distribution of signed delivery gaps, severity classification, and diagnostic evaluation of Late_delivery_risk.")
    
    col_risk1, col_risk2 = st.columns(2)
    
    with col_risk1:
        st.markdown("##### 📈 Distribution of Signed Delivery Gaps (Days)")
        gap_freq = gap_analysis['gap_frequencies']
        fig_gap = px.bar(
            gap_freq,
            x='Delivery_Gap',
            y='Shipment_Count',
            text='Percentage',
            color='Delivery_Gap',
            color_continuous_scale=[
                (0.0, '#10b981'),
                (0.33, '#3b82f6'),
                (0.5, '#f59e0b'),
                (1.0, '#ef4444')
            ]
        )
        fig_gap.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_gap.update_layout(
            xaxis_title="Delivery Gap (Actual Days - Scheduled Days)",
            yaxis_title="Shipments",
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_gap, use_container_width=True)
        
    with col_risk2:
        st.markdown("##### 🗂️ Delay Severity Tier Breakdown")
        sev_df = gap_analysis['severity_breakdown']
        fig_sev = px.bar(
            sev_df,
            x='Severity_Tier',
            y='Count',
            text='Share (%)',
            color='Severity_Tier',
            color_discrete_map={
                'Early (-2 to -1 days)': '#10b981',
                'On Schedule (0 days)': '#3b82f6',
                'Minor Delay (1 day)': '#f59e0b',
                'Moderate Delay (2 days)': '#ea580c',
                'Severe Delay (3-4 days)': '#dc2626'
            }
        )
        fig_sev.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_sev.update_layout(
            xaxis_title="Severity Tier",
            yaxis_title="Shipments",
            showlegend=False,
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_sev, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 Late-Delivery Risk vs Actual Delay Diagnostic")
    st.caption("Empirical confusion matrix and classification metrics comparing the recorded `Late_delivery_risk` flag against observed `Delivery_Gap > 0`.")
    
    conf = risk_analysis['confusion_matrix']
    diag_metrics = risk_analysis['metrics']
    
    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
    col_m1.metric("Diagnostic Accuracy", f"{diag_metrics['accuracy']:.1f}%")
    col_m2.metric("Precision", f"{diag_metrics['precision']:.1f}%")
    col_m3.metric("Recall (Sensitivity)", f"{diag_metrics['recall_sensitivity']:.1f}%")
    col_m4.metric("Specificity", f"{diag_metrics['specificity']:.1f}%")
    col_m5.metric("F1-Score", f"{diag_metrics['f1_score']:.3f}")
    
    col_matrix, col_crosstab = st.columns([1, 1.2])
    
    with col_matrix:
        st.markdown("##### 2x2 Confusion Matrix")
        cm_display = pd.DataFrame(
            [
                [conf['TP'], conf['FP']],
                [conf['FN'], conf['TN']]
            ],
            index=["Actual: Delayed (Gap > 0)", "Actual: On-Time (Gap <= 0)"],
            columns=["Predicted: Risk = 1", "Predicted: Risk = 0"]
        )
        st.dataframe(cm_display.style.format("{:,}"), use_container_width=True)
        
    with col_crosstab:
        st.markdown("##### Delivery Status vs Late Delivery Risk Cross-Tab")
        st.dataframe(risk_analysis['status_crosstab'], use_container_width=True)
        
    st.warning(
        f"🔍 **Root Cause of the 4,423 False Negatives:** "
        f"{risk_analysis['discrepancy_explanation']['root_cause']}"
    )


# =========================================================
# TAB 3: SHIPPING MODE SLAS (MODULE 3)
# =========================================================
with tab3:
    st.subheader("Shipping Mode Logistics Performance & SLA Diagnostics")
    st.caption("Evaluating fulfillment efficiency, volume share, scheduled target days, and delay severity across shipping modes.")
    
    st.dataframe(mode_df, use_container_width=True)
    
    st.markdown("---")
    col_sm1, col_sm2 = st.columns(2)
    
    with col_sm1:
        st.markdown("##### 📊 On-Time Rate vs Delay Rate by Shipping Mode")
        fig_mode_rates = go.Figure()
        fig_mode_rates.add_trace(go.Bar(
            name='On-Time Rate (%)',
            x=mode_df['Shipping Mode'],
            y=mode_df['On-Time Rate (%)'],
            marker_color='#10b981',
            text=mode_df['On-Time Rate (%)'].apply(lambda v: f"{v:.1f}%"),
            textposition='inside'
        ))
        fig_mode_rates.add_trace(go.Bar(
            name='Delay Rate (%)',
            x=mode_df['Shipping Mode'],
            y=mode_df['Delay Rate (%)'],
            marker_color='#ef4444',
            text=mode_df['Delay Rate (%)'].apply(lambda v: f"{v:.1f}%"),
            textposition='inside'
        ))
        fig_mode_rates.update_layout(
            barmode='group',
            xaxis_title="Shipping Mode",
            yaxis_title="Percentage (%)",
            yaxis_range=[0, 105],
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_mode_rates, use_container_width=True)
        
    with col_sm2:
        st.markdown("##### ⏱️ Average Delay Severity vs Average Signed Gap (Days)")
        fig_mode_delays = go.Figure()
        fig_mode_delays.add_trace(go.Bar(
            name='Avg Delay (Delayed Only)',
            x=mode_df['Shipping Mode'],
            y=mode_df['Avg Delay (days)'],
            marker_color='#f59e0b',
            text=mode_df['Avg Delay (days)'].apply(lambda v: f"{v:.2f}d"),
            textposition='inside'
        ))
        fig_mode_delays.add_trace(go.Bar(
            name='Avg Signed Delivery Gap',
            x=mode_df['Shipping Mode'],
            y=mode_df['Avg Delivery Gap (days)'],
            marker_color='#6366f1',
            text=mode_df['Avg Delivery Gap (days)'].apply(lambda v: f"{v:+.2f}d"),
            textposition='inside'
        ))
        fig_mode_delays.update_layout(
            barmode='group',
            xaxis_title="Shipping Mode",
            yaxis_title="Days",
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_mode_delays, use_container_width=True)

    st.error("""
    🚨 **Critical SLA Discovery: The First Class 1-Day Promise Fallacy**
    - **First Class:** In 100% of the 27,814 First Class shipments, scheduled delivery was set to **1.0 day**, but actual transit was **2.0 days**, resulting in a **100% delay rate**. The network physically does not support next-day delivery under current routing.
    - **Second Class:** Scheduled for **2.0 days**, but transit requires **2 to 6 days** (averaging 4.5 days), yielding a **79.73% delay rate** with an average delay of 2.50 days.
    - **Standard Class:** By providing a realistic **4.0-day buffer**, Standard Class fulfills **60.23% of orders on time** and carries 59.7% of total volume.
    """)


# =========================================================
# TAB 4: REGIONAL & MARKET ANALYSIS (MODULE 4)
# =========================================================
with tab4:
    st.subheader("Geographic & Regional Delay Index Analysis")
    st.caption("Market-level performance and Regional Delay Index (RDI) comparing regional delay rates against the baseline.")
    
    col_geo1, col_geo2 = st.columns([1, 1.3])
    
    with col_geo1:
        st.markdown("##### 🌐 Market Performance Summary")
        st.dataframe(market_df, use_container_width=True)
        
    with col_geo2:
        st.markdown("##### 📊 Regional Delay Index (RDI) by Order Region")
        fig_rdi = px.bar(
            region_df,
            x='Regional Delay Index',
            y='Order Region',
            orientation='h',
            color='Regional Delay Index',
            color_continuous_scale=[(0.0, '#10b981'), (0.5, '#3b82f6'), (1.0, '#ef4444')],
            text='Regional Delay Index'
        )
        fig_rdi.add_vline(x=1.00, line_dash="dash", line_color="black", annotation_text="Baseline (1.00)")
        fig_rdi.update_traces(texttemplate='%{text:.2f}', textposition='outside')
        fig_rdi.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="Regional Delay Index (RDI)",
            coloraxis_showscale=False,
            margin=dict(t=20, b=20, l=10, r=10),
            height=600
        )
        st.plotly_chart(fig_rdi, use_container_width=True)

    st.markdown("---")
    st.markdown("##### 🏆 Best vs Worst Performing Regions")
    col_best, col_worst = st.columns(2)
    with col_best:
        st.markdown("**Top 5 Punctual Regions (Lowest RDI):**")
        st.dataframe(region_df.tail(5)[['Order Region', 'Total Shipments', 'Delay Rate (%)', 'On-Time Rate (%)', 'Regional Delay Index']].reset_index(drop=True), use_container_width=True)
    with col_worst:
        st.markdown("**Top 5 High-Delay Regions (Highest RDI):**")
        st.dataframe(region_df.head(5)[['Order Region', 'Total Shipments', 'Delay Rate (%)', 'On-Time Rate (%)', 'Regional Delay Index']].reset_index(drop=True), use_container_width=True)
        
    st.info(
        "🗺️ **Geographic Coordinate Validation:** "
        "The coordinates (`Latitude` and `Longitude`) in this dataset represent customer originating locations "
        "(predominantly Puerto Rico and US mainland), while `Order City` and `Order Country` represent global "
        "destinations. Displaying customer coordinates as delivery destinations would be misleading; "
        "hence, geographical evaluation is transparently structured by destination `Market` and `Order Region`."
    )


# =========================================================
# TAB 5: CUSTOMER SEGMENTS (MODULE 5)
# =========================================================
with tab5:
    st.subheader("Customer Segment Logistics Efficiency")
    st.caption("Comparing fulfillment metrics across Consumer, Corporate, and Home Office accounts.")
    
    st.dataframe(segment_df, use_container_width=True)
    
    st.markdown("---")
    col_seg1, col_seg2 = st.columns(2)
    
    with col_seg1:
        st.markdown("##### 👥 Shipment Volume Share by Segment")
        fig_seg_pie = px.pie(
            segment_df,
            values='Shipment Volume',
            names='Customer Segment',
            color='Customer Segment',
            color_discrete_sequence=['#3b82f6', '#10b981', '#f59e0b'],
            hole=0.4
        )
        fig_seg_pie.update_traces(textinfo='percent+label')
        fig_seg_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
        st.plotly_chart(fig_seg_pie, use_container_width=True)
        
    with col_seg2:
        st.markdown("##### ⏱️ Delay Rate & Average Delay Across Segments")
        fig_seg_bar = go.Figure()
        fig_seg_bar.add_trace(go.Bar(
            name='Delay Rate (%)',
            x=segment_df['Customer Segment'],
            y=segment_df['Delay Rate (%)'],
            marker_color='#ef4444',
            text=segment_df['Delay Rate (%)'].apply(lambda v: f"{v:.1f}%"),
            textposition='inside'
        ))
        fig_seg_bar.add_trace(go.Bar(
            name='Avg Delay (days)',
            x=segment_df['Customer Segment'],
            y=segment_df['Avg Delay (days)'],
            marker_color='#f59e0b',
            text=segment_df['Avg Delay (days)'].apply(lambda v: f"{v:.2f}d"),
            textposition='inside'
        ))
        fig_seg_bar.update_layout(
            barmode='group',
            xaxis_title="Customer Segment",
            margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig_seg_bar, use_container_width=True)

    st.success("""
    💡 **Customer Segment Parity Finding:** 
    Across Consumer (57.29%), Corporate (57.11%), and Home Office (57.52%), delay rates differ by less than 0.4%. 
    Logistics fulfillment handles all commercial accounts through the same dispatch pipelines without preferential priority.
    """)


# =========================================================
# TAB 6: QUALITY & STRATEGY (MODULE 6)
# =========================================================
with tab6:
    st.subheader("Data Quality Audit, Correlations & Strategic Recommendations")
    st.caption("Verifying dataset health, correlation analysis, and evidence-grounded operational guidance.")
    
    # Data Quality Card
    st.markdown("##### 📋 Data Quality & Hygiene Summary")
    q_col1, q_col2, q_col3, q_col4 = st.columns(4)
    q_col1.metric("Total Raw Records", f"{quality_report['total_rows']:,}")
    q_col2.metric("Total Columns", f"{quality_report['total_cols']}")
    q_col3.metric("Duplicate Rows", f"{quality_report['duplicate_rows']}")
    q_col4.metric("Invalid Shipping Days", f"{quality_report['invalid_shipping_records']}")
    
    with st.expander("🔍 **View Detailed Data Hygiene Report**"):
        st.write("**Documented Missing Values:**", quality_report['missing_values'])
        st.write("**Redundant Feature Pairs:**", quality_report['redundant_columns'])
        st.write("**Protected Customer PII Features (Masked):**", quality_report['pii_columns'])
        
    st.markdown("---")
    
    # Correlation Analysis
    st.markdown("##### 📈 Correlation Analysis: What Actually Drives Delivery Gaps?")
    col_corr1, col_corr2 = st.columns([1.2, 1])
    
    with col_corr1:
        st.dataframe(correlations_df[['Correlation with Delivery Gap']], use_container_width=True)
        
    with col_corr2:
        st.markdown("""
        **Key Correlation Findings:**
        - **Order Item Total / Sales:** $r = -0.0040$ (No correlation)
        - **Order Item Discount Rate:** $r = +0.0015$ (No correlation)
        - **Order Item Quantity:** $r = +0.0018$ (No correlation)
        - **Benefit per Order / Profit:** $r = -0.0054$ (No correlation)
        - **Late_delivery_risk:** $r = +0.7776$ (Strong correlation)
        
        *Interpretation:* Order size, price, and financial margin have no bearing on fulfillment speed. Delivery gaps are 100% governed by physical transit logistics and shipping mode SLAs.
        """)

    st.markdown("---")
    
    # Dynamic Operational Insights
    st.markdown("##### 🧠 Dynamic Operational Findings (Based on Active Filters)")
    for ins in insights:
        st.info(f"**{ins['title']}**\n\n{ins['content']}")
        
    st.markdown("---")
    
    # Strategic Recommendations
    st.markdown("##### 🎯 Strategic C-Suite Recommendations")
    rec1, rec2, rec3 = st.columns(3)
    
    with rec1:
        st.markdown("""
        **1. Recalibrate First Class SLA**  
        Immediately update promised First Class transit time from 1 day to 2 days. This eliminates an artificial 100% delay rate and lifts global on-time fulfillment by 15.4 percentage points.
        """)
        
    with rec2:
        st.markdown("""
        **2. Overhaul Second Class Carrier SLAs**  
        Extend Second Class promise window from 2 to 3-4 days, or establish enforceable SLA penalty clauses with contracted carriers whose deliveries stretch to 6 days.
        """)
        
    with rec3:
        st.markdown("""
        **3. Segregate Canceled Orders**  
        Update operational data ingestion to isolate canceled dispatches before computing fulfillment metrics, eliminating 4,423 false delay records.
        """)

    st.markdown("---")
    
    # Export Data (PII Protected)
    st.markdown("##### 📥 Export Filtered Dataset")
    export_cols = [c for c in df_filtered.columns if c not in PII_COLUMNS]
    export_csv = df_filtered[export_cols].head(5000).to_csv(index=False).encode('utf-8')
    st.download_button(
        label="⬇️ Download Filtered Data Sample (Top 5,000 Rows, PII Masked)",
        data=export_csv,
        file_name="supply_chain_filtered_sample.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("---")
st.caption("Unified Mentor Machine Learning Fellowship — Supply Chain Delivery Performance Project | Fellow: Harsha Vardhan (UMID010926107863) | Built with Python & Streamlit")
