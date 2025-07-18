import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Dyce Decision Engine", layout="centered")

VERSION = "1.5 - July 2025"

LOGO_PATH = "DYCE-DARK BG.png"
FONT_REGULAR = ".streamlit/Montserrat-Regular.ttf"
FONT_BOLD = ".streamlit/Montserrat-Bold.ttf"
FONT_ITALIC = ".streamlit/Montserrat-Italic.ttf"

st.image(LOGO_PATH, width=200)
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

st.sidebar.subheader("Margin & Uplift Limits")
minimum_unit_margin_ppkwh = st.sidebar.number_input("Minimum Unit Margin (p/kWh)", min_value=0.0, max_value=10.0, value=0.5, step=0.05)
max_broker_uplift_standing = st.sidebar.number_input("Max Broker Uplift - Standing Charge (p/day)", min_value=0.0, max_value=100.0, value=5.0)
max_broker_uplift_unit_rate = st.sidebar.number_input("Max Broker Uplift - Unit Rate (p/kWh)", min_value=0.0, max_value=10.0, value=1.0)

approval_roles = ['Sales Agent', 'Channel Manager', 'Commercial Manager', 'Managing Director']
approval_matrix = {
    'Sales Agent': {'Max Sites': 2, 'Max Spend': 25000, 'Max Volume (kWh)': 100000},
    'Channel Manager': {'Max Sites': 6, 'Max Spend': 50000, 'Max Volume (kWh)': 250000},
    'Commercial Manager': {'Max Sites': 25, 'Max Spend': 100000, 'Max Volume (kWh)': 500000},
    'Managing Director': {'Max Sites': float('inf'), 'Max Spend': float('inf'), 'Max Volume (kWh)': float('inf')}
}

# --- Business Information ---
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

# --- Credit Information ---
st.header("3️⃣ Credit Information")
credit_score = st.number_input("Creditsafe Score", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, value=3)
ccjs = st.radio("Any CCJs/Defaults in the last 2 years?", ["No", "Yes"])
payment_terms = st.selectbox("Requested Payment Terms", ["14 Days Direct Debit", "14 Days BACS", "28 Days BACS"])

# --- Decision Logic ---
def run_decision():
    reasons = []
    decision = "Approved"
    required_approver = "Sales Agent"

    if credit_score < refer_threshold:
        decision = "Declined"
        reasons.append("Credit Score below referral threshold")
    if ccjs == "Yes":
        decision = "Declined"
        reasons.append("CCJs/Defaults present")

    if decision != "Declined":
        if refer_threshold <= credit_score < approve_threshold:
            reasons.append("Credit Score between thresholds")

        if years_trading < 1:
            reasons.append("Less than 1 year trading")

        if sic_risk in ["High", "Very High"]:
            reasons.append("High/Very High SIC Risk")

        if unit_margin_ppkwh < minimum_unit_margin_ppkwh:
            reasons.append("Margin below minimum threshold")

        if broker_uplift_standing > max_broker_uplift_standing:
            reasons.append("Standing charge uplift exceeds maximum")

        if broker_uplift_unit_rate > max_broker_uplift_unit_rate:
            reasons.append("Unit rate uplift exceeds maximum")

        if payment_terms != "14 Days Direct Debit":
            reasons.append("Non-standard payment terms")

        for role in approval_roles:
            limits = approval_matrix[role]
            if (number_of_sites <= limits['Max Sites'] and
                contract_value <= limits['Max Spend'] and
                annual_volume_kwh <= limits['Max Volume (kWh)']):
                required_approver = role
                break

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return decision, required_approver, reasons, timestamp

# --- PDF Export ---
class PDF(FPDF):
    def header(self):
        self.image(LOGO_PATH, x=10, y=8, w=50)
        self.ln(35)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Dyce Energy Decision Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

def export_to_pdf(inputs, decision, approver, reasons, timestamp):
    pdf = PDF()
    pdf.add_page()

    pdf.set_text_color(15, 42, 52)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Dyce Credit Decision Report', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Inputs:', ln=True)
    pdf.set_font('Arial', '', 12)
    for k, v in inputs.items():
        pdf.multi_cell(0, 10, f"{k}: {v}")

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Decision Summary:', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f"Decision: {decision}\nApprover: {approver}\nTimestamp: {timestamp}")

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Reasons / Stipulations:', ln=True)
    pdf.set_font('Arial', '', 12)
    for reason in reasons:
        pdf.multi_cell(0, 10, f"- {reason}")

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

# --- Run Decision ---
if st.button("Run Decision Engine"):
    inputs = {
        'Business Type': business_type,
        'Number of Sites': number_of_sites,
        'Annual Volume': annual_volume_kwh,
        'Contract Value': contract_value,
        'Contract Term': contract_term,
        'Unit Margin': unit_margin_ppkwh,
        'Broker Uplift Standing': broker_uplift_standing,
        'Broker Uplift Unit Rate': broker_uplift_unit_rate,
        'SIC Code': sic_code,
        'SIC Sector': sic_sector,
        'SIC Risk': sic_risk,
        'Credit Score': credit_score,
        'Years Trading': years_trading,
        'CCJs': ccjs,
        'Payment Terms': payment_terms
    }

    final_decision, required_approver, reasons, timestamp = run_decision()

    st.subheader("Decision Results")
    st.write(f"**Version:** {VERSION}")
    st.write(f"**Timestamp:** {timestamp}")
    st.write(f"**Final Decision:** {final_decision}")
    st.write(f"**Required Approver:** {required_approver}")

    if reasons:
        st.markdown("**Reasons / Stipulations:**")
        for reason in reasons:
            st.markdown(f"- {reason}")
    else:
        st.write("No stipulations or referrals.")

    pdf_data = export_to_pdf(inputs, final_decision, required_approver, reasons, timestamp)
    st.download_button(label="Download Decision Report as PDF", data=pdf_data, file_name="Credit_Decision_Report.pdf", mime="application/pdf")
