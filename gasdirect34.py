# Gas Direct V3.4 (Input Scroll Fixed, Output Stable)
# ---------------------------------------------------------------------------------
# Streamlit App for Direct Sales: 12/24/36 Month Gas Pricing Quote Tool
#
# ✅ Features:
# - Multi-site pricing with postcode-to-LDZ mapping
# - Real-time cost lookup from uploaded supplier flat file
# - Uplift controls and TAC calculation across 3 contract durations (12/24/36m)
# - Export to Excel
# - Smooth performance via caching
# - Fully working horizontal scroll on input rows (per site)
# ---------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import io

# ----------------------------------------
# PAGE CONFIG
# ----------------------------------------
st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool (12/24/36 Month Quote Builder)")

# ----------------------------------------
# CACHED DATA LOADERS
# ----------------------------------------
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

# ----------------------------------------
# POSTCODE MATCHING FUNCTION (IMPROVED)
# ----------------------------------------
def match_postcode_to_ldz(postcode, ldz_df):
    postcode = postcode.replace(" ", "").upper()
    for length in [7, 6, 5, 4, 3]:
        match = ldz_df[ldz_df["Postcode"].str.startswith(postcode[:length])]
        if not match.empty:
            return match.iloc[0]["LDZ"]
    return ""

# ----------------------------------------
# MAIN APP LOGIC
# ----------------------------------------
ldz_df = load_ldz_data()
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    flat_df = load_flat_file(uploaded_file)

    st.subheader("Quote Setup")
    customer_name = st.text_input("Customer Name")
    product_type = st.selectbox("Product Type", options=["Standard Gas", "Carbon Off"])
    carbon_offset_required = True if product_type == "Carbon Off" else False
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    st.subheader("Multi-site Input")

    st.markdown("""
        <style>
        .scrollable-site-block {
            overflow-x: auto;
            white-space: nowrap;
            padding: 1rem 0;
            border-bottom: 1px solid #ccc;
        }
        .scrollable-site-block .block-column {
            display: inline-block;
            min-width: 220px;
            margin-right: 1rem;
            vertical-align: top;
        }
        </style>
    """, unsafe_allow_html=True)

    input_rows = []

    for i in range(10):
        st.markdown(f"### Site {i+1}")
        st.markdown('<div class="scrollable-site-block">', unsafe_allow_html=True)

        site = st.text_input("Site Name", key=f"site_{i}")
        postcode_input = st.text_input("Postcode", key=f"postcode_{i}")
        kwh = st.number_input("Annual Consumption (kWh)", min_value=0, value=0, step=1000, key=f"kwh_{i}")
        ldz = match_postcode_to_ldz(postcode_input, ldz_df)

        row_data = {
            "Customer": customer_name,
            "Site": site,
            "Postcode": postcode_input,
            "Annual Consumption (kWh)": kwh,
            "LDZ": ldz
        }

        for idx, duration in enumerate([12, 24, 36]):
            st.markdown(f'<div class="block-column">', unsafe_allow_html=True)

            uplift_unit = st.number_input(f"Uplift Unit ({duration}m)", min_value=0.0, value=0.0, step=0.01, key=f"uplift_unit_{i}_{duration}")
            uplift_sc = st.number_input(f"Uplift SC ({duration}m)", min_value=0.0, value=0.0, step=0.1, key=f"uplift_sc_{i}_{duration}")

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

            st.metric(f"Unit Rate ({duration}m)", f"{final_unit:.3f}")
            st.metric(f"SC ({duration}m)", f"{final_sc:.2f}")
            st.metric(f"TAC £ ({duration}m)", f"£{tac:.2f}")

            row_data[f"Unit Rate ({duration}m)"] = unit_rate
            row_data[f"Standing Charge ({duration}m)"] = standing_charge
            row_data[f"Uplift Unit Rate ({duration}m)"] = uplift_unit
            row_data[f"Uplift Standing Charge ({duration}m)"] = uplift_sc
            row_data[f"Final Unit Rate ({duration}m)"] = final_unit
            row_data[f"Final Standing Charge ({duration}m)"] = final_sc
            row_data[f"Total Annual Cost (£, {duration}m)"] = tac

            st.markdown('</div>', unsafe_allow_html=True)  # End block-column

        st.markdown('</div>', unsafe_allow_html=True)  # End scrollable-site-block

        input_rows.append(row_data)

    if input_rows:
        st.subheader("Download Results")
        results_df = pd.DataFrame(input_rows)

        st.markdown("""
        <style>
        .scrollable-table-wrapper {
            overflow-x: auto;
            padding-bottom: 1rem;
        }
        </style>
        <div class="scrollable-table-wrapper">
        """, unsafe_allow_html=True)

        st.dataframe(results_df, use_container_width=False)

        st.markdown("</div>", unsafe_allow_html=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            results_df.to_excel(writer, index=False, sheet_name="Quote")
        output.seek(0)

        st.download_button(
            label="Download Quote as Excel",
            data=output,
            file_name=f"{output_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload the supplier flat file to begin.")
