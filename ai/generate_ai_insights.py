"""
Last-Mile Delivery Intelligence — AI Insights Generator
---------------------------------------------------------
What this does:
1. Connects to your MySQL database
2. Pulls validated aggregate metrics (same logic as your Power BI DAX measures)
3. Sends those real numbers to Groq (an LLM API) with a prompt asking for insights
4. Writes the AI's response back into a new table: ai_insights
5. Power BI reads that table directly and displays whatever the latest run produced

Run this manually whenever you want fresh insights (e.g. after updating your data).
"""

import mysql.connector
from groq import Groq
from datetime import datetime

# ============== EDIT THIS SECTION ==============
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "your_mysql_password"      # <-- put your real MySQL password
DB_NAME = "delivery_db"           # <-- put your real database name
TABLE_NAME = "deliveries"          # <-- change if your table name is different
GROQ_API_KEY = "gsk_your_key_here"       # <-- paste your Groq API key here
# =================================================

# If any query below errors with "Unknown column", run this first in MySQL Workbench
# to see your real column names, then adjust the queries accordingly:
#   SELECT * FROM deliveries_clean LIMIT 5;

client = Groq(api_key=GROQ_API_KEY)

# ---------- Fixed lookup: abbreviation -> full Brazilian state name ----------
# This is a hardcoded dictionary, not AI-generated, so there is zero risk of
# a wrong/invented name ever appearing in the output.
BR_STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapa", "AM": "Amazonas", "BA": "Bahia",
    "CE": "Ceara", "DF": "Distrito Federal", "ES": "Espirito Santo", "GO": "Goias",
    "MA": "Maranhao", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais",
    "PA": "Para", "PB": "Paraiba", "PR": "Parana", "PE": "Pernambuco", "PI": "Piaui",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul",
    "RO": "Rondonia", "RR": "Roraima", "SC": "Santa Catarina", "SP": "Sao Paulo",
    "SE": "Sergipe", "TO": "Tocantins",
}


def full_name(code):
    """Return the full state name, or the code itself if not found (never guesses)."""
    return BR_STATE_NAMES.get(code, code)


conn = mysql.connector.connect(
    host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
)
cursor = conn.cursor(dictionary=True)

# ---------- 1. Pull validated overall metrics ----------
cursor.execute(f"""
    SELECT
        COUNT(*) AS total_orders,
        SUM(is_late) AS late_orders,
        ROUND(SUM(is_late) / COUNT(*) * 100, 1) AS sla_breach_pct,
        ROUND(AVG(transit_days), 1) AS avg_transit_days,
        ROUND(AVG(warehouse_handover_days), 1) AS avg_warehouse_days
    FROM {TABLE_NAME}
""")
overall = cursor.fetchone()

# ---------- 2. Worst customer states (sample-size safe, min 30 orders) ----------
cursor.execute(f"""
    SELECT customer_state,
           ROUND(SUM(is_late) / COUNT(*) * 100, 1) AS breach_pct,
           COUNT(*) AS n
    FROM {TABLE_NAME}
    GROUP BY customer_state
    HAVING n >= 30
    ORDER BY breach_pct DESC
    LIMIT 3
""")
worst_states = cursor.fetchall()

# ---------- 3. Worst origin-destination lanes (min 20 orders) ----------
cursor.execute(f"""
    SELECT seller_state, customer_state,
           ROUND(SUM(is_late) / COUNT(*) * 100, 1) AS breach_pct,
           COUNT(*) AS n
    FROM {TABLE_NAME}
    GROUP BY seller_state, customer_state
    HAVING n >= 20
    ORDER BY breach_pct DESC
    LIMIT 3
""")
worst_lanes = cursor.fetchall()

# ---------- Convert state codes to full names BEFORE sending to the AI ----------
# Doing this in Python (not asking the AI to translate) guarantees accuracy.
for row in worst_states:
    row["customer_state"] = full_name(row["customer_state"])

for row in worst_lanes:
    row["seller_state"] = full_name(row["seller_state"])
    row["customer_state"] = full_name(row["customer_state"])

# ---------- 4. Build the prompt (AI only sees numbers you've already validated) ----------
prompt = f"""
You are an operations analyst writing a short executive summary for a last-mile
e-commerce delivery dashboard for a company operating in Brazil. State names given
below are already full, correct Brazilian state names (e.g. "Alagoas", "Sao Paulo") -
use them exactly as given, do not abbreviate them, and do not substitute any other
country's place names.

Using ONLY the validated metrics below, write:
- Exactly 3 short, concrete bullet-point insights (one sentence each, no sub-bullets)
- 1 short recommended action (maximum 2 sentences)

Keep the ENTIRE response under 120 words total. Do not invent any numbers that are
not given to you below. Use plain business language, suitable for a non-technical reader.

OVERALL METRICS:
- Total Orders: {overall['total_orders']}
- SLA Breach %: {overall['sla_breach_pct']}%
- Avg Transit Days: {overall['avg_transit_days']}
- Avg Warehouse Handling Days: {overall['avg_warehouse_days']}

WORST CUSTOMER STATES (minimum 30 orders, so these are reliable, not small-sample noise):
{worst_states}

WORST ORIGIN-TO-DESTINATION LANES (minimum 20 orders):
{worst_lanes}
"""

# ---------- 5. Call Groq ----------
response = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": prompt}],
)
insight_text = response.choices[0].message.content

# ---------- 6. Write the result back into MySQL ----------
cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_insights (
        id INT AUTO_INCREMENT PRIMARY KEY,
        generated_at DATETIME,
        insight_text TEXT
    )
""")
cursor.execute(
    "INSERT INTO ai_insights (generated_at, insight_text) VALUES (%s, %s)",
    (datetime.now(), insight_text),
)
conn.commit()

print("Done! Insight generated and saved to the ai_insights table:\n")
print(insight_text)

cursor.close()
conn.close()
