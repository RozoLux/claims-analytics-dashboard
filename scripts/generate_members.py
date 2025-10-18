import pandas as pd
import random

# Load policy_ids
policies_df = pd.read_csv("data/raw/policies.csv")
valid_policy_ids = policies_df["policy_id"].tolist()

# Generate synthetic members
random.seed(42)
members_data = {
    "member_id": list(range(1, 5001)),
    "policy_id": random.choices(valid_policy_ids, k=5000),
    "gender": random.choices(["M", "F"], k=5000),
    "birth_date": pd.to_datetime(pd.Series(pd.date_range("1940-01-01", "2005-12-31", periods=5000))).dt.strftime("%Y-%m-%d"),
    "region": random.choices(["North", "South", "East", "West"], k=5000),
    "smoker_flag": random.choices([True, False], k=5000),
    "bmi": [round(random.uniform(18.0, 40.0), 1) for _ in range(5000)],
    "join_date": pd.to_datetime(pd.Series(pd.date_range("2019-01-01", "2025-12-31", periods=5000))).dt.strftime("%Y-%m-%d"),
}

members_df = pd.DataFrame(members_data)
members_df.to_csv("data/raw/members.csv", index=False)

print("✅ members.csv regenerated with valid policy_id references!")
