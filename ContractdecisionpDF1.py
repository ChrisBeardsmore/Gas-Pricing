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

# [Inputs Section remains unchanged — as per your provided code]

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
        reasons.append("CCJs or Defaults in last 2 years")

    if decision != "Declined":
        if refer_threshold <= credit_score < approve_threshold:
            reasons.append("Referral: Credit Score between referral and approval thresholds")

        if years_trading < 1:
            reasons.append("Referral: Less than 1 year trading")

        if sic_risk in ["High", "Very High"]:
            reasons.append("Referral: High/Very High SIC Risk")

        if unit_margin_ppkwh < minimum_unit_margin_ppkwh:
            reasons.append("Referral: Unit Margin below minimum")

        if broker_uplift_standing > max_broker_uplift_standing:
            reasons.append("Referral: Broker Standing Charge uplift exceeds maximum")

        if broker_uplift_unit_rate > max_broker_uplift_unit_rate:
            reasons.append("Referral: Broker Unit Rate uplift exceeds maximum")

        if payment_terms != "14 Days Direct Debit":
            reasons.append("Referral: Non-standard payment terms")

        # Approver matrix evaluation
        for role in approval_roles:
            limits = approval_matrix[role]
            if (number_of_sites <= limits['Max Sites'] and
                contract_value <= limits['Max Spend'] and
                annual_volume_kwh <= limits['Max Volume (kWh)'] and
                unit_margin_ppkwh >= limits['Min Unit Margin (p/kWh)'] and
                broker_uplift_standing <= limits['Max Broker Uplift - Standing Charge (p/day)'] and
                broker_uplift_unit_rate <= limits['Max Broker Uplift - Unit Rate (p/kWh)']):
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
        self.set_font('Montserrat', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Dyce Energy Decision Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

def export_to_pdf(inputs, decision, approver, reasons, timestamp):
    pdf = PDF()
    pdf.add_page()
    pdf.add_font('Montserrat', '', FONT_REGULAR, uni=True)
    pdf.add_font('Montserrat', 'B', FONT_BOLD, uni=True)
    pdf.add_font('Montserrat', 'I', FONT_ITALIC, uni=True)

    pdf.set_text_color(15, 42, 52)
    pdf.set_font('Montserrat', 'B', 16)
    pdf.cell(0, 10, 'Dyce Credit Decision Report', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Montserrat', 'B', 12)
    pdf.cell(0, 10, 'Inputs:', ln=True)
    pdf.set_font('Montserrat', '', 12)
    for k, v in inputs.items():
        pdf.multi_cell(0, 10, f"{k}: {v}")

    pdf.ln(5)
    pdf.set_font('Montserrat', 'B', 12)
    pdf.cell(0, 10, 'Decision Summary:', ln=True)
    pdf.set_font('Montserrat', '', 12)
    pdf.multi_cell(0, 10, f"Decision: {decision}\nApprover: {approver}\nTimestamp: {timestamp}")

    pdf.ln(5)
    pdf.set_font('Montserrat', 'B', 12)
    pdf.cell(0, 10, 'Reasons / Stipulations:', ln=True)
    pdf.set_font('Montserrat', '', 12)
    for reason in reasons:
        pdf.multi_cell(0, 10, f"- {reason}")

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    return BytesIO(pdf_bytes)

# --- Run Decision on Button ---
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
