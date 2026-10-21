# Fellowship Evaluation: Presentation Slide Deck & Viva Defense Guide

**Project Title:** Delivery Performance, Delay Risk, and Logistics Efficiency Analysis in Global Supply Chain Operations  
**Fellowship:** Unified Mentor Machine Learning Fellowship  
**Dataset:** 180,519 Global Transactions (`APL_Logistics.csv`, ~59.6 MB)  

---

## Part 1: Recommended 10-Slide Presentation Structure

### Slide 1: Title & Fellowship Overview
- **Title:** Delivery Performance, Delay Risk, and Logistics Efficiency in Global Supply Chains
- **Subtitle:** An Empirical Diagnostic of 180,519 Global Orders
- **Presenter:** Senior Data Science & Supply Chain Fellow
- **Fellowship:** Unified Mentor Machine Learning Fellowship

### Slide 2: Business Problem & Operational Impact
- **The Challenge:** High customer-reported delivery delays, SLA penalties, and customer churn.
- **The Core Question:** Are delays caused by carrier transit bottlenecks, international distances, or internal scheduling promises?
- **Scope:** 180,519 fulfillment records spanning 5 global markets, 23 regions, and 4 commercial shipping modes.

### Slide 3: Dataset Architecture & Hygiene
- **Data Size:** 180,519 rows × 40 columns (~59.6 MB).
- **Encoding:** Latin-1 (`iso-8859-1`) due to multi-lingual regional characters.
- **Data Hygiene:** 0 duplicate rows; 100% completeness on 38 of 40 columns (only 8 nulls in customer last name, 3 in zipcode).
- **Ethics & Privacy:** Customer PII (name, address, zipcode) masked and excluded from dashboards.
- **Integrity Notice:** No timestamp columns exist in the 40-feature dataset; avoided synthetic date fabrication.

### Slide 4: Metric Formulations & KPI Definitions
- **Delivery Gap:** $\text{Actual Shipping Days} - \text{Scheduled Shipping Days}$
  - $\text{Gap} < 0$: Early (24.02%)
  - $\text{Gap} == 0$: Exactly On Schedule (18.70%)
  - $\text{Gap} > 0$: Delayed (57.28%)
- **On-Time Delivery Rate:** $42.72\%$ ($\text{Gap} \le 0$)
- **Delay Rate:** $57.28\%$ (103,400 delayed shipments)
- **Average Delay Severity:** $+1.62 \text{ days}$ (among delayed shipments)
- **Late-Delivery Risk Rate:** $54.83\%$ (98,977 shipments)

### Slide 5: The Major Discovery — The First Class SLA Paradox
- **The Finding:** First Class shipping has a **100.0% delay rate** across all 27,814 shipments!
- **Root Cause:** Scheduled shipping time was fixed at **1.0 day**, but actual transit time took **2.0 days in 100% of shipments**.
- **Takeaway:** Carrier operations are remarkably consistent (always 2 days), but the published marketing promise (1 day) is structurally flawed.
- **Second Class:** Promised 2 days, but actually requires 2 to 6 days (avg 4.5 days) $\rightarrow$ 79.73% delay rate.
- **Standard Class:** Realistic 4-day scheduled buffer $\rightarrow$ 60.23% on-time rate.

### Slide 6: Decoupling Risk Flag from Observed Delays
- **The Paradox:** Why is `Late_delivery_risk = 1` tagged on 54.83% of orders while actual delays are 57.28%?
- **The Solution:** The difference (4,423 orders) corresponds 100% to **`Shipping canceled`** orders.
- **Data Pipeline Finding:** In canceled dispatches, real days exceeded scheduled days, but risk was coded as 0 because the order was aborted. For completed dispatches, `Late_delivery_risk` had **100% precision**.

### Slide 7: Geographic & Demographic Neutrality
- **Market Delay Parity:** LATAM (57.02%), Europe (57.69%), Pacific Asia (57.32%), USCA (57.15%), Africa (56.81%).
- **Regional Delay Index (RDI):** All regions cluster tightly around 1.00 (range 0.907 to 1.060).
- **Customer Segments:** Consumer (57.29%), Corporate (57.11%), Home Office (57.52%) differ by $< 0.4\%$.
- **Financial Correlation:** Correlation between delivery delay and order value, item discount, or profit margin is essentially zero ($|r| < 0.005$).

### Slide 8: Interactive Streamlit Dashboard Architecture
- **Tech Stack:** Python, Streamlit, Pandas, NumPy, Plotly.
- **6 Integrated Modules:** Performance Overview, Risk Diagnostic, Mode SLAs, Regional Analysis, Segment Breakdown, Quality & Strategy.
- **Dynamic Interactivity:** Multi-tier cascading filters, instant caching (`@st.cache_data`), responsive layout, and zero-record handling.

### Slide 9: Strategic C-Suite Recommendations
1. **Recalibrate First Class SLA to 2 Days:** Instantly converts 27,814 orders from "late" to "on-time", improving global on-time performance by **+15.4 percentage points**.
2. **Re-contract Second Class Logistics:** Extend promise windows to 3–4 days or partner with guaranteed 48-hour 3PL carriers.
3. **Data Pipeline Cleansing:** Segregate canceled shipments prior to calculating logistics fulfillment metrics.

### Slide 10: Technical Verification & Limitations
- **Verification:** 5/5 automated unit tests passed; full 180k-row stress test completed with zero errors.
- **Limitations:** Lack of calendar dates precludes seasonal trend analysis; lack of carrier IDs prevents carrier-level benchmarking.
- **Conclusion:** Fulfillment operations are physically stable; aligning customer promises with empirical reality restores customer trust.

---

## Part 2: Viva / Evaluator Q&A Defense Guide

### Q1: "How did you calculate Delivery Gap and define On-Time vs Delayed?"
> **Answer:** "Delivery Gap is calculated as `Actual Shipping Days - Scheduled Shipping Days`. A gap strictly greater than zero indicates a delay ($\text{Gap} > 0$). A gap less than or equal to zero indicates on-time delivery ($\text{Gap} \le 0$). Importantly, we separated on-time deliveries into two distinct groups: **Exact On-Schedule** ($\text{Gap} = 0$, representing 18.70%) and **Early / Advance Shipping** ($\text{Gap} < 0$, representing 24.02%), totaling a 42.72% on-time fulfillment rate."

### Q2: "What is the denominator for Average Delay?"
> **Answer:** "The denominator for Average Delay is strictly the count of **delayed deliveries** (103,400 orders where $\text{Gap} > 0$), resulting in an average delay of **1.62 days**. For average signed gap across the entire dataset (including early and on-time shipments), the denominator is all 180,519 valid shipments, yielding **+0.57 days**."

### Q3: "Why did First Class shipping show a 100% delay rate? Is the carrier failing?"
> **Answer:** "No, the carrier is not failing. Across all 27,814 First Class shipments in the dataset, actual delivery consistently took **2.0 days** with zero variance. However, the internal scheduling system promised delivery in **1.0 day**. The 100% delay rate is caused by an unrealistic marketing/scheduling promise rather than physical carrier disruption."

### Q4: "Why does Late_delivery_risk (54.83%) differ from the observed delay rate (57.28%)?"
> **Answer:** "The difference of 4,423 records corresponds entirely to orders with `Delivery Status = 'Shipping canceled'`. In those instances, logged transit days exceeded scheduled days, but because the shipment was canceled rather than fulfilled, `Late_delivery_risk` was coded as 0. For all completed dispatches, `Late_delivery_risk` matched `Late delivery` with 100% precision."

### Q5: "What is the Regional Delay Index (RDI) and how is it interpreted?"
> **Answer:** "RDI is a transparent ratio: $\text{Regional Delay Rate} / \text{Baseline Overall Delay Rate (57.28\%)}$. An RDI of 1.00 indicates performance exactly matching the company average. Values above 1.00 denote higher-than-average delays (e.g., Central Africa at 1.060), while values below 1.00 denote higher punctuality (e.g., Canada at 0.907). Across all 23 global regions, RDI remained between 0.907 and 1.060, proving that delays are not primarily caused by geography."

### Q6: "Why did you not show a time-series trend chart over months or years?"
> **Answer:** "The dataset provided (`APL_Logistics.csv`) contains 40 columns and does not include calendar dates or timestamps (`order date` or `shipping date`). Per fellowship guidelines and scientific integrity, we explicitly documented this data limitation rather than fabricating synthetic dates or substituting unrelated fields."
