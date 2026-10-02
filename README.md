# Last-Mile E-Commerce Delivery Intelligence

A Power BI + SQL + Python analytics project analyzing last-mile delivery operations for an e-commerce marketplace — identifying where, when, and why deliveries breach SLA, with an AI-generated insights layer built on top of validated metrics.

> **Note on the dataset:** this project uses the public [Olist Brazilian E-Commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) as a proxy dataset. No public operational dataset exists for Indian e-commerce platforms, so Olist — the standard dataset for this type of analysis — was used to demonstrate how the same framework would apply to any last-mile delivery operation.

---

## Business Questions Answered

1. Which warehouses/sellers have the highest delivery delays?
2. Which origin-to-destination lanes perform poorly?
3. Which customer cities/states are delivery bottlenecks?
4. Is the delay mainly happening during warehouse handover or transit?
5. Are SLA breaches improving or worsening over time?
6. Which types of deliveries are most at risk?

---

## Tech Stack

- **Python (Pandas)** — data cleaning and feature engineering
- **MySQL** — cleaned data storage
- **SQL** — business analysis queries
- **Power BI + DAX** — dashboard and KPI measures
- **Groq API (LLM)** — automated executive insight generation

---

## Dashboard

**Page 1 — Executive Overview**
KPI cards (Total Orders, SLA Breach %, On-Time %, Avg Delivery Days), SLA breach trend over time, delivery outcome severity breakdown, and SLA breach % by customer/seller state, with a date-range slicer.

**Page 2 — Operations Deep Dive**
Worst-performing sellers, worst origin→destination lanes, worst bottleneck cities, warehouse-handling vs. transit delay breakdown, SLA breach by route type, and an AI-generated insights panel.

*(Add dashboard screenshots here, e.g. `![Page 1](powerbi/screenshots/page1.png)`)*

---

## Key Findings

- **8.1%** of ~96,000 orders breach SLA overall; **91.9%** on-time.
- **Transit time (9.3 days) is nearly 3x warehouse handling time (3.2 days)** — the delay bottleneck is predominantly in carrier/transit, not seller-side packing.
- **Cross-state deliveries breach SLA more than within-state ones** (~8.5% vs ~5.5%), confirming distance/logistics complexity drives risk.
- **Alagoas** is the highest-risk customer state (23.9% breach, 397 orders) — backed by a solid sample size, not noise.
- **Paraná → Alagoas** is the worst specific delivery lane (38.9% breach), and **São Paulo → Alagoas** is the highest-*volume* risky lane (26.3% breach across 255 orders).
- A sample-size validation step was applied throughout: any state, seller, or lane shown is backed by a minimum order threshold (20–30+ orders) to avoid small-sample distortion (e.g., one state initially showed a 66.7% breach rate — driven by just 3 total orders — and was excluded).

---

## AI Insights Layer

A lightweight GenAI pipeline automates executive summarization on top of validated metrics — it does not generate or alter any underlying numbers.

```
MySQL (validated metrics) → Python script → Groq LLM API → MySQL (ai_insights table) → Power BI (DAX measure → text box)
```

1. `generate_ai_insights.py` pulls validated aggregate metrics (SLA breach %, transit/warehouse days, worst states and lanes) directly from the MySQL database — the same logic underlying the Power BI DAX measures.
2. Brazilian state codes are converted to full state names using a **hardcoded Python lookup table** before being sent to the AI — not left to the model to translate.
3. The validated metrics are sent to the Groq API, which returns a concise 3-bullet executive summary + one recommended action.
4. The result is written to an `ai_insights` table in MySQL; Power BI reads the latest row via a DAX measure and displays it directly on the dashboard.

**Note:** this is a manual-run pipeline (rerun the script, then refresh in Power BI) rather than a live/scheduled one — the architecture supports wiring it to a scheduler (e.g. a cron job) for production use.

**A real failure case worth noting:** the first version of this pipeline let the AI translate Brazilian state codes itself, and it hallucinated — producing US state names (e.g. "Alabama" for the code "AL") and even an invented place name. Rather than just prompt-engineering around it, the translation step was moved into deterministic Python code, removing the AI's ability to make that decision at all.

---

## Project Structure

```
├── data/
│   ├── raw/              # Original Olist dataset files
│   └── clean/             # Cleaned, feature-engineered data
├── notebooks/
│   ├── m1_first_look.py
│   ├── m2_clean_features.py
│   └── m3_load_to_mysql.py
├── sql/
│   └── analysis_mysql.sql # Business analysis queries
├── ai/
│   ├── generate_ai_insights.py
│   └── check_models.py
├── powerbi/
│   └── Last_Mile_Operations_Dashboard.pbix
└── README.md
```

---

## How to Run

1. Clone the repo and place the Olist dataset CSVs in `data/raw/`.
2. Run the notebooks in order (`m1` → `m2` → `m3`) to clean the data and load it into MySQL.
3. Run the SQL queries in `sql/analysis_mysql.sql` to validate the analysis layer.
4. Open the `.pbix` file in Power BI Desktop and point it to your MySQL instance.
5. (Optional) To regenerate AI insights: set your MySQL and Groq API credentials in `ai/generate_ai_insights.py`, run it, then refresh the Power BI report.

---

## Author

**Gauri Bagad**
[LinkedIn](https://linkedin.com/in/gauri-bagad-893b0a234) · gauribagad1503@gmail.com
