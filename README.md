# Delivery Performance, Delay Risk, and Logistics Efficiency Analysis in Global Supply Chain Operations

**Unified Mentor Machine Learning Fellowship — Capstone Project**  
*Senior Data Science, Logistics Analytics & Interactive Streamlit Dashboard*

---

## 1. Project Overview
This repository delivers an end-to-end, empirical analytics solution and production-ready Streamlit dashboard designed to evaluate global supply-chain delivery performance, diagnose late-delivery risk, and expose fulfillment bottlenecks across **180,519 real transactions** (~59.6 MB).

Rather than displaying superficial charts, the platform provides rigorous, mathematically verified diagnostics that decouple marketing SLA promises from physical logistics capabilities.

---

## 2. Directory Architecture
```text
supply_chain_delivery_analysis/
├── data/
│   ├── .gitkeep
│   └── APL_Logistics.csv            # Original dataset (~59.6 MB, Latin-1 encoding)
├── src/
│   ├── data_cleaning.py             # Data loading, validation, PII masking & gap calculations
│   ├── analysis.py                  # Statistical distribution, SLA diagnostics & correlations
│   └── metrics.py                   # Standardized KPI definitions, denominators & RDI index
├── reports/
│   ├── findings.md                  # Comprehensive technical findings & analysis report
│   └── executive_summary.md         # C-Suite executive briefing & operational recommendations
├── tests/
│   ├── test_metrics.py              # Automated unit tests for metric correctness
│   └── test_stress_pipeline.py      # End-to-end stress test across real dataset & edge filters
├── app.py                           # 6-module interactive Streamlit dashboard
├── requirements.txt                 # Clean, verified dependency manifest
├── README.md                        # Documentation, methodology & setup guide
└── .gitignore                       # Standard rules protecting raw datasets and environments
```

---

## 3. Dataset Characteristics & Hygiene Summary

- **File Name:** `APL_Logistics.csv` (placed in `data/`)
- **File Size:** 62,500,190 bytes (~59.60 MB)
- **Rows & Columns:** 180,519 rows × 40 features
- **Encoding:** Latin-1 (`iso-8859-1` / `cp1252`)
- **Missing Values:**
  - `Customer Lname`: 8 missing records (0.004%). Imputed with `'Unknown'`.
  - `Customer Zipcode`: 3 missing records (0.002%). Imputed with `'0'`.
  - All other 38 features are 100% complete.
- **Duplicates:** 0 exact duplicate rows.
- **Data Integrity:** `Days for shipping (real)` ranges from 0 to 6 days. `Days for shipment (scheduled)` ranges from 0 to 4 days. No negative or impossible values exist.
- **Redundant Features Identified:** `Sales per customer` == `Order Item Total`, `Benefit per order` == `Order Profit Per Order`, `Product Price` == `Order Item Product Price`.
- **Customer Privacy (PII):** Customer personal features (`Customer Fname`, `Customer Lname`, `Customer Street`, `Customer Zipcode`) are strictly masked and isolated from public tables.
- **Absence of Dates:** The 40-column dataset contains no timestamp/date columns (`order date (DateOrders)` / `shipping date (DateOrders)`). In accordance with fellowship guidelines, temporal trends are omitted with clear documentation.

---

## 4. Key Performance Indicator (KPI) Formulations

1. **Delivery Gap:**
   $$\text{Delivery Gap} = \text{Actual Shipping Days} - \text{Scheduled Shipping Days}$$
   - $\text{Gap} > 0$: **Delayed**
   - $\text{Gap} = 0$: **Exactly On Schedule**
   - $\text{Gap} < 0$: **Early (Advanced Shipping)**

2. **On-Time Delivery Rate (Combined):**
   $$\text{On-Time Rate} = \frac{\sum [\text{Delivery Gap} \le 0]}{N_{\text{total}}} \times 100\% = \mathbf{42.72\%}$$
   - *Exact On-Schedule Rate ($\text{Gap} = 0$):* **18.70%** (33,753 shipments)
   - *Early Delivery Rate ($\text{Gap} < 0$):* **24.02%** (43,366 shipments)

3. **Delay Rate:**
   $$\text{Delay Rate} = \frac{\sum [\text{Delivery Gap} > 0]}{N_{\text{total}}} \times 100\% = \mathbf{57.28\%} \quad (103,400 \text{ shipments})$$

4. **Average Delay Severity:**
   $$\text{Average Delay} = \frac{\sum_{\text{delayed}} \text{Delivery Gap}}{N_{\text{delayed}}} = \mathbf{1.62 \text{ days}}$$
   - *Denominator:* 103,400 delayed shipments.

5. **Average Signed Delivery Gap:**
   $$\text{Average Delivery Gap} = \frac{\sum \text{Delivery Gap}}{N_{\text{total}}} = \mathbf{+0.57 \text{ days}}$$

6. **Late-Delivery Risk Rate:**
   $$\text{Late-Delivery Risk Rate} = \frac{\sum [\text{Late\_delivery\_risk} = 1]}{N_{\text{total}}} \times 100\% = \mathbf{54.83\%} \quad (98,977 \text{ shipments})$$

7. **Regional Delay Index (RDI):**
   $$\text{RDI}_{\text{region}} = \frac{\text{Regional Delay Rate}}{\text{Baseline Overall Delay Rate (57.28\%)}}$$
   - $\text{RDI} > 1.0$: Region experiences higher delay frequency than average.
   - $\text{RDI} < 1.0$: Region achieves better delivery punctuality than average.

---

## 5. Core Empirical Findings

1. **The First Class SLA Fallacy (100% Delay Rate):**
   Scheduled shipping for all 27,814 First Class shipments is set to **1.0 day**, but actual fulfillment takes **2.0 days in 100% of cases**. The network physically does not support next-day delivery; the SLA promise is structurally flawed.
2. **Second Class Transit Inefficiency (79.73% Delay Rate):**
   Scheduled for **2.0 days**, but transit takes between 2 and 6 days (averaging 4.5 days), yielding an average delay of 2.50 days.
3. **Standard Class Buffer Effect (60.23% On-Time):**
   Carrying 59.7% of global volume, Standard Class provides a realistic 4-day buffer, achieving the highest on-time performance.
4. **The 4,423-Order Cancellation Discrepancy:**
   The difference between observed delays (57.28%) and `Late_delivery_risk` = 1 (54.83%) corresponds exactly to **`Shipping canceled`** orders, which were tagged with `Risk = 0` despite recorded transit days exceeding scheduled days.
5. **Geographic & Segment Parity:**
   Delay rates across all 5 global markets (LATAM, Europe, Pacific Asia, USCA, Africa) and all customer segments (Consumer, Corporate, Home Office) remain tightly bounded between 56.8% and 57.7%. Delays are mode-driven, not geography- or customer-driven.

---

## 6. Local Setup and Execution

### Prerequisites
- Python 3.10 – 3.12 installed.

### Setup Instructions
```bash
# 1. Navigate to the project directory
cd supply_chain_delivery_analysis

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate   # On Windows
# source venv/bin/activate # On macOS/Linux

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Run automated unit and pipeline tests
python -m unittest discover -s tests
python tests/test_stress_pipeline.py

# 5. Launch the Streamlit dashboard
streamlit run app.py
```

---

## 7. Streamlit Community Cloud Deployment
1. Push this repository to GitHub (ensure `data/*.csv` is ignored by `.gitignore` or use Git LFS / cloud bucket storage for large files).
2. Connect your GitHub repository to [share.streamlit.io](https://share.streamlit.io).
3. Set `app.py` as the main file path.
4. Set Python 3.12 as the runtime version.
5. Deploy and view live insights!

---

## 8. License & Fellowship Attribution
Developed as part of the **Unified Mentor Machine Learning Fellowship**. Designed for institutional evaluation and executive-ready supply chain decision intelligence.
