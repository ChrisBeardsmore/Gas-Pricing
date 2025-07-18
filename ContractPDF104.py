import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Dyce Decision Engine", layout="wide")

VERSION = "1.9 - July 2025"
LOGO_PATH = "DYCE-DARK BG.png"

# --- Enforce white background and dark text including input labels ---
st.markdown("""
    <style>
        .stApp {
            background-color: white;
            color: rgb(15,42,52);
        }
        label {
            color: rgb(15,42,52) !important;
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
        'Max Spend': st.sidebar.number_input(f"{role} - Max Spend (£)", 0, 1000000, 25000),
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

# --- Decision Logic ---
def run_decision():
    reasons = []
    decision = "Approved"

    if credit_score < refer_threshold:
        decision = "Declined"
        reasons.append("Declined: Credit Score below referral threshold")
    if ccjs == "Yes":
        decision = "Declined"
        reasons.append("Declined: CCJs or Defaults present")

    if decision != "Declined":
        if refer_threshold <= credit_score < approve_threshold:
            reasons.append("Referral: Credit Score between thresholds")

        if (business_type in ["Sole Trader", "Partnership"] and years_trading < 1) or (business_type == "Limited Company" and years_trading < 2):
            reasons.append("Referral: Insufficient trading history")

        if sic_risk in ["High", "Very High"]:
            reasons.append("Referral: SIC Risk is High/Very High")

        if payment_terms != "14 Days Direct Debit":
            reasons.append("Referral: Payment terms exceed maximum allowed")

        if unit_margin_ppkwh < minimum_unit_margin_ppkwh:
            reasons.append("Referral: Unit Margin below minimum")

        if broker_uplift_standing > max_broker_uplift_standing:
            reasons.append("Referral: Standing charge uplift exceeds maximum")

        if broker_uplift_unit_rate > max_broker_uplift_unit_rate:
            reasons.append("Referral: Unit rate uplift exceeds maximum")

    if decision == "Declined":
        required_approver = None
    else:
        required_approver = "Managing Director"
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
        self.set_text_color(15, 42, 52)
        self.cell(0, 10, f'Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

def export_to_pdf(inputs, decision, approver, reasons, timestamp):
    pdf = PDF()
    pdf.add_page()

    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(15, 42, 52)
    pdf.cell(0, 10, 'Dyce Credit Decision Report', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Inputs Summary:', ln=True)
    pdf.set_font('Arial', '', 12)
    for k, v in inputs.items():
        pdf.multi_cell(0, 10, f"{k}: {v}")

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Decision:', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, f"Decision: {decision}\nApprover Required: {approver if approver else 'N/A'}\nTimestamp: {timestamp}")

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Reasons / Stipulations:', ln=True)
    pdf.set_font('Arial', '', 12)
    for reason in reasons:
        pdf.multi_cell(0, 10, f"- {reason}")

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

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
        'SIC Description': sic_description,
        'SIC Risk': sic_risk,
        'Credit Score': credit_score,
        'Years Trading': years_trading,
        'CCJs': ccjs,
        'Payment Terms': payment_terms
    }

    final_decision, required_approver, reasons, timestamp = run_decision()

    st.subheader("Decision Results")
    st.write(f"**Final Decision:** {final_decision}")
    if required_approver:
        st.write(f"**Required Approver:** {required_approver}")
    st.write(f"**Timestamp:** {timestamp}")

    st.markdown("**Reasons / Stipulations:**")
    for reason in reasons:
        st.markdown(f"- {reason}")

    pdf_data = export_to_pdf(inputs, final_decision, required_approver, reasons, timestamp)
    st.download_button("Download PDF Report", pdf_data, "Credit_Decision_Report.pdf", "application/pdf")
