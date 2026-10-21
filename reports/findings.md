# Research & Findings Report: Delivery Performance, Delay Risk, and Logistics Efficiency in Global Supply Chain Operations

**Unified Mentor Machine Learning Fellowship**  
**Author:** Senior Data Analyst & Analytics Specialist  
**Dataset Analyzed:** `data/APL_Logistics.csv` (180,519 records, 40 fields, ~59.6 MB)  
**Status:** Validated, Verified & Deployment-Ready  

---

## 1. Executive Context & Business Problem
In modern global supply chain and multi-channel fulfillment operations, fulfilling delivery service-level agreements (SLAs) is paramount for customer retention, operational cost containment, and brand trust. Pervasive delivery delays lead to customer attrition, escalated customer support costs, and supply chain friction.

This study systematically investigates 180,519 global fulfillment transactions from `APL_Logistics.csv` to address:
1. True delivery performance versus scheduled shipping windows.
2. The severity, frequency, and statistical distribution of transit delays.
3. Fulfillment efficiency across different commercial shipping modes.
4. Geographic delivery performance across global markets and order regions.
5. The diagnostic relationship between recorded `Late_delivery_risk` and empirical delivery delays.
6. Evidence-based operational interventions to eliminate systemic delivery failure.

---

## 2. Dataset Architecture & Data Validation

### 2.1 File Characteristics
- **File Name:** `APL_Logistics.csv`
- **File Size:** 62,500,190 bytes (~59.60 MB)
- **Total Rows:** 180,519 transactions
- **Total Columns:** 40 features
- **Encoding:** Latin-1 / ISO-8859-1 (failed standard UTF-8 parsing on byte `0xe9`)

### 2.2 Data Quality & Cleaning Actions
- **Missing Values:**
  - `Customer Lname`: 8 missing values (0.004%). Imputed with `'Unknown'`.
  - `Customer Zipcode`: 3 missing values (0.002%). Imputed with `'0'`.
  - All other 38 columns have 100% data completeness with zero nulls.
- **Duplicate Records:** 0 exact duplicate rows across all 40 features.
- **Shipping Day Validation:**
  - `Days for shipping (real)` ranges from `0.0` to `6.0` days (mean: 3.50, median: 3.0, std: 1.62).
  - `Days for shipment (scheduled)` ranges from `0.0` to `4.0` days (mean: 2.93, median: 4.0, std: 1.37).
  - No negative or impossible shipping day values were detected.
- **Redundant Columns Identified:**
  - `Sales per customer` is 100% identical to `Order Item Total`.
  - `Benefit per order` is 100% identical to `Order Profit Per Order`.
  - `Product Price` is 100% identical to `Order Item Product Price`.
  - `Customer Id` and `Order Customer Id` are identical customer tracking identifiers.
- **Personally Identifiable Information (PII):**
  - Columns `Customer Fname`, `Customer Lname`, `Customer Street`, and `Customer Zipcode` contain personal customer identifiers. These fields are strictly masked and excluded from public-facing dashboard tables to preserve data privacy.
- **Absence of Date / Timestamp Columns:**
  - `APL_Logistics.csv` contains 40 columns and does not contain timestamp/date fields (`order date (DateOrders)` / `shipping date (DateOrders)`). Per project specification, time-series date filters and trend charts are omitted with clear documentation rather than inventing synthetic timestamps.

---

## 3. Metric Formulations & Grounded Definitions

1. **Delivery Gap:**
   $$\text{Delivery Gap} = \text{Days for shipping (real)} - \text{Days for shipment (scheduled)}$$
   - $\text{Gap} > 0$: **Delayed**
   - $\text{Gap} = 0$: **Exactly On Schedule**
   - $\text{Gap} < 0$: **Early (Advanced Shipping)**

2. **On-Time Delivery Rate (Combined):**
   $$\text{On-Time Rate} = \frac{\sum [\text{Delivery Gap} \le 0]}{N_{\text{total}}} \times 100\% = 42.72\%$$
   - Exactly On-Schedule Rate ($\text{Gap} = 0$): **18.70%** (33,753 shipments)
   - Early / Advance Delivery Rate ($\text{Gap} < 0$): **24.02%** (43,366 shipments)

3. **Delay Rate:**
   $$\text{Delay Rate} = \frac{\sum [\text{Delivery Gap} > 0]}{N_{\text{total}}} \times 100\% = 57.28\% \quad (103,400 \text{ shipments})$$

4. **Average Delay Severity:**
   $$\text{Average Delay} = \frac{\sum_{\text{delayed}} \text{Delivery Gap}}{N_{\text{delayed}}} = 1.62 \text{ days}$$
   - *Denominator:* 103,400 delayed shipments.

5. **Average Delivery Gap (Signed):**
   $$\text{Average Delivery Gap} = \frac{\sum \text{Delivery Gap}}{N_{\text{total}}} = +0.57 \text{ days}$$
   - *Denominator:* 180,519 total shipments.

6. **Late-Delivery Risk Rate:**
   $$\text{Late-Delivery Risk Rate} = \frac{\sum [\text{Late\_delivery\_risk} = 1]}{N_{\text{total}}} \times 100\% = 54.83\% \quad (98,977 \text{ shipments})$$

7. **Regional Delay Index (RDI):**
   $$\text{RDI}_{\text{region}} = \frac{\text{Delay Rate}_{\text{region}}}{\text{Baseline Delay Rate} \ (57.28\%)}$$

---

## 4. Key Empirical Findings

### 4.1 Root Cause Discovery: The Shipping Mode SLA Paradox
Delivery performance is overwhelmingly determined by the commercial shipping mode and unrealistic scheduling promises rather than carrier failure or geographic distance:

| Shipping Mode | Volume | Volume Share | Scheduled SLA | Actual Transit | On-Time Rate | Delay Rate | Avg Delay | Late Risk Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Standard Class** | 107,752 | 59.69% | 4.0 days | 2 – 6 days | **60.23%** | 39.77% | 1.51 days | 38.07% |
| **Second Class** | 35,216 | 19.51% | 2.0 days | 2 – 6 days | **20.27%** | 79.73% | 2.50 days | 76.63% |
| **First Class** | 27,814 | 15.41% | 1.0 day | **2.0 days** | **0.00%** | **100.00%** | 1.00 day | 95.32% |
| **Same Day** | 9,737 | 5.39% | 0.0 days | 0 – 1 days | **52.17%** | 47.83% | 1.00 day | 45.74% |

#### Key Insights:
1. **First Class has a 100% Delay Rate:** In all 27,814 First Class shipments, the scheduled shipping day is fixed at 1 day, while actual transit time is universally 2 days. The fulfillment network physically cannot deliver in 1 day; the SLA promise is structurally flawed.
2. **Second Class Fails 80% of the Time:** Second Class promises 2-day delivery, yet actual transit takes between 2 and 6 days (averaging over 4 days), resulting in an average delay of 2.50 days.
3. **Standard Class Is the Only Stable Buffer:** By providing a 4-day scheduled window, Standard Class achieves the highest on-time rate (60.23%), with 24.0% arriving ahead of schedule.

### 4.2 Decoupling `Late_delivery_risk` from Observed Delay
A critical finding is that `Late_delivery_risk` (54.83%) does not equal empirical delivery delay (57.28%):
- **Observed Delays ($\text{Gap} > 0$):** 103,400 orders.
- **Marked as Late Delivery Risk ($= 1$):** 98,977 orders.
- **Discrepancy (4,423 orders):** Exactly corresponds to **`Shipping canceled`** orders!
  - In the logistics system, when an order was canceled, real transit days were still logged (exceeding scheduled days by 1 to 4 days), but because the shipment was canceled, `Delivery Status` was marked as `'Shipping canceled'` and `Late_delivery_risk` was assigned `0`.
  - For fulfilled shipments, `Late_delivery_risk` has **100% precision** against `'Late delivery'`.

### 4.3 Market and Geographic Parity
Contrary to assumptions that international markets suffer disproportionate delays:
- **LATAM:** 51,594 orders | Delay Rate: 57.02% | RDI: 0.996
- **Europe:** 50,252 orders | Delay Rate: 57.69% | RDI: 1.007
- **Pacific Asia:** 41,260 orders | Delay Rate: 57.32% | RDI: 1.001
- **USCA:** 25,799 orders | Delay Rate: 57.15% | RDI: 0.998
- **Africa:** 11,614 orders | Delay Rate: 56.81% | RDI: 0.992

All global markets operate within $\pm 0.7\%$ of the baseline 57.28% delay rate. Even across 23 sub-regions, the RDI ranges tightly from 0.907 (Canada) to 1.060 (Central Africa).

### 4.4 Customer Segment Uniformity
- **Consumer:** 93,504 orders (51.8%) | Delay Rate: 57.29% | Avg Delay: 1.61 days
- **Corporate:** 54,789 orders (30.4%) | Delay Rate: 57.11% | Avg Delay: 1.62 days
- **Home Office:** 32,226 orders (17.8%) | Delay Rate: 57.52% | Avg Delay: 1.62 days

Delays do not discriminate by customer segment. Operational routing treats all segment orders identically.

### 4.5 Financial & Operational Independence
Correlation analysis between Delivery Gap and numeric variables:
- `Order Item Total / Sales`: $r = -0.0040$
- `Order Item Discount Rate`: $r = +0.0015$
- `Order Item Quantity`: $r = +0.0018$
- `Order Profit Per Order`: $r = -0.0054$

**Conclusion:** Higher order values, item quantities, discounts, and profitability metrics do not correlate with faster delivery. Expedited logistics is not granted to higher-tier commercial transactions.

---

## 5. Actionable Strategic Recommendations

1. **Immediate SLA Recalibration for First Class:**
   - Modify the published First Class SLA commitment from 1 day to 2 days. This single operational policy adjustment will instantly shift 27,814 orders from "delayed" to "on schedule," improving the global on-time rate by 15.4 percentage points.
2. **Revise Second Class Promised Windows:**
   - Extend Second Class scheduled delivery windows from 2 days to 3 or 4 days, or restrict Second Class carrier selection to express partners capable of true 48-hour dispatch.
3. **Harmonize Cancellation Tracking:**
   - Update data ingestion pipelines to segregate canceled orders before calculating delivery gap KPIs, preventing aborted dispatches from contaminating logistics fulfillment metrics.
4. **Volume Prioritization Routing:**
   - Establish expedited fulfillment queues for high-margin and high-volume corporate accounts, addressing the current lack of relationship between commercial value and delivery speed.

---

## 6. Methodological Limitations
- **Omission of Timestamps:** The dataset contains no calendar dates, preventing longitudinal trend analysis, seasonal demand spike tracking, and day-of-week dispatch evaluation.
- **Granular Carrier Metrics:** Specific logistics carriers (e.g., DHL, FedEx, national postal services) are not broken down; only commercial shipping mode classes are logged.
