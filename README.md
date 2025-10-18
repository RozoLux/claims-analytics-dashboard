# 📊 Insurance Claims Analytics Dashboard

An interactive Streamlit app to explore and analyze synthetic health insurance claims using SQL + Python + AI tools.

![dashboard screenshot](screenshot.png) <!-- Replace or delete if you don’t have it yet -->

---

## 🚀 Features

- 📈 KPI Overview: Total Paid, Earned Premiums, Loss Ratio
- 🧍 Member & Claims Filtering: Gender, Region, Smoker Status, Product Code, Claim Type
- 📉 Monthly Trends: Claims Paid, Loss Ratio Over Time
- 🧩 Portfolio Mix: Visual breakdown by product, region, and more
- 🛠 SQL Views + Pandas for flexible data queries
- 🤖 Ready to extend with ML features (e.g. claim prediction)

---

## 🧰 Tech Stack

- **Python** + **Pandas**
- **SQLite** + custom SQL views
- **Streamlit** UI framework
- **Plotly / Matplotlib** for charts
- Git + GitHub for version control

---

## ⚙️ How to Run Locally

```bash
# Clone the repo and install dependencies:

```bash
git clone https://github.com/RozoLux/claims-analytics-dashboard.git
cd claims-analytics-dashboard
pip install -r requirements.txt

# Create and activate virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run src/app/app.py

📦 claims-analytics-dashboard
│
├── data/             # Raw CSVs and input data
├── db/               # SQLite DB and SQL view scripts
├── notebooks/        # Jupyter notebooks for EDA
├── src/app/          # Streamlit app code
├── README.md         # Project overview (you're here)
└── requirements.txt  # Python dependencies
