# Gas Direct V3.9 (Add Base TAC & Margin per Duration)
# ---------------------------------------------------------------------------------
# Adds margin calculation as Final TAC - Base TAC for each duration
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

    st.subheader("Multi-site Input (Editable Grid)")

    initial_data = pd.DataFrame({
        "Site Name": ["" for _ in range(10)],
        "Postcode": ["" for _ in range(10)],
        "Annual kWh": [0 for _ in range(10)],
        "Uplift Unit (12m)": [0.0 for _ in range(10)],
        "Uplift SC (12m)": [0.0 for _ in range(10)],
        "Uplift Unit (24m)": [0.0 for _ in range(10)],
        "Uplift SC (24m)": [0.0 for _ in range(10)],
        "Uplift Unit (36m)": [0.0 for _ in range(10)],
        "Uplift SC (36m)": [0.0 for _ in range(10)],
    })

    edited_data = st.data_editor(
        initial_data,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        key="editable_site_inputs"
    )

    st.subheader("Calculated Results (with Margin)")
    results = []

    for _, row in edited_data.iterrows():
        site = row["Site Name"]
        postcode = row["Postcode"]
        kwh = row["Annual kWh"]
        if not postcode or kwh <= 0:
            continue

        ldz = match_postcode_to_ldz(postcode, ldz_df)
        result_row = {
            "Customer": customer_name,
            "Site": site,
            "Postcode": postcode,
            "LDZ": ldz,
            "Annual kWh": kwh
        }

        for duration in [12, 24, 36]:
            uplift_unit = row[f"Uplift Unit ({duration}m)"]
            uplift_sc = row[f"Uplift SC ({duration}m)"]

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
                unit_rate = 0.0
                standing_charge = 0.0

            final_unit = unit_rate + uplift_unit
            final_sc = standing_charge + uplift_sc
            base_tac = round((unit_rate * kwh + standing_charge * 365) / 100, 2)
            final_tac = round((final_unit * kwh + final_sc * 365) / 100, 2)
            margin = round(final_tac - base_tac, 2)

            result_row[f"Unit Rate ({duration}m)"] = unit_rate
            result_row[f"Standing Charge ({duration}m)"] = standing_charge
            result_row[f"Final Unit Rate ({duration}m)"] = final_unit
            result_row[f"Final SC ({duration}m)"] = final_sc
            result_row[f"Base TAC (£, {duration}m)"] = base_tac
            result_row[f"TAC (£, {duration}m)"] = final_tac
            result_row[f"Margin (£, {duration}m)"] = margin

        results.append(result_row)

    if results:
        results_df = pd.DataFrame(results)

        st.dataframe(results_df, use_container_width=True)

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
