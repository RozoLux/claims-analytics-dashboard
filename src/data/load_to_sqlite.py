import sqlite3, pandas as pd, os

DB_PATH = "db/claims.db"
RAW = "data/raw"

tables = [
    ("products",         ["product_code","product_name","product_family","underwriting_class","waiting_period_days"]),
    ("policies",         ["policy_id","product_code","cover_type","sum_assured","start_date","end_date","premium_freq","premium_amount","channel"]),
    ("members",          ["member_id","policy_id","gender","birth_date","region","smoker_flag","bmi","join_date"]),
    ("claims",           ["claim_id","member_id","policy_id","claim_date","notification_date","diagnosis_code","claim_type","status","initial_reserve","approved_amount","paid_amount","close_date"]),
    ("claim_payments",   ["payment_id","claim_id","payment_date","payment_amount"]),
    ("premiums_ledger",  ["policy_id","period_month","earned_premium"]),
    ("calendar",         ["dt","month","quarter","year"]),
]

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

for tbl, cols in tables:
    csv_path = os.path.join(RAW, f"{tbl}.csv")
    df = pd.read_csv(csv_path)
    # normalize dtypes a bit
    for c in df.columns:
        if "date" in c or c in ["dt","period_month","start_date","end_date","claim_date","close_date","notification_date","payment_date"]:
            # leave as text; SQLite will accept text dates
            df[c] = df[c].astype(str)
    df.to_sql(tbl, conn, if_exists="replace", index=False)
    print(f"Loaded {tbl}: {len(df)} rows")

conn.close()
print("✅ All tables loaded into db/claims.db")
