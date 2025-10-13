# 🧾 Insurance Claims Analytics Dashboard

This Streamlit dashboard helps visualize and analyze insurance claims, member risk profiles, and loss ratios using SQLite + Pandas + SQL Views.

## 🚀 Features
- KPIs (Total Paid, Earned, Loss Ratio)
- Claims filtering by gender, region, smoker flag, product, and claim type
- Monthly trends: Loss Ratio & Paid Amount
- Portfolio Mix: Gender, Region, Product, Smoker
- SQLite backend with SQL views
- Easy to extend for ML or production

## 📊 Tech Stack
- Python / Pandas
- SQLite / SQL Views
- Streamlit
- Matplotlib / Plotly (optional)
- Git & GitHub

## 📦 How to Run

```bash
git clone https://github.com/your-username/claims-analytics-dashboard.git
cd claims-analytics-dashboard
pip install -r requirements.txt
streamlit run src/app/app.py
