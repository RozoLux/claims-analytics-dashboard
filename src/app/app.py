import streamlit as st
import sqlite3
import pandas as pd

@st.cache_resource
def get_conn():
    return sqlite3.connect("db/claims.db", check_same_thread=False)

@st.cache_data
def fetch_df(query):
    with get_conn() as conn:
        return pd.read_sql_query(query, conn)

st.title("📊 Insurance Claims Analytics Dashboard")

# Define tab layout
tab1, tab2, tab3 = st.tabs(["Overview", "Claims Analysis", "Portfolio Mix"])

# ---- TAB 1: Overview ----
with tab1:
    st.header("🔍 KPIs & Loss Ratio Trend")

    kpi = fetch_df("SELECT * FROM vw_paid_kpis;")
    col1, col2, col3 = st.columns(3)
    col1.metric("🧾 Total Earned", f"{kpi['earned'][0]:,.0f} €")
    col2.metric("💸 Total Paid", f"{kpi['paid'][0]:,.0f} €")
    col3.metric("📉 Loss Ratio", f"{kpi['loss_ratio'][0]*100:.1f} %")

    st.subheader("📈 Monthly Loss Ratio")
    lr = fetch_df("SELECT * FROM vw_loss_ratio_monthly ORDER BY month;")
    st.line_chart(data=lr, x="month", y="loss_ratio")

# ---- TAB 2: Claims Analysis ----
with tab2:
    st.header("📊 Claims Breakdown by Type and Member Profile")

    # Load enriched claims data
    df = fetch_df("SELECT * FROM vw_claims_enriched")

    # --- Sidebar filters ---
    st.sidebar.header("🎯 Filter Claims By")
    gender = st.sidebar.selectbox("Gender", ["All"] + sorted(df["gender"].dropna().unique()))
    region = st.sidebar.selectbox("Region", ["All"] + sorted(df["region"].dropna().unique()))
    smoker = st.sidebar.selectbox("Smoker", ["All", True, False])
    product = st.sidebar.selectbox("Product Code", ["All"] + sorted(df["product_code"].dropna().unique()))

    # --- Claim Type filter ---
    claim_types = ["All"] + sorted(df["claim_type"].dropna().unique())
    claim_type = st.sidebar.selectbox("Claim Type", claim_types)

    # Apply filters
    filtered = df.copy()
    if gender != "All":
        filtered = filtered[filtered["gender"] == gender]
    if region != "All":
        filtered = filtered[filtered["region"] == region]
    if smoker != "All":
        if smoker is True:
            filtered = filtered[filtered["smoker_flag"] == 1]
        elif smoker is False:
            filtered = filtered[filtered["smoker_flag"] == 0]
    if product != "All":
        filtered = filtered[filtered["product_code"] == product]
    if claim_type != "All":
        filtered = filtered[filtered["claim_type"] == claim_type]

    # --- Filtered KPIs ---
    col1, col2 = st.columns(2)
    col1.metric("💸 Total Paid (Filtered)", f"{filtered['paid_amount'].sum():,.0f} €")
    col2.metric("📊 Average Claim", f"{filtered['paid_amount'].mean():,.2f} €")


    # --- Charts ---
    st.subheader("💰 Monthly Paid Amount")
    df_paid = (
    filtered.groupby([pd.to_datetime(filtered["claim_date"]).dt.to_period("M"), "claim_type"])["paid_amount"]
    .sum()
    .rename_axis(["month", "claim_type"])
    .reset_index()
    )
    df_paid["month"] = df_paid["month"].astype(str)
    pivot = df_paid.pivot(index="month", columns="claim_type", values="paid_amount").fillna(0)
    st.line_chart(pivot)

    st.subheader("📄 Filtered Claims Data")
    st.dataframe(filtered.head(50))


# ---- TAB 3: Portfolio Mix ----
with tab3:
    st.header("📦 Portfolio Mix Overview")

    # Load data from the view
    mix = fetch_df("SELECT * FROM vw_member_portfolio")

    st.subheader("🧬 Gender Distribution")
    st.bar_chart(mix["gender"].value_counts())

    st.subheader("🚬 Smoker vs Non-Smoker")
    st.bar_chart(mix["smoker_flag"].value_counts())

    st.subheader("🌍 Regional Distribution")
    st.bar_chart(mix["region"].value_counts())

    st.subheader("🛡️ Product Mix")
    st.bar_chart(mix["product_family"].value_counts())


