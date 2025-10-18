import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

# ---------- CONFIG (tweak if needed) ----------
START_DATE = date(2020, 1, 1)
END_DATE   = date(2025, 9, 30)

N_PRODUCTS = 12
N_MEMBERS  = 5000   # keep modest for older Mac
N_POLICIES = 4000   # <= members; some members share a policy in real life, but we keep 1-1/1-many simple
MAX_CLAIMS_PER_MEMBER = 4

# Base frequencies (per member per year); adjusted by risk factors later
BASE_LAMBDA_HEALTH = 0.35
BASE_QX_LIFE = {  # annual death prob by age band (very rough toy numbers)
    (18, 29): 0.0003,
    (30, 39): 0.0006,
    (40, 49): 0.0015,
    (50, 59): 0.0035,
    (60, 69): 0.0080,
    (70, 85): 0.0180,
}

# Severity (paid) lognormal params (meanlog, sdlog) per claim_type
SEVERITY_PARAMS = {
    "outpatient": (6.0, 0.6),     # ~ e^{6} ≈ 403; wide spread
    "hospitalization": (7.4, 0.55),  # ~ e^{7.4} ≈ 1640
    "disability": (8.0, 0.6),     # ~ 2980
    "death": (10.0, 0.4),         # ~ 22000 (but we’ll also cap by sum_assured)
}

DENIAL_RATE_BY_TYPE = {"outpatient": 0.08, "hospitalization": 0.10, "disability": 0.12, "death": 0.05}

CHANNELS = ["Broker", "Direct", "Agency", "Online"]
REGIONS  = ["North", "South", "East", "West"]
UW_CLASS = ["Standard", "Substandard"]
FAMILIES = ["Health", "Life"]

def daterange_months(start: date, end: date):
    """Yield first day of months between start and end inclusive."""
    cur = date(start.year, start.month, 1)
    last = date(end.year, end.month, 1)
    while cur <= last:
        yield cur
        cur = (cur + relativedelta(months=1)).replace(day=1)

def age_on(dob: date, on_date: date) -> int:
    return on_date.year - dob.year - ((on_date.month, on_date.day) < (dob.month, dob.day))

def sample_lognormal(meanlog, sdlog, size=None):
    return np.random.lognormal(mean=meanlog, sigma=sdlog, size=size)

# ---------- PRODUCTS ----------
def generate_products(n=N_PRODUCTS):
    products = []
    for i in range(n):
        fam = random.choice(FAMILIES)
        products.append({
            "product_code": f"P{i+1:03d}",
            "product_name": f"{fam} Plan {i+1}",
            "product_family": fam,
            "underwriting_class": random.choice(UW_CLASS),
            "waiting_period_days": random.choice([0, 30, 60, 90]) if fam == "Health" else 0
        })
    return pd.DataFrame(products)

# ---------- MEMBERS ----------
def generate_members(n=N_MEMBERS):
    members = []
    for i in range(n):
        dob = fake.date_of_birth(minimum_age=18, maximum_age=85)
        members.append({
            "member_id": i+1,
            "gender": random.choice(["M", "F"]),
            "birth_date": dob,
            "region": random.choice(REGIONS),
            "smoker_flag": random.random() < 0.25,  # ~25%
            "bmi": round(max(16, np.random.normal(27, 5)), 1),  # truncated at 16
            "join_date": fake.date_between(start_date="-5y", end_date="today")
        })
    df = pd.DataFrame(members)
    # Keep joins within model period
    df["join_date"] = pd.to_datetime(df["join_date"]).clip(lower=pd.Timestamp(START_DATE), upper=pd.Timestamp(END_DATE)).dt.date
    return df

# ---------- POLICIES ----------
def generate_policies(members: pd.DataFrame, products: pd.DataFrame, n=N_POLICIES):
    # assign a subset of members to have policies (1 policy/member for simplicity; some members might not have an active policy)
    chosen_member_ids = np.random.choice(members["member_id"], size=n, replace=False)
    chosen_members = members.set_index("member_id").loc[chosen_member_ids].reset_index()

    policies = []
    pid = 1
    for _, row in chosen_members.iterrows():
        prod = products.sample(1).iloc[0]
        fam = prod["product_family"]
        cover_type = "health" if fam == "Health" else "life"

        # policy dates
        start = max(row["join_date"], START_DATE)
        # random tenure 6–60 months within window
        months = random.randint(6, 60)
        end = (pd.to_datetime(start) + relativedelta(months=months)).date()
        end = min(end, END_DATE)

        # sum assured & premium
        if cover_type == "life":
            sum_assured = float(np.random.choice([50000, 100000, 150000, 250000, 500000], p=[0.35,0.35,0.15,0.1,0.05]))
            base_prem = sum_assured * 0.0008  # toy factor
        else:
            sum_assured = float(np.random.choice([5000, 10000, 20000, 50000], p=[0.4,0.35,0.2,0.05]))
            base_prem = 300 + np.random.gamma(2.0, 60)  # 300 + gamma noise

        premium_freq = np.random.choice(["M","Q","A"], p=[0.7,0.2,0.1])
        # convert to amount per frequency
        freq_div = {"M":12, "Q":4, "A":1}[premium_freq]
        premium_amount = round(max(10.0, base_prem / freq_div), 2)

        policies.append({
            "policy_id": pid,
            "member_id": int(row["member_id"]),
            "product_code": prod["product_code"],
            "cover_type": cover_type,
            "sum_assured": sum_assured,
            "start_date": start,
            "end_date": end,
            "premium_freq": premium_freq,
            "premium_amount": premium_amount,
            "channel": np.random.choice(CHANNELS)
        })
        pid += 1

    return pd.DataFrame(policies)

# ---------- PREMIUMS LEDGER ----------
def expand_premiums_ledger(policies: pd.DataFrame):
    rows = []
    for _, p in policies.iterrows():
        start = pd.to_datetime(p["start_date"]).date()
        end = pd.to_datetime(p["end_date"]).date()
        for m0 in daterange_months(start, end):
            # Earned premium approximation: convert freq to monthly equivalent
            freq_div = {"M":12, "Q":4, "A":1}[p["premium_freq"]]
            monthly_equiv = float(p["premium_amount"]) * freq_div / 12.0
            rows.append({
                "policy_id": int(p["policy_id"]),
                "period_month": m0.strftime("%Y-%m"),
                "earned_premium": round(monthly_equiv, 2)
            })
    return pd.DataFrame(rows)

# ---------- CLAIMS ----------
def annual_qx(age):
    for (lo, hi), q in BASE_QX_LIFE.items():
        if lo <= age <= hi:
            return q
    return list(BASE_QX_LIFE.values())[-1]

def member_health_lambda(age, smoker, bmi, uw_class):
    lam = BASE_LAMBDA_HEALTH
    if age >= 60: lam *= 1.6
    elif age >= 45: lam *= 1.3
    if smoker: lam *= 1.25
    if bmi >= 32: lam *= 1.2
    if uw_class == "Substandard": lam *= 1.2
    return lam

def simulate_claims(members: pd.DataFrame, policies: pd.DataFrame, products: pd.DataFrame):
    prod_map = products.set_index("product_code").to_dict(orient="index")
    pol = policies.merge(members[["member_id","gender","birth_date","region","smoker_flag","bmi"]], on="member_id", how="left")
    claims = []
    cid = 1
    for _, row in pol.iterrows():
        start = pd.to_datetime(row["start_date"]).date()
        end = pd.to_datetime(row["end_date"]).date()
        uwc = prod_map[row["product_code"]]["underwriting_class"]
        fam = prod_map[row["product_code"]]["product_family"]
        cover = row["cover_type"]

        # number of potential claim events over tenure
        months = max(1, (end.year - start.year) * 12 + (end.month - start.month) + 1)
        years = months / 12.0

        # HEALTH claims (Poisson)
        if cover == "health":
            lam = member_health_lambda(
                age_on(row["birth_date"], start),
                bool(row["smoker_flag"]),
                float(row["bmi"]),
                uwc
            ) * years
            n_claims = min(MAX_CLAIMS_PER_MEMBER, np.random.poisson(lam))
            for _ in range(n_claims):
                cdate = fake.date_between_dates(date_start=start, date_end=end)
                ctype = np.random.choice(["outpatient","hospitalization","disability"], p=[0.6,0.3,0.1])
                denial = random.random() < DENIAL_RATE_BY_TYPE[ctype]
                status = "denied" if denial else "closed"

                # severity (paid)
                sev = float(sample_lognormal(*SEVERITY_PARAMS[ctype]))
                paid = 0.0 if denial else round(sev, 2)

                claims.append({
                    "claim_id": cid,
                    "member_id": int(row["member_id"]),
                    "policy_id": int(row["policy_id"]),
                    "claim_date": cdate,
                    "notification_date": cdate + timedelta(days=random.randint(0,14)),
                    "diagnosis_code": np.random.choice(["A10","B20","C30","D40","E50"]),
                    "claim_type": ctype,
                    "status": status,
                    "initial_reserve": round(paid * np.random.uniform(0.8, 1.1), 2) if not denial else 0.0,
                    "approved_amount": paid,
                    "paid_amount": paid,
                    "close_date": cdate + timedelta(days=random.randint(5,60)) if not denial else cdate + timedelta(days=random.randint(1,10))
                })
                cid += 1

        # LIFE (death) — very rare, at most 1 per policy (and it closes policy in reality)
        else:
            age0 = age_on(row["birth_date"], start)
            qx = annual_qx(age0)
            # chance of occurrence during tenure ≈ qx * years (toy)
            if random.random() < min(0.9, qx * years):
                cdate = fake.date_between_dates(date_start=start, date_end=end)
                denial = random.random() < DENIAL_RATE_BY_TYPE["death"]
                status = "denied" if denial else "closed"
                # death severity capped by sum assured
                sev = float(sample_lognormal(*SEVERITY_PARAMS["death"]))
                paid = 0.0 if denial else float(min(sev, row["sum_assured"]))
                claims.append({
                    "claim_id": cid,
                    "member_id": int(row["member_id"]),
                    "policy_id": int(row["policy_id"]),
                    "claim_date": cdate,
                    "notification_date": cdate + timedelta(days=random.randint(0,7)),
                    "diagnosis_code": "DEATH",
                    "claim_type": "death",
                    "status": status,
                    "initial_reserve": round(paid, 2) if not denial else 0.0,
                    "approved_amount": paid,
                    "paid_amount": paid,
                    "close_date": cdate + timedelta(days=random.randint(5,30)) if not denial else cdate + timedelta(days=random.randint(1,10))
                })
                cid += 1

    return pd.DataFrame(claims)

# ---------- CLAIM PAYMENTS ----------
def simulate_payments(claims: pd.DataFrame):
    payments = []
    pid = 1
    for _, c in claims.iterrows():
        total = float(c["paid_amount"])
        if total <= 0:
            continue
        # split into 1–3 payments
        k = np.random.choice([1,2,3], p=[0.6,0.3,0.1])
        remaining = total
        pay_dates = sorted([
            pd.to_datetime(c["claim_date"]) + timedelta(days=int(d))
            for d in np.cumsum(np.random.randint(0, 45, size=k))
        ])
        # ensure last payment on/ before close_date
        if pd.notna(c["close_date"]):
            pay_dates[-1] = min(pay_dates[-1].date(), pd.to_datetime(c["close_date"]).date())

        parts = np.random.dirichlet(np.ones(k))
        for i in range(k):
            amt = round(remaining * parts[i], 2)
            if i == k-1:  # fix rounding
                amt = round(total - sum(p["payment_amount"] for p in payments if p["claim_id"] == c["claim_id"]), 2)
            payments.append({
                "payment_id": pid,
                "claim_id": int(c["claim_id"]),
                "payment_date": pd.to_datetime(pay_dates[i]).date(),
                "payment_amount": amt
            })
            pid += 1
    return pd.DataFrame(payments)

# ---------- CALENDAR ----------
def build_calendar(start=START_DATE, end=END_DATE):
    days = pd.date_range(start=start, end=end, freq="D")
    cal = pd.DataFrame({"dt": days})
    cal["month"] = cal["dt"].dt.month
    cal["quarter"] = cal["dt"].dt.quarter
    cal["year"] = cal["dt"].dt.year
    cal["dt"] = cal["dt"].dt.date
    return cal

# ---------- MAIN ----------
if __name__ == "__main__":
    print("▶ Generating products, members, policies, claims, payments, premiums_ledger, calendar")

    products = generate_products()
    members  = generate_members()
    policies = generate_policies(members, products)
    premiums = expand_premiums_ledger(policies)
    claims   = simulate_claims(members, policies, products)
    payments = simulate_payments(claims)
    calendar = build_calendar()

    # Save outputs
    outdir = "data/raw"
    products.to_csv(f"{outdir}/products.csv", index=False)
    members.to_csv(f"{outdir}/members.csv", index=False)
    policies.to_csv(f"{outdir}/policies.csv", index=False)
    claims.to_csv(f"{outdir}/claims.csv", index=False)
    payments.to_csv(f"{outdir}/claim_payments.csv", index=False)
    premiums.to_csv(f"{outdir}/premiums_ledger.csv", index=False)
    calendar.to_csv(f"{outdir}/calendar.csv", index=False)

    # Tiny summary
    print("✅ Done.")
    print(f"products: {len(products)} | members: {len(members)} | policies: {len(policies)}")
    print(f"claims: {len(claims)} | payments: {len(payments)} | premiums rows: {len(premiums)} | calendar days: {len(calendar)}")
