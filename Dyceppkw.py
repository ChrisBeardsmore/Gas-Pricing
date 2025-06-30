import streamlit as st
import pandas as pd
import io

# ====== Branding Settings ======
BRAND_PRIMARY_COLOR = "#0F2A34"  # Dyce dark blue
BRAND_ACCENT_COLOR = "#DE00B9"   # Dyce magenta
LOGO_URL = "Dyce_logo.png"      # Replace with your actual logo file or URL
COMPANY_NAME = "Dyce Energy"
APP_TITLE = "Gas Pricing Uplift Calculator"
APP_TAGLINE = "Business Energy Made Simple"
FOOTER = "© 2025 Dyce Energy – Confidential Pricing Tool"

# ====== Streamlit Page Config ======
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ====== Custom CSS ======
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Montserrat', sans-serif;
        color: {BRAND_PRIMARY_COLOR};
    }}
    .stButton>button {{
        background-color: {BRAND_ACCENT_COLOR};
        color: white;
        font-weight: 600;
        border-radius: 6px;
        padding: 0.4rem 1rem;
    }}
    .stButton>button:hover {{
        background-color: #b80091;
        color: white;
    }}
    .block-container {{
        padding-top: 2rem;
    }}
    </style>
""", unsafe_allow_html=True)

# ====== Header Branding ======
st.markdown(
    f"""
    <div style="display: flex; align-items: center; padding: 0 0 1rem 0;">
        <img src="{LOGO_URL}" alt="Dyce Logo" style="height: 60px; margin-right: 20px;">
        <div>
            <h1 style="margin-bottom: 0; color: {BRAND_PRIMARY_COLOR};">{APP_TITLE}</h1>
            <p style="margin-top: 0; font-size: 1.1em; color: {BRAND_ACCENT_COLOR};">{APP_TAGLINE}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ====== File Upload ======
uploaded_file = st.file_uploader("Upload your flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File loaded successfully.")
    st.write("Preview of your data:")
    st.dataframe(df.head())

    st.markdown("---")
    st.subheader("Step 1 – Enter Uplift (in pence) per Band & Contract Length")

    # Define default bands
    default_bands = [
        {"Min": 0, "Max": 999},
        {"Min": 1000, "Max": 24999},
        {"Min": 25000, "Max": 49999},
        {"Min": 50000, "Max": 73199},
        {"Min": 73200, "Max": 124999},
        {"Min": 125000, "Max": 292999},
        {"Min": 293000, "Max": 731999},
    ]

    band_inputs = []

    with st.expander("🔧 Click to edit all 7 bands × 3 contract terms", expanded=True):
        for i, band in enumerate(default_bands):
            st.markdown(f"**Band {i+1}: {band['Min']}–{band['Max']} kWh**")
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            inputs = {
                "Min": band["Min"],
                "Max": band["Max"],
                "Unit_1": col1.number_input(f"Unit Uplift 1Y (p)", key=f"u1_{i}", value=0.5),
                "Stand_1": col2.number_input(f"Standing Uplift 1Y (p)", key=f"s1_{i}", value=1.0),
                "Unit_2": col3.number_input(f"Unit Uplift 2Y (p)", key=f"u2_{i}", value=0.4),
                "Stand_2": col4.number_input(f"Standing Uplift 2Y (p)", key=f"s2_{i}", value=0.9),
                "Unit_3": col5.number_input(f"Unit Uplift 3Y (p)", key=f"u3_{i}", value=0.3),
                "Stand_3": col6.number_input(f"Standing Uplift 3Y (p)", key=f"s3_{i}", value=0.8),
            }
            band_inputs.append(inputs)

    st.markdown("---")
    st.subheader("Step 2 – Select Contract Length and Annual Consumption")

    contract_length = st.selectbox("Contract Length (Years)", [1, 2, 3])
    annual_consumption = st.number_input("Annual Consumption (kWh)", min_value=1, value=20000, step=500)
    days_per_year = 365

    st.markdown(f"""
    <div style="background-color: {BRAND_PRIMARY_COLOR}; padding: 1rem; border-radius: 8px; color: white;">
        <b>Settings Summary:</b><br>
        • Contract Length: {contract_length} year(s)<br>
        • Annual Consumption: {annual_consumption} kWh
    </div>
    """, unsafe_allow_html=True)

    # Helper function
    def get_band_uplifts(consumption):
        for b in band_inputs:
            if b["Min"] <= consumption <= b["Max"]:
                return {
                    "unit": b[f"Unit_{contract_length}"],
                    "stand": b[f"Stand_{contract_length}"]
                }
        return {"unit": 0.0, "stand": 0.0}

    # Apply uplifts
    uplifts = df.apply(
        lambda row: get_band_uplifts((row["MinimumAnnualConsumption"] + row["MaximumAnnualConsumption"]) / 2),
        axis=1
    )

    df["Unit_Uplift_p"] = [u["unit"] for u in uplifts]
    df["Standing_Uplift_p"] = [u["stand"] for u in uplifts]

    df["UnitRate_Uplifted"] = (df["UnitRate"] + df["Unit_Uplift_p"]).round(3)
    df["StandingCharge_Uplifted"] = (df["StandingCharge"] + df["Standing_Uplift_p"]).round(3)

    df["EstimatedAnnualCost_Original"] = (
        (df["StandingCharge"] * days_per_year) +
        (df["UnitRate"] * annual_consumption)
    ) / 100

    df["EstimatedAnnualCost_Uplifted"] = (
        (df["StandingCharge_Uplifted"] * days_per_year) +
        (df["UnitRate_Uplifted"] * annual_consumption)
    ) / 100

    st.subheader("✅ Preview of Uplifted Data")
    st.dataframe(df.head())

    output = io.BytesIO()
    df.to_csv(output, index=False)

    st.download_button(
        label="⬇️ Download Uplifted CSV",
        data=output.getvalue(),
        file_name="uplifted_output_by_contract.csv",
        mime="text/csv"
    )

# ====== Footer Branding ======
st.markdown(
    f"""
    <hr>
    <div style="text-align: center; color: grey; font-size: 0.9em;">
        {FOOTER}
    </div>
    """,
    unsafe_allow_html=True
)
