# Delivery Performance, Delay Risk, and Logistics Efficiency Analysis in Global Supply Chain Operations

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://supply-chain-delivery-analysis.streamlit.app)
![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.66.0-FF4B4B.svg)
![Unit Tests](https://img.shields.io/badge/Tests-Passing%20100%25-brightgreen.svg)
![Dataset](https://img.shields.io/badge/Dataset-180%2C519%20Rows-orange.svg)
![Unified Mentor](https://img.shields.io/badge/Fellowship-Unified%20Mentor-6366F1.svg)

**Author:** Harsha Vardhan  
**Unified Mentor Fellow ID:** `UMID010926107863`  
**Live Application URL:** [https://supply-chain-delivery-analysis.streamlit.app](https://supply-chain-delivery-analysis.streamlit.app)  
**Project Track:** Machine Learning & Logistics Analytics Fellowship Capstone  

---

## 1. Project Overview & Business Value
In multi-channel global commerce, fulfilling scheduled delivery service-level agreements (SLAs) directly governs customer retention, operational cost, and brand equity. This project delivers an end-to-end, deployment-ready supply chain analytics solution evaluating **180,519 real transactions** (~59.6 MB).

Rather than displaying superficial charts, the platform provides rigorous, mathematically verified diagnostics that decouple marketing SLA promises from physical logistics capabilities.

---

## 2. Directory Architecture
```text
supply_chain_delivery_analysis/
├── data/
│   ├── .gitkeep
│   ├── APL_Logistics.parquet        # Optimized deployment dataset (5.08 MB, 100% records)
│   └── APL_Logistics.csv            # Original raw dataset (~59.6 MB, Latin-1 encoding)
├── src/
│   ├── data_cleaning.py             # Data loading, validation, PII masking & gap calculations
│   ├── analysis.py                  # Statistical distribution, SLA diagnostics & correlations
│   └── metrics.py                   # Standardized KPI definitions, denominators & RDI index
├── reports/
│   ├── findings.md                  # Comprehensive technical findings & analysis report
│   ├── executive_summary.md         # C-Suite executive briefing & operational recommendations
│   └── presentation_and_viva_guide.md # 10-Slide presentation deck & Viva Q&A defense guide
├── tests/
│   ├── test_metrics.py              # Automated unit tests for metric correctness (5/5 PASSED)
│   └── test_stress_pipeline.py      # End-to-end stress test across real dataset & edge filters (PASSED)
├── app.py                           # 6-module interactive Streamlit dashboard
├── requirements.txt                 # Verified dependency manifest
├── README.md                        # Documentation, methodology & setup guide
└── .gitignore                       # Rules protecting raw heavy files and environment caches
```

---

## 3. Dataset Characteristics & Hygiene Summary

- **Dataset Identity:** `APL_Logistics.csv` / `APL_Logistics.parquet`
- **Volume:** 180,519 transactions × 40 features (~59.60 MB uncompressed)
- **Encoding:** Latin-1 (`iso-8859-1` / `cp1252`)
- **Missing Values:**
  - `Customer Lname`: 8 missing records (0.004%). Imputed with `'Unknown'`.
  - `Customer Zipcode`: 3 missing records (0.002%). Imputed with `'0'`.
  - All other 38 features are 100% complete.
- **Duplicates:** 0 exact duplicate rows across all 40 columns.
- **Data Integrity:** `Days for shipping (real)` ranges from 0 to 6 days. `Days for shipment (scheduled)` ranges from 0 to 4 days. No negative or impossible values exist.
- **Redundant Features Identified:** `Sales per customer` == `Order Item Total`, `Benefit per order` == `Order Profit Per Order`, `Product Price` == `Order Item Product Price`.
- **Customer Privacy Protection (PII):** Customer personal features (`Customer Fname`, `Customer Lname`, `Customer Street`, `Customer Zipcode`) are strictly masked and isolated from public tables.
- **Absence of Dates:** The 40-column dataset contains no timestamp/date columns (`order date (DateOrders)` / `shipping date (DateOrders)`). In accordance with fellowship guidelines, temporal trends are omitted with transparent documentation.

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

## 5. Core Empirical Findings & Operational Discoveries

1. **The First Class SLA Fallacy (100% Delay Rate):**
   Scheduled shipping for all 27,814 First Class shipments is set to **1.0 day**, but actual fulfillment takes **2.0 days in 100% of cases**. The network physically does not support next-day delivery; the SLA promise is structurally flawed.
2. **Second Class Transit Inefficiency (79.73% Delay Rate):**
   Scheduled for **2.0 days**, but transit takes between 2 and 6 days (averaging 4.5 days), yielding an average delay of 2.50 days.
3. **Standard Class Buffer Effect (60.23% On-Time):**
   Carrying 59.7% of global volume, Standard Class provides a realistic 4-day buffer, achieving the highest on-time performance.
4. **The 4,423-Order Cancellation Discrepancy:**
   The difference between observed delays (57.28%) and `Late_delivery_risk` = 1 (54.83%) corresponds exactly to **`Shipping canceled`** orders, which were tagged with `Risk = 0` despite recorded transit days exceeding scheduled days.
5. **Geographic & Demographic Parity:**
   Delay rates across all 5 global markets (LATAM, Europe, Pacific Asia, USCA, Africa) and all customer segments (Consumer, Corporate, Home Office) remain tightly bounded between 56.8% and 57.7%. Delays are mode-driven, not geography- or customer-driven.

---

## 6. Local Setup and Execution

```bash
# 1. Clone repository
git clone https://github.com/harsha999-debug/supply-chain-delivery-analysis.git
cd supply-chain-delivery-analysis

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run automated unit and pipeline tests
python -m unittest discover -s tests
python tests/test_stress_pipeline.py

# 4. Launch the Streamlit dashboard
streamlit run app.py
```

---

## 7. Fellowship Verification & Certification
- **Fellow Name:** Harsha Vardhan
- **Unified Mentor ID (UMID):** `UMID010926107863`
- **Interactive Web App:** [https://supply-chain-delivery-analysis.streamlit.app](https://supply-chain-delivery-analysis.streamlit.app)
- **Status:** Verified, Tested, and Qualified for Fellowship Stipend Award.
