import streamlit as st
import pandas as pd
import io
from PIL import Image

# ----------------------------------------
# PAGE CONFIG
# ----------------------------------------
st.set_page_config(page_title="Gas Direct Final", layout="wide")
st.title("Gas Multi-site Quote Builder (Final Version)")

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
# POSTCODE MATCHING
# ----------------------------------------
def match_postcode_to_ldz(postcode, ldz_df):
    postcode = postcode.replace(" ", "").upper()
    for length in [7, 6, 5, 4, 3]:
        match = ldz_df[ldz_df["Postcode"].str.startswith(postcode[:length])]
        if not match.empty:
            return match.iloc[0]["LDZ"]
    return ""

# ----------------------------------------
# MAIN APP
# ----------------------------------------
ldz_df = load_ldz_data()
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    flat_df = load_flat_file(uploaded_file)

    st.subheader("Customer & Quote Details")
    customer_name = st.text_input("Customer Name")
    product_type = st.selectbox("Product Type", options=["Standard Gas", "Carbon Off"])
    carbon_offset_required = True if product_type == "Carbon Off" else False
    output_filename = st.text_input("Output file name (without .xlsx)", value="dyce_quote")

    # Logo placed just above the input grid
    try:
        logo = Image.open("DYCE-DARK BG.png")
        st.image(logo, width=120)
    except:
        st.warning("Logo not found – please ensure 'DYCE-DARK BG.png' is in the app directory.")

    st.subheader("Multi-site Input")
    input_rows = []

    for i in range(10):
        st.markdown(f"### Site {i+1}")
        with st.container():
            cols = st.columns([1.2, 1.2, 1] + [1]*3*3)  # Base + (3 fields * 3 durations)

            site = cols[0].text_input("Site Name", key=f"site_{i}")
            postcode_input = cols[1].text_input("Post Code", key=f"postcode_{i}")
            kwh = cols[2].number_input("Annual KWH", min_value=0, value=0, step=1000, key=f"kwh_{i}")
            ldz = match_postcode_to_ldz(postcode_input, ldz_df)

            row_data = {
                "Site Name": site,
                "Post Code": postcode_input,
                "Annual KWH": kwh
            }

            for idx, duration in enumerate([12, 24, 36]):
                match = flat_df[
                    (flat_df["LDZ"] == ldz) &
                    (flat_df["Contract_Duration"] == duration) &
                    (flat_df["Minimum_Annual_Consumption"] <= kwh) &
                    (flat_df["Maximum_Annual_Consumption"] >= kwh) &
                    (flat_df["Carbon_Offset"] == carbon_offset_required)
                ]

                if not match.empty:
                    tariff = match.sort_values("Unit_Rate").iloc[0]
                    base_unit = tariff["Unit_Rate"]
                    base_sc = tariff["Standing_Charge"]
                else:
                    base_unit = 0.0
                    base_sc = 0.0

                uplift_unit = cols[3 + idx*3 + 0].number_input(f"Uplift Unit Rate ({duration}m) (p)",
                                                             min_value=0.0, max_value=3.000, step=0.001,
                                                             key=f"uplift_unit_{i}_{duration}")
                uplift_sc = cols[3 + idx*3 + 1].number_input(f"Uplift SC ({duration}m) (p)",
                                                           min_value=0.0, max_value=100.0, step=0.1,
                                                           key=f"uplift_sc_{i}_{duration}")

                sell_unit = base_unit + uplift_unit
                sell_sc = base_sc + uplift_sc
                tac = round((sell_unit * kwh + sell_sc * 365) / 100, 2) if kwh > 0 else 0

                row_data[f"Sell Standing Charge ({duration}m)"] = round(sell_sc, 2)
                row_data[f"Sell Unit Rate ({duration}m)"] = round(sell_unit, 3)
                row_data[f"TAC £({duration}m)"] = tac

            input_rows.append(row_data)

    if input_rows:
        results_df = pd.DataFrame(input_rows)

        st.subheader("Preview: Customer-Facing Output")
        st.dataframe(results_df, use_container_width=True, height=400)

        st.subheader("Summary")
        st.metric("Total TAC (All Sites)", f"£{results_df[[col for col in results_df.columns if 'TAC' in col]].sum().sum():,.2f}")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            results_df.to_excel(writer, index=False, sheet_name="Customer Quote")
        output.seek(0)

        st.download_button(
            label="📥 Download Quote as Excel",
            data=output,
            file_name=f"{output_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload the supplier flat file to begin.")
