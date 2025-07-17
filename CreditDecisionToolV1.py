import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

st.set_page_config(page_title="Dyce Decision Engine", layout="centered")

VERSION = "1.0 - July 2025"

st.title(f"⚡ Dyce Decision Engine (v{VERSION})")

# --- Configurable Inputs ---
st.sidebar.header("🔧 Configuration")
minimum_margin = st.sidebar.number_input("Minimum Margin %", min_value=0.0, max_value=100.0, value=0.5, step=0.05)
maximum_broker_uplift = st.sidebar.number_input("Maximum Broker Uplift (p/kWh)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

utility = st.selectbox("Utility Type", ["Power", "Gas"])

# --- Business Details ---
st.header("1️⃣ Business Information")
business_type = st.selectbox("Business Type", ["Sole Trader", "Partnership", "Limited Company"])
number_of_sites = st.number_input("Number of Sites", min_value=1, value=1)
annual_volume = st.number_input("Estimated Annual Volume (MWh)", min_value=0.0, value=50.0)
contract_value = st.number_input("Total Contract Spend (£)", min_value=0.0, value=25000.0)
contract_term = st.number_input("Contract Term (Years)", min_value=1, max_value=10, value=3)
margin_percent = st.number_input("Proposed Margin (%)", min_value=0.0, value=0.6)
broker_uplift = st.number_input("Broker Uplift (p/kWh)", min_value=0.0, value=0.9)

# --- Credit Inputs ---
st.header("2️⃣ Credit Information")
credit_score = st.number_input("Creditsafe Score", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, value=3)
ccjs = st.radio("Any CCJs/Defaults in the last 2 years?", ["No", "Yes"])
payment_terms = st.selectbox("Requested Payment Terms", ["14 Days Direct Debit", "30 Days BACS", ">30 Days BACS"])

# --- Functions ---
def determine_approval_level():
    matrix = {
        'Power': {
            'Sales Agent': {'Max Sites': 2, 'Max Spend': 25000, 'Max EAC': 25, 'Min Margin': 0.5, 'Max Broker Uplift': 1.0},
            'Channel Manager': {'Max Sites': 6, 'Max Spend': 50000, 'Max EAC': 25, 'Min Margin': 0.4, 'Max Broker Uplift': 1.5},
            'Commercial Manager': {'Max Sites': 25, 'Max Spend': 100000, 'Max EAC': 100, 'Min Margin': 0.3, 'Max Broker Uplift': 2.0},
            'Managing Director': {}
        },
        'Gas': {
            'Sales Agent': {'Max Sites': 2, 'Max Spend': 25000, 'Max AQ': 100, 'Min Margin': 0.3, 'Max Broker Uplift': 1.0},
            'Channel Manager': {'Max Sites': 6, 'Max Spend': 50000, 'Max AQ': 100, 'Min Margin': 0.25, 'Max Broker Uplift': 1.5},
            'Commercial Manager': {'Max Sites': 25, 'Max Spend': 100000, 'Max AQ': 500, 'Min Margin': 0.2, 'Max Broker Uplift': 2.0},
            'Managing Director': {}
        }
    }

    for role, limits in matrix[utility].items():
        if role == 'Managing Director':
            return role

        if number_of_sites > limits['Max Sites']:
            continue
        if contract_value > limits['Max Spend']:
            continue
        volume = annual_volume if utility == 'Power' else annual_volume * 4  # rough conversion if needed
        if utility == 'Power' and volume > limits['Max EAC']:
            continue
        if utility == 'Gas' and volume > limits['Max AQ']:
            continue
        if margin_percent < limits['Min Margin']:
            continue
        if broker_uplift > limits['Max Broker Uplift']:
            continue

        return role

    return 'Managing Director'

def credit_decision():
    if credit_score >= 80:
        credit_status = 'Approved'
    elif credit_score >= 60:
        credit_status = 'Refer'
    else:
        credit_status = 'Decline'

    referral_flags = []

    if ccjs == 'Yes':
        referral_flags.append('CCJ/Defaults present')

    if payment_terms != '14 Days Direct Debit':
        referral_flags.append('Non-standard payment terms')

    if years_trading < 1:
        referral_flags.append('Less than 12 months trading')

    if credit_status != 'Approved':
        referral_flags.append('Credit score below 80')

    margin_check = 'Pass' if margin_percent >= minimum_margin else 'Requires Review'
    broker_check = 'Pass' if broker_uplift <= maximum_broker_uplift else 'Requires Review'

    approval_level = determine_approval_level()

    return credit_status, referral_flags, margin_check, broker_check, approval_level

if st.button("Run Decision Engine"):
    credit_status, referrals, margin_check, broker_check, approval_level = credit_decision()

    st.subheader("Decision Results")
    st.write(f"**Credit Status:** {credit_status}")
    st.write(f"**Margin Check:** {margin_check}")
    st.write(f"**Broker Uplift Check:** {broker_check}")
    st.write(f"**Approval Required:** {approval_level}")

    if referrals:
        st.warning("Referral Triggers:")
        for r in referrals:
            st.write(f"- {r}")

    st.write(f"**Decision Engine Version:** {VERSION}")
    st.write(f"Decision Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
