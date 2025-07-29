
# Gas Direct Final 5 – Confirmed Logic Build
# ---------------------------------------------------------------------------------
# ✅ Unified input grid using st.data_editor
# ✅ Editable fields: Site Name, Post Code, Annual KWH, SC Uplift, Unit Uplift
# ✅ SC uplift max = 100p/day | Unit Uplift max = 3.000p/kWh (to 3dp)
# ✅ Pulls base prices from supplier file by LDZ + Duration + Band + Carbon
# ✅ Calculates final Sell prices, TAC, Dyce Margin
# ✅ Output = customer-facing: Sell SC, Sell Unit, TAC only (no uplift/margin)
# ✅ Summary total TAC
# ✅ Download to Excel (clean export)
# ---------------------------------------------------------------------------------

import streamlit as st
import pandas as pd
import io
from PIL import Image

st.set_page_config(page_title="Gas Direct Final", layout="wide")
st.title("Gas Multi-site Quote Builder (Final Version)")

# Load LDZ and Supplier File
@st.cache_data
def load_ldz_data():
    url = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/postcode_ldz_full.csv"
    df = pd.read_csv(url)
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

# Load Data
ldz_df = load_ldz_data()
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    flat_df = load_flat_file(uploaded_file)

    st.subheader("Customer & Quote Details")
    customer_name = st.text_input("Customer Name")
    product_type = st.selectbox("Product Type", ["Standard Gas", "Carbon Off"])
    carbon_offset_required = (product_type == "Carbon Off")
    output_filename = st.text_input("Output file name (no .xlsx)", value="dyce_quote")

    try:
        logo = Image.open("DYCE-DARK BG.png")
        st.image(logo, width=120)
    except:
        st.warning("Logo not found – please upload 'DYCE-DARK BG.png'.")

    st.markdown("### Multi-site Input Grid (All values in pence)")
    st.caption("SC Uplift max = 100p/day | Unit Rate Uplift max = 3.000p/kWh")

    durations = [12, 24, 36]
    base_cols = ["Site Name", "Post Code", "Annual KWH"]
    dynamic_cols = [
        f"Standing charge ({d}m)" for d in durations
    ] + [
        f"Unit Rate ({d}m)" for d in durations
    ] + [
        f"Standing Charge Uplift ({d}m)" for d in durations
    ] + [
        f"Uplift unit rate ({d}m)" for d in durations
    ] + [
        f"Sell Standing Charge ({d}m)" for d in durations
    ] + [
        f"Sell Unit Rate ({d}m)" for d in durations
    ] + [
        f"TAC £({d}m)" for d in durations
    ] + [
        f"Dyce Margin ({d}m)" for d in durations
    ]

    full_columns = base_cols + dynamic_cols
    editable = base_cols + [f"Standing Charge Uplift ({d}m)" for d in durations] + [f"Uplift unit rate ({d}m)" for d in durations]
    initial_data = pd.DataFrame([{col: 0 if "KWH" in col or "Uplift" in col else "" for col in full_columns} for _ in range(10)])

    edited = st.data_editor(
        initial_data,
        use_container_width=True,
        num_rows="fixed",
        hide_index=True,
        disabled=[col for col in full_columns if col not in editable],
        key="grid_final"
    )

    results = []
    for _, row in edited.iterrows():
        site = row["Site Name"]
        postcode = row["Post Code"]
        kwh = row["Annual KWH"]
        if not postcode or kwh <= 0:
            continue

        ldz = match_postcode_to_ldz(postcode, ldz_df)
        result = {"Site Name": site, "Post Code": postcode, "Annual KWH": kwh}

        for dur in durations:
            uplift_sc = min(float(row.get(f"Standing Charge Uplift ({dur}m)", 0)), 100.0)
            uplift_unit = min(float(row.get(f"Uplift unit rate ({dur}m)", 0)), 3.000)

            match = flat_df[
                (flat_df["LDZ"] == ldz) &
                (flat_df["Contract_Duration"] == dur) &
                (flat_df["Minimum_Annual_Consumption"] <= kwh) &
                (flat_df["Maximum_Annual_Consumption"] >= kwh) &
                (flat_df["Carbon_Offset"] == carbon_offset_required)
            ]

            if not match.empty:
                base = match.sort_values("Unit_Rate").iloc[0]
                base_unit = base["Unit_Rate"]
                base_sc = base["Standing_Charge"]
            else:
                base_unit = base_sc = 0.0

            sell_unit = base_unit + uplift_unit
            sell_sc = base_sc + uplift_sc

            base_tac = round((base_unit * kwh + base_sc * 365) / 100, 2)
            final_tac = round((sell_unit * kwh + sell_sc * 365) / 100, 2)
            margin = round(final_tac - base_tac, 2)

            result[f"Standing charge ({dur}m)"] = round(base_sc, 2)
            result[f"Unit Rate ({dur}m)"] = round(base_unit, 3)
            result[f"Standing Charge Uplift ({dur}m)"] = round(uplift_sc, 2)
            result[f"Uplift unit rate ({dur}m)"] = round(uplift_unit, 3)
            result[f"Sell Standing Charge ({dur}m)"] = round(sell_sc, 2)
            result[f"Sell Unit Rate ({dur}m)"] = round(sell_unit, 3)
            result[f"TAC £({dur}m)"] = final_tac
            result[f"Dyce Margin ({dur}m)"] = margin

        results.append(result)

    if results:
        df = pd.DataFrame(results)
        st.subheader("Customer-Facing Output")
        export_cols = ["Site Name", "Post Code", "Annual KWH"] +                       [f"Sell Standing Charge ({d}m)" for d in durations] +                       [f"Sell Unit Rate ({d}m)" for d in durations] +                       [f"TAC £({d}m)" for d in durations]
        export_df = df[export_cols]
        st.dataframe(export_df, use_container_width=True)

        st.subheader("Summary")
        tac_total = export_df[[col for col in export_df.columns if "TAC" in col]].sum().sum()
        st.metric("Total TAC (£)", f"£{tac_total:,.2f}")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            export_df.to_excel(writer, index=False, sheet_name="Customer Quote")
        output.seek(0)

        st.download_button(
            label="📥 Download Customer Quote",
            data=output,
            file_name=f"{output_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload the supplier flat file to begin.")
