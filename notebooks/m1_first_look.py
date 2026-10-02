# notebooks/m1_first_look.py
import pandas as pd

RAW = "data/raw/brazildataset/"

# 1. Load the core tables
orders    = pd.read_csv(RAW + "olist_orders_dataset.csv")
items     = pd.read_csv(RAW + "olist_order_items_dataset.csv")
customers = pd.read_csv(RAW + "olist_customers_dataset.csv")
sellers   = pd.read_csv(RAW + "olist_sellers_dataset.csv")

# 2. Convert the date columns from text -> real datetimes (critical for delay math later)
date_cols = [
    "order_purchase_timestamp",
    "order_delivered_carrier_date",
    "order_delivered_customer_date",
    "order_estimated_delivery_date",
]
for c in date_cols:
    orders[c] = pd.to_datetime(orders[c], errors="coerce")

# 3. Reduce order_items to ONE row per order (an order can have many items)
#    We keep the seller and total freight so we can analyze the warehouse (seller) side.
items_agg = (
    items.groupby("order_id")
         .agg(seller_id=("seller_id", "first"),   # main warehouse for the order
              n_items=("order_item_id", "count"),
              freight_value=("freight_value", "sum"))
         .reset_index()
)

# 4. Build ONE order-level table by joining the pieces together
df = (orders
      .merge(customers[["customer_id", "customer_city", "customer_state"]], on="customer_id", how="left")
      .merge(items_agg, on="order_id", how="left")
      .merge(sellers[["seller_id", "seller_city", "seller_state"]], on="seller_id", how="left"))

# 5. Profile it — the "first look" every analyst does
print("Rows, Columns:", df.shape)
print("\nOrder status counts:\n", df["order_status"].value_counts())
print("\nDate range:", df["order_purchase_timestamp"].min(), "->", df["order_purchase_timestamp"].max())
print("\nMissing values per column:\n", df.isna().sum())
print("\nSample:\n", df.head())

# 6. Export a small sample to Excel for a manual pivot-table sanity check
df.head(2000).to_excel("data/raw/sample_for_excel.xlsx", index=False)
print("\nSaved sample_for_excel.xlsx — open it and try a quick pivot.")