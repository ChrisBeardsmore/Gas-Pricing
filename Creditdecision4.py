import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Dyce Decision Engine", layout="centered")

VERSION = "1.2 - July 2025"

st.title(f"⚡ Dyce Decision Engine (v{VERSION})")

SIC_CODES_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/Sic%20Codes.xlsx"

@st.cache_data
def load_sic_codes():
    df = pd.read_excel(SIC_CODES_URL)
    df['SIC_Code'] = df['SIC_Code'].astype(str).str.strip()
    return df

sic_df = load_sic_codes()

# --- Configurable Inputs ---
st.sidebar.header("🔧 Configuration")

st.sidebar.subheader("Credit Criteria")
approve_threshold = st.sidebar.number_input("Credit Score Threshold for Approval", min_value=0, max_value=100, value=80)
refer_threshold = st.sidebar.number_input("Credit Score Threshold for Referral", min_value=0, max_value=100, value=60)
max_days_to_pay = st.sidebar.number_input("Max Days to Pay Allowed", min_value=1, value=14)

st.sidebar.subheader("Margin & Uplift Limits")
minimum_unit_margin_ppkwh = st.sidebar.number_input("Minimum Unit Margin (p/kWh)", min_value=0.0, max_value=10.0, value=0.5, step=0.05)
max_broker_uplift_standing = st.sidebar.number_input("Max Broker Uplift - Standing Charge (p/day)", min_value=0.0, max_value=100.0, value=5.0)
max_broker_uplift_unit_rate = st.sidebar.number_input("Max Broker Uplift - Unit Rate (p/kWh)", min_value=0.0, max_value=10.0, value=1.0)

st.sidebar.subheader("Approval Matrix")
utility = st.sidebar.selectbox("Utility Type", ["Power", "Gas"])

approval_roles = ['Sales Agent', 'Channel Manager', 'Commercial Manager', 'Managing Director']
approval_matrix = {}

for role in approval_roles:
    st.sidebar.markdown(f"**{role}**")
    approval_matrix[role] = {
        'Max Sites': st.sidebar.number_input(f"{role} - Max Sites", min_value=0, value=25 if role == 'Commercial Manager' else 2),
        'Max Spend': st.sidebar.number_input(f"{role} - Max Spend (£)", min_value=0, value=100000 if role == 'Commercial Manager' else 25000),
        'Max Volume (kWh)": st.sidebar.number_input(f"{role} - Max Volume (kWh)", min_value=0, value=500000 if role == 'Commercial Manager' else 100000),
        'Min Unit Margin (p/kWh)': st.sidebar.number_input(f"{role} - Min Unit Margin (p/kWh)", min_value=0.0, value=0.5),
        'Max Broker Uplift - Standing Charge (p/day)': st.sidebar.number_input(f"{role} - Max Broker Uplift - Standing Charge (p/day)", min_value=0.0, value=5.0),
        'Max Broker Uplift - Unit Rate (p/kWh)': st.sidebar.number_input(f"{role} - Max Broker Uplift - Unit Rate (p/kWh)", min_value=0.0, value=1.0)
    }

# --- Business Details ---
st.header("1️⃣ Business Information")
business_type = st.selectbox("Business Type", ["Sole Trader", "Partnership", "Limited Company"])
number_of_sites = st.number_input("Number of Sites", min_value=1, value=1)
annual_volume_kwh = st.number_input("Estimated Annual Volume (kWh)", min_value=0.0, value=50000.0)
contract_value = st.number_input("Total Contract Spend (£)", min_value=0.0, value=25000.0)
contract_term = st.number_input("Contract Term (Years)", min_value=1, max_value=10, value=3)

unit_margin_ppkwh = st.number_input("Proposed Unit Margin (p/kWh)", min_value=0.0, value=0.6)
broker_uplift_standing = st.number_input("Broker Uplift - Standing Charge (p/day)", min_value=0.0, value=0.5)
broker_uplift_unit_rate = st.number_input("Broker Uplift - Unit Rate (p/kWh)", min_value=0.0, value=0.9)

# --- SIC Code and Risk ---
st.header("2️⃣ SIC Code Information")
sic_code = st.text_input("SIC Code (enter 5-digit code if known)").strip()
sic_sector = "Unknown"
sic_risk = "Medium"

if sic_code:
    matched = sic_df[sic_df['SIC_Code'] == sic_code]
    if not matched.empty:
        sic_sector = matched.iloc[0]['Sector']
        sic_risk = matched.iloc[0]['Typical_Risk_Rating']
    else:
        sic_risk = st.selectbox("Manual Sector Risk (SIC not found)", ["Low", "Medium", "High", "Very High"], index=1)

st.markdown(f"**SIC Sector:** {sic_sector}")
st.markdown(f"**Typical SIC Risk Rating:** {sic_risk}")

# --- Credit Inputs ---
st.header("3️⃣ Credit Information")
credit_score = st.number_input("Creditsafe Score", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, value=3)
ccjs = st.radio("Any CCJs/Defaults in the last 2 years?", ["No", "Yes"])
payment_terms = st.selectbox("Requested Payment Terms", ["14 Days Direct Debit", "30 Days BACS", ">30 Days BACS"])

if st.button("Run Decision Engine"):
    st.subheader("Decision Results")
    st.write(f"**Version:** {VERSION}")
    st.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
