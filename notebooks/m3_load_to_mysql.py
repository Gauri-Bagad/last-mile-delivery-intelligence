# notebooks/m3_load_to_mysql.py
import pandas as pd
from sqlalchemy import create_engine

# 1. Read the clean table we saved in Milestone 2
df = pd.read_csv("data/clean/deliveries_clean.csv")

# 2. Your MySQL connection details (change USER + PASSWORD to yours)
USER, PASSWORD = "root", "root"
HOST, PORT, DB = "localhost", 3306, "delivery_db"

engine = create_engine(f"mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB}")

# 3. Write the DataFrame into MySQL as table 'deliveries'
df.to_sql("deliveries", engine, if_exists="replace", index=False,
          chunksize=1000, method="multi")   # chunks = faster for ~96k rows

# 4. Quick test that it landed
print(pd.read_sql("SELECT COUNT(*) AS total_rows FROM deliveries", engine))
print("Loaded into MySQL -> schema 'delivery_db', table 'deliveries'")