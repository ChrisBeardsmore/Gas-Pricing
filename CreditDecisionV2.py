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

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- Remaining Decision Engine and Streamlit logic remains unchanged ---
