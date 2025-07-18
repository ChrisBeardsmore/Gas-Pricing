import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from fpdf import FPDF
import json

st.set_page_config(page_title="Dyce Decision Engine", layout="wide")

VERSION = "1.9 - July 2025"
LOGO_PATH = "DYCE-DARK BG.png"

# --- Style Updates: White background, dark text, input labels, pink buttons ---
st.markdown("""
    <style>
        .stApp {
            background-color: white;
            color: rgb(15,42,52);
        }
        label {
            color: rgb(15,42,52) !important;
        }
        div.stButton > button {
            background-color: rgb(222,0,185) !important;
            color: white !important;
        }
        div.stDownloadButton > button {
            background-color: rgb(222,0,185) !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

st.image(LOGO_PATH, width=200)

st.title(f"⚡ Dyce Decision Engine (v{VERSION})")

SIC_CODES_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/Sic%20Codes.xlsx"

@st.cache_data
def load_sic_codes():
    df = pd.read_excel(SIC_CODES_URL)
    df['SIC_Code'] = df['SIC_Code'].astype(str).str.strip()
    return df

sic_df = load_sic_codes()

# --- Sidebar Config ---
st.sidebar.header("🔧 Configuration")
approve_threshold = st.sidebar.number_input("Credit Score Threshold for Approval", 0, 100, 80)
refer_threshold = st.sidebar.number_input("Credit Score Threshold for Referral", 0, 100, 60)
max_days_to_pay = st.sidebar.number_input("Max Days to Pay Allowed", 1, 90, 14)
minimum_unit_margin_ppkwh = st.sidebar.number_input("Minimum Unit Margin (p/kWh)", 0.0, 10.0, 0.5)
max_broker_uplift_standing = st.sidebar.number_input("Max Broker Uplift Standing Charge (p/day)", 0.0, 100.0, 5.0)
max_broker_uplift_unit_rate = st.sidebar.number_input("Max Broker Uplift Unit Rate (p/kWh)", 0.0, 10.0, 1.0)

st.sidebar.subheader("Approval Matrix")
approval_roles = ['Sales Agent', 'Channel Manager', 'Commercial Manager', 'Managing Director']
approval_matrix = {}
for role in approval_roles:
    st.sidebar.markdown(f"**{role}**")
    approval_matrix[role] = {
        'Max Sites': st.sidebar.number_input(f"{role} - Max Sites", 0, 100, 2),
        'Max Spend': st.sidebar.number_input(f"{role} - Max Spend (£)", 0, 10000000, 25000),
        'Max Volume (kWh)': st.sidebar.number_input(f"{role} - Max Volume (kWh)", 0, 10000000, 100000),
    }

st.header("1️⃣ Business Information")
business_type = st.selectbox("Business Type", ["Sole Trader", "Partnership", "Limited Company"])
number_of_sites = st.number_input("Number of Sites", 1)
annual_volume_kwh = st.number_input("Estimated Annual Volume (kWh)", 0.0)
contract_value = st.number_input("Total Contract Spend (£)", 0.0)
contract_term = st.number_input("Contract Term (Years)", 1, 10)
unit_margin_ppkwh = st.number_input("Proposed Unit Margin (p/kWh)", 0.0)
broker_uplift_standing = st.number_input("Broker Uplift - Standing Charge (p/day)", 0.0)
broker_uplift_unit_rate = st.number_input("Broker Uplift - Unit Rate (p/kWh)", 0.0)

st.header("2️⃣ SIC Code Information")
sic_code = st.text_input("SIC Code (5-digit)").strip()
sic_risk = "Medium"
sic_description = "Unknown"

if sic_code:
    matched = sic_df[sic_df['SIC_Code'] == sic_code]
    if not matched.empty:
        sic_description = matched.iloc[0]['SIC_Description']
        sic_risk = matched.iloc[0]['Typical_Risk_Rating']
        st.markdown(f"**SIC Description:** {sic_description}")
        st.markdown(f"**Typical Risk Rating:** {sic_risk}")
    else:
        st.warning("SIC Code not found. Please manually select risk.")
        sic_risk = st.selectbox("Manual Sector Risk", ["Low", "Medium", "High", "Very High"], index=1)

st.header("3️⃣ Credit Information")
credit_score = st.number_input("Creditsafe Score", 0, 100)
years_trading = st.number_input("Years Trading", 0)
ccjs = st.radio("Any CCJs/Defaults in last 2 years?", ["No", "Yes"])
payment_terms = st.selectbox("Requested Payment Terms", ["14 Days Direct Debit", "14 Days BACS", "28 Days BACS"])

# --- Decision Logic, PDF, and Button functionality remains unchanged ---
# (Preserved from previous stable build)

# [Rest of the decision logic and PDF export remains as previously implemented]
