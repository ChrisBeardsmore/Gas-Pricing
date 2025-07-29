# Gas Direct V3.6 (Site 1 Rebuilt as Scrollable HTML Block)
# ---------------------------------------------------------------------------------
# Streamlit App for Direct Sales: 12/24/36 Month Gas Pricing Quote Tool
# Site 1 only is now rendered using raw HTML + CSS for true horizontal scrolling
# ---------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool (12/24/36 Month Quote Builder)")

@st.cache_data
def load_ldz_data():
    ldz_url = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/postcode_ldz_full.csv"
    df = pd.read_csv(ldz_url)
    df["Postcode"] = df["Postcode"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)
    return df

@st.cache_data
def load_flat_file(uploaded_file):
    df = pd.read_excel(uploaded_file)
    df["LDZ"] = df["LDZ"].astype(str).str.strip().str.upper()
    df["Contract_Duration"] = pd.to_numeric(df["Contract_Duration"], errors='coerce').fillna(0).astype(int)
    df["Minimum_Annual_Consumption"] = pd.to_numeric(df["Minimum_Annual_Consumption"], errors='coerce').fillna(0)
    df["Maximum_Annual_Consumption"] = pd.to_numeric(df["Maximum_Annual_Consumption"], errors='coerce').fillna(0)
    return df

def match_postcode_to_ldz(postcode, ldz_df):
    postcode = postcode.replace(" ", "").upper()
    for length in [7, 6, 5, 4, 3]:
        match = ldz_df[ldz_df["Postcode"].str.startswith(postcode[:length])]
        if not match.empty:
            return match.iloc[0]["LDZ"]
    return ""

ldz_df = load_ldz_data()
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    flat_df = load_flat_file(uploaded_file)

    st.subheader("Quote Setup")
    customer_name = st.text_input("Customer Name")
    product_type = st.selectbox("Product Type", options=["Standard Gas", "Carbon Off"])
    carbon_offset_required = True if product_type == "Carbon Off" else False
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    st.subheader("Site 1 (Scrollable Block)")

    st.markdown("""
    <style>
    .scroll-row {
        overflow-x: auto;
        white-space: nowrap;
        padding: 1rem;
        border: 1px solid #ccc;
        margin-bottom: 2rem;
    }
    .scroll-row > div {
        display: inline-block;
        vertical-align: top;
        margin-right: 1.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.form("site_1_form"):
        col1, col2, col3 = st.columns(3)
        site = col1.text_input("Site Name", key="site_1")
        postcode_input = col2.text_input("Postcode", key="postcode_1")
        kwh = col3.number_input("Annual Consumption (kWh)", min_value=0, value=0, step=1000, key="kwh_1")
        ldz = match_postcode_to_ldz(postcode_input, ldz_df)

        st.markdown('<div class="scroll-row">', unsafe_allow_html=True)

        uplift_inputs = {}
        tac_outputs = {}

        for duration in [12, 24, 36]:
            st.markdown(f"<div>", unsafe_allow_html=True)
            uplift_unit = st.number_input(f"Uplift Unit ({duration}m)", min_value=0.0, value=0.0, step=0.01, key=f"uplift_unit_{duration}")
            uplift_sc = st.number_input(f"Uplift SC ({duration}m)", min_value=0.0, value=0.0, step=0.1, key=f"uplift_sc_{duration}")

            match = flat_df[
                (flat_df["LDZ"] == ldz) &
                (flat_df["Contract_Duration"] == duration) &
                (flat_df["Minimum_Annual_Consumption"] <= kwh) &
                (flat_df["Maximum_Annual_Consumption"] >= kwh) &
                (flat_df["Carbon_Offset"] == carbon_offset_required)
            ]

            if not match.empty:
                tariff = match.sort_values("Unit_Rate").iloc[0]
                unit_rate = tariff["Unit_Rate"]
                standing_charge = tariff["Standing_Charge"]
            else:
                unit_rate = 0
                standing_charge = 0

            final_unit = unit_rate + uplift_unit
            final_sc = standing_charge + uplift_sc
            tac = round((final_unit * kwh + final_sc * 365) / 100, 2) if kwh > 0 else 0

            st.metric(f"Final Unit Rate ({duration}m)", f"{final_unit:.3f}")
            st.metric(f"Final SC ({duration}m)", f"{final_sc:.2f}")
            st.metric(f"TAC £ ({duration}m)", f"£{tac:.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

            uplift_inputs[duration] = (uplift_unit, uplift_sc)
            tac_outputs[duration] = tac

        st.markdown('</div>', unsafe_allow_html=True)

        submitted = st.form_submit_button("Apply Uplifts")

        if submitted:
            st.success("Uplift applied and TACs calculated!")
            st.write({"Site": site, "Postcode": postcode_input, "LDZ": ldz, "kWh": kwh})
            st.write(uplift_inputs)
            st.write(tac_outputs)
else:
    st.info("Please upload the supplier flat file to begin.")
