# Gas Direct Final V5.1
# ----------------------------------------------------------
# Streamlit App for Multi-Site Gas Pricing (Final Version)
# - Uses unified input grid with 21 columns (from gasinputs.xlsx)
# - Pre-fills Standing Charges & Unit Rates from flat file
# - User sets uplifts in pence (with cap validation)
# - Customer-facing output (no margins/uplifts shown)
# - Logo top-right, summary totals
# ----------------------------------------------------------

import streamlit as st
import pandas as pd
import io
from PIL import Image

st.set_page_config(page_title="Gas Direct Final", layout="wide")
st.title("Gas Multi-site Quote Builder (Final V5.1)")

@st.cache_data
def load_ldz_data():
    url = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/postcode_ldz_full.csv"
    df = pd.read_csv(url)
    df["Postcode"] = df["Postcode"].astype(str).str.upper().str.replace(r"\\s+", "", regex=True)
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

    st.subheader("Customer & Quote Details")
    customer_name = st.text_input("Customer Name")
    product_type = st.selectbox("Product Type", options=["Standard Gas", "Carbon Off"])
    carbon_offset_required = (product_type == "Carbon Off")
    output_filename = st.text_input("Output file name (no .xlsx)", value="dyce_quote")

    # Top-right logo
    with st.container():
        col1, col2 = st.columns([9, 1])
        with col2:
            try:
                logo = Image.open("DYCE-DARK BG.png")
                st.image(logo, width=120)
            except:
                st.warning("Logo not found")

    st.subheader("Unified Input Grid")
    st.caption("Note: SC uplift cap = 100p/day, Unit cap = 3.000p/kWh")

    durations = [12, 24, 36]
    base_cols = ["Site Name", "Post Code", "Annual KWH"]
    uplift_cols = [
        f"Standing Charge Uplift ({d}m)" for d in durations
    ] + [
        f"Uplift unit rate ({d}m)" for d in durations
    ]

    display_cols = []
    for d in durations:
        display_cols += [
            f"Standing charge ({d}m)", f"Unit Rate ({d}m)",
            f"Standing Charge Uplift ({d}m)", f"Uplift unit rate ({d}m)",
            f"TAC £({d}m)", f"Dyce Margin ({d}m)"
        ]

    all_cols = base_cols + display_cols
    editable_cols = base_cols + uplift_cols

    initial_data = pd.DataFrame([{col: "" if col in ["Site Name", "Post Code"] else 0 for col in all_cols} for _ in range(10)])

    # Pre-fill standing charges and unit rates
    for idx in range(len(initial_data)):
        row = initial_data.loc[idx]
        postcode = str(row["Post Code"])
        kwh = row["Annual KWH"]
        ldz = match_postcode_to_ldz(postcode, ldz_df)

        for duration in durations:
            match = flat_df[
                (flat_df["LDZ"] == ldz) &
                (flat_df["Contract_Duration"] == duration) &
                (flat_df["Carbon_Offset"] == carbon_offset_required)
            ]
            if not match.empty:
                tariff = match.iloc[0]
                initial_data.at[idx, f"Standing charge ({duration}m)"] = round(tariff["Standing_Charge"], 2)
                initial_data.at[idx, f"Unit Rate ({duration}m)"] = round(tariff["Unit_Rate"], 3)

    edited = st.data_editor(
        initial_data,
        use_container_width=True,
        hide_index=True,
        disabled=[col for col in all_cols if col not in editable_cols]
    )

    # Calculate outputs
    output_rows = []
    for _, row in edited.iterrows():
        site = row["Site Name"]
        postcode = row["Post Code"]
        kwh = row["Annual KWH"]
        if not postcode or kwh <= 0:
            continue

        ldz = match_postcode_to_ldz(postcode, ldz_df)
        result = {"Site Name": site, "Post Code": postcode, "Annual KWH": kwh}

        for duration in durations:
            base_sc = float(row.get(f"Standing charge ({duration}m)", 0))
            base_unit = float(row.get(f"Unit Rate ({duration}m)", 0))
            uplift_sc = min(float(row.get(f"Standing Charge Uplift ({duration}m)", 0)), 100.0)
            uplift_unit = min(float(row.get(f"Uplift unit rate ({duration}m)", 0)), 3.000)

            sell_sc = base_sc + uplift_sc
            sell_unit = base_unit + uplift_unit

            base_tac = (base_unit * kwh + base_sc * 365) / 100
            final_tac = (sell_unit * kwh + sell_sc * 365) / 100
            margin = final_tac - base_tac

            result[f"Sell Standing Charge ({duration}m)"] = round(sell_sc, 2)
            result[f"Sell Unit Rate ({duration}m)"] = round(sell_unit, 3)
            result[f"TAC £({duration}m)"] = round(final_tac, 2)
            result[f"Dyce Margin ({duration}m)"] = round(margin, 2)

        output_rows.append(result)

    if output_rows:
        st.subheader("Customer-Facing Output")
        display = pd.DataFrame(output_rows)
        sell_cols = [col for col in display.columns if "Sell" in col or "TAC" in col or col in base_cols]
        st.dataframe(display[sell_cols], use_container_width=True)

        st.subheader("Summary Totals")
        summary = {
            f"Total TAC £({d}m)": display[f"TAC £({d}m)"].sum().round(2) for d in durations
        }
        st.write(pd.DataFrame([summary]))

        # Download
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            export_df = display[sell_cols]
            export_df.to_excel(writer, index=False, sheet_name="Quote")
        output.seek(0)

        st.download_button(
            label="Download Quote as Excel",
            data=output,
            file_name=f"{output_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload the supplier flat file to begin.")
