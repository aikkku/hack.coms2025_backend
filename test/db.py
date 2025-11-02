import pandas as pd
import sqlite3

# 1. Load CSV
df = pd.read_csv("results.csv")

# 2. Keep only the columns that match your DB table
df = df[["course_code", "title", "instructors"]]   # ← adjust to your actual DB columns

# 3. Connect to existing database
conn = sqlite3.connect("courses.db")

# 4. Append (don’t replace!) to the existing table
df.to_sql("courses", conn, if_exists="append", index=False)

conn.close()
print("✅ CSV data copied to existing database.")
