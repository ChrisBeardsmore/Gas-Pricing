import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

st.set_page_config(page_title="Dyce Decision Engine", layout="centered")

VERSION = "1.4 - July 2025"

st.title(f"⚡ Dyce Decision Engine (v{VERSION})")

LOGO_PATH = "DYCE-DARK BG.png"
FONT_REGULAR = ".streamlit/Montserrat-Regular.ttf"
FONT_BOLD = ".streamlit/Montserrat-Bold.ttf"
FONT_ITALIC = ".streamlit/Montserrat-Italic.ttf"

SIC_CODES_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/Sic%20Codes.xlsx"

@st.cache_data
def load_sic_codes():
    df = pd.read_excel(SIC_CODES_URL)
    df['SIC_Code'] = df['SIC_Code'].astype(str).str.strip()
    return df

sic_df = load_sic_codes()

class PDF(FPDF):
    def header(self):
        self.image(LOGO_PATH, x=10, y=8, w=50)
        self.ln(35)

    def footer(self):
        self.set_y(-15)
        self.set_font('Montserrat', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Dyce Energy Decision Report - Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

# --- PDF Export Function ---
def export_to_pdf(decision, approver, reasons, timestamp):
    pdf = PDF()
    pdf.add_page()

    pdf.add_font('Montserrat', '', FONT_REGULAR, uni=True)
    pdf.add_font('Montserrat', 'B', FONT_BOLD, uni=True)
    pdf.add_font('Montserrat', 'I', FONT_ITALIC, uni=True)

    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(15, 42, 52)

    pdf.set_font('Montserrat', 'B', 16)
    pdf.cell(0, 10, 'Dyce Credit Decision Report', ln=True, align='C')
    pdf.ln(10)

    pdf.set_font('Montserrat', 'B', 12)
    pdf.cell(0, 10, 'Decision Details', ln=True)

    pdf.set_font('Montserrat', '', 12)
    pdf.multi_cell(0, 10, f"Decision: {decision}\nApprover Required: {approver}\nTimestamp: {timestamp}")
    pdf.ln(5)

    pdf.set_font('Montserrat', 'B', 12)
    pdf.cell(0, 10, 'Reasons / Stipulations:', ln=True)

    pdf.set_font('Montserrat', '', 12)
    for reason in reasons:
        pdf.set_text_color(222, 0, 185)
        pdf.multi_cell(0, 10, f"- {reason}")
        pdf.set_text_color(15, 42, 52)

    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer = BytesIO(pdf_bytes)
    return buffer

# --- Decision Logic Example ---
def run_decision():
    decision = "Approved"
    required_approver = "Sales Agent"
    reasons = []

    # Example: input checks (replace with real input capture logic)
    credit_score = 75
    years_trading = 3
    ccjs = "No"
    sic_risk = "Medium"
    payment_terms = "14 Days Direct Debit"

    if credit_score < 60:
        decision = "Declined"
        reasons.append("Credit Score below 60")
    elif credit_score < 80:
        decision = "Referral"
        reasons.append("Credit Score between 60-79")

    if ccjs == "Yes":
        decision = "Declined"
        reasons.append("CCJ present")

    if years_trading < 1:
        reasons.append("Less than 1 year trading")

    if sic_risk in ["High", "Very High"]:
        reasons.append("High/Very High sector risk")

    if payment_terms != "14 Days Direct Debit":
        reasons.append("Payment terms not standard (Direct Debit 14 days)")

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return decision, required_approver, reasons, timestamp

if st.button("Run Decision Engine"):
    final_decision, required_approver, reasons, timestamp = run_decision()

    st.subheader("Decision Results")
    st.write(f"**Final Decision:** {final_decision}")
    st.write(f"**Required Approver:** {required_approver}")
    st.write(f"**Timestamp:** {timestamp}")

    if reasons:
        st.markdown("**Reasons / Stipulations:**")
        for reason in reasons:
            st.markdown(f"- {reason}")
    else:
        st.write("No specific stipulations or referrals.")

    pdf_data = export_to_pdf(final_decision, required_approver, reasons, timestamp)
    st.download_button(label="Download Decision Report as PDF", data=pdf_data, file_name="Credit_Decision_Report.pdf", mime="application/pdf")
