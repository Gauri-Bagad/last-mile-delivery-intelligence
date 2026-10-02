# notebooks/m2_clean_features.py
import pandas as pd
import numpy as np

RAW, CLEAN = "data/raw/brazildataset/", "data/clean/"

# ---- 1. Rebuild the order-level table (same join as Milestone 1) ----
orders    = pd.read_csv(RAW + "olist_orders_dataset.csv")
items     = pd.read_csv(RAW + "olist_order_items_dataset.csv")
customers = pd.read_csv(RAW + "olist_customers_dataset.csv")
sellers   = pd.read_csv(RAW + "olist_sellers_dataset.csv")

date_cols = ["order_purchase_timestamp", "order_delivered_carrier_date",
             "order_delivered_customer_date", "order_estimated_delivery_date"]
for c in date_cols:
    orders[c] = pd.to_datetime(orders[c], errors="coerce")

items_agg = (items.groupby("order_id")
                  .agg(seller_id=("seller_id", "first"),
                       n_items=("order_item_id", "count"),
                       freight_value=("freight_value", "sum"))
                  .reset_index())

df = (orders
      .merge(customers[["customer_id", "customer_city", "customer_state"]], on="customer_id", how="left")
      .merge(items_agg, on="order_id", how="left")
      .merge(sellers[["seller_id", "seller_city", "seller_state"]], on="seller_id", how="left"))

# ---- 2. Keep only orders where a delivery actually happened ----
before = len(df)
df = df[df["order_status"] == "delivered"].copy()
df = df.dropna(subset=date_cols)
print(f"Kept {len(df)} of {before} rows after focusing on completed deliveries")

# ---- 3. Engineer the delay metrics (all in DAYS) ----
day = np.timedelta64(1, "D")
df["warehouse_handover_days"] = (df["order_delivered_carrier_date"]  - df["order_purchase_timestamp"])  / day
df["transit_days"]            = (df["order_delivered_customer_date"] - df["order_delivered_carrier_date"]) / day
df["actual_delivery_days"]    = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"])  / day
df["promised_days"]           = (df["order_estimated_delivery_date"] - df["order_purchase_timestamp"])  / day
df["delay_vs_sla_days"]       = (df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]) / day

# ---- 4. Business flags ----
df["is_late"] = (df["delay_vs_sla_days"] > 0).astype(int)          # 1 = SLA breach

def bucket(d):
    if d <= 0: return "On-Time"
    if d <= 3: return "Slightly Late (1-3d)"
    if d <= 7: return "Late (4-7d)"
    return "Severely Late (>7d)"
df["sla_bucket"] = df["delay_vs_sla_days"].apply(bucket)

df["is_cross_state"] = (df["seller_state"] != df["customer_state"]).astype(int)
df["route_type"]     = np.where(df["is_cross_state"] == 1, "Cross-State", "Within-State")
df["order_month"]    = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
df["order_date"]     = df["order_purchase_timestamp"].dt.date

# ---- 5. Remove impossible records (data errors, NOT real delays) ----
q = len(df)
df = df[(df["warehouse_handover_days"] >= 0) &
        (df["transit_days"] >= 0) &
        (df["actual_delivery_days"] >= 0)]
print(f"Removed {q - len(df)} rows with impossible negative durations")

# ---- 6. Save the analytics-ready table ----
keep = ["order_id", "order_month", "order_date",
        "seller_id", "seller_city", "seller_state",
        "customer_city", "customer_state", "route_type", "is_cross_state",
        "n_items", "freight_value",
        "warehouse_handover_days", "transit_days", "actual_delivery_days",
        "promised_days", "delay_vs_sla_days", "is_late", "sla_bucket"]
df[keep].to_csv(CLEAN + "deliveries_clean.csv", index=False)

# ---- 7. Quick health check ----
print("\nOn-time rate: {:.1%}".format(1 - df["is_late"].mean()))
print("Avg warehouse handover: {:.1f} days".format(df["warehouse_handover_days"].mean()))
print("Avg transit: {:.1f} days".format(df["transit_days"].mean()))
print("\nSLA buckets:\n", df["sla_bucket"].value_counts())
print(f"\nSaved -> data/clean/deliveries_clean.csv ({len(df)} rows)")