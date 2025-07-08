import streamlit as st
import pandas as pd
import io

# ------------------ CONFIG ------------------
st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool")

# Link to postcode → LDZ mapping file on GitHub
LDZ_DATA_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/postcode_ldz.csv"

@st.cache_data
def load_ldz_data():
    return pd.read_csv(LDZ_DATA_URL)

ldz_df = load_ldz_data()

# ------------------ SUPPLIER FLAT FILE UPLOAD ------------------
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # ------------------ QUOTE SETUP ------------------
    st.subheader("📋 Customer & Quote Options")

    customer_name = st.text_input("Customer Name")
    contract_filter = st.selectbox("Contract Duration (years)", options=[1, 2, 3])
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    # ------------------ METER INPUT ------------------
    st.subheader("🔢 Multi-site Input (up to 10 meters)")
    input_df = pd.DataFrame({
        "Site": [f"Site {i+1}" for i in range(10)],
        "Postcode": ["" for _ in range(10)],
        "Annual Consumption (kWh)": [0 for _ in range(10)],
    })
    site_inputs = st.data_editor(input_df, use_container_width=True, num_rows="fixed", key="multi_meter_input")

    # ------------------ UPLIFT ENTRY ------------------
    st.subheader("💰 Profit Uplift Settings")
    uplift_unit = st.number_input("Uplift to Unit Rate (p/kWh)", min_value=0.0, value=0.0, step=0.01)
    uplift_sc = st.number_input("Uplift to Standing Charge (p/day)", min_value=0.0, value=0.0, step=0.1)

    # ------------------ NORMALISE FIELDS ------------------
    ldz_df["Postcode"] = ldz_df["Postcode"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)
    df["LDZ"] = df["LDZ"].astype(str).str.upper().str.strip()
    df["Exit_Zone"] = df["Exit_Zone"].astype(str).str.upper().str.strip()

    # ------------------ MAIN LOGIC ------------------
    results = []

    for _, row in site_inputs.iterrows():
        postcode = str(row["Postcode"]).replace(" ", "").upper()
        kwh = row["Annual Consumption (kWh)"]

        if postcode and kwh > 0:
            match = ldz_df[ldz_df["Postcode"] == postcode]

            if not match.empty:
                ldz = match.iloc[0]["LDZ"]
                exit_zone = match.iloc[0]["Exit Zone"]

                matches = df[
                    (df["LDZ"] == ldz) &
                    (df["Exit_Zone"] == exit_zone) &
                    (df["Minimum_Annual_Consumption"] <= kwh) &
                    (df["Maximum_Annual_Consumption"] >= kwh) &
                    (df["Contract_Duration"] == contract_filter)
                ]

                for _, t in matches.iterrows():
                    total_cost = (t["Unit_Rate"] + uplift_unit) * kwh + (t["Standing_Charge"] + uplift_sc) * 365
                    results.append({
                        "Customer": customer_name,
                        "Site": row["Site"],
                        "Postcode": postcode,
                        "LDZ": ldz,
                        "Exit Zone": exit_zone,
                        "Contract Duration": t["Contract_Duration"],
                        "Product Name": t["Product_Name"],
                        "Final Unit Rate (p/kWh)": round(t["Unit_Rate"] + uplift_unit, 4),
                        "Final Standing Charge (p/day)": round(t["Standing_Charge"] + uplift_sc, 4),
                        "Total Annual Cost (£)": round(total_cost / 100, 2)
                    })
            else:
                results.append({
                    "Customer": customer_name,
                    "Site": row["Site"],
                    "Postcode": postcode,
                    "LDZ": "Not found",
                    "Exit Zone": "Not found",
                    "Contract Duration": contract_filter,
                    "Product Name": "",
                    "Final Unit Rate (p/kWh)": "",
                    "Final Standing Charge (p/day)": "",
                    "Total Annual Cost (£)": "Postcode not found"
                })

    # ------------------ OUTPUT ------------------
    if results:
        st.subheader("📊 Quoted Results")
        results_df = pd.DataFrame(results)
        st.dataframe(results_df, use_container_width=True)

        # Create Excel file
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            results_df.to_excel(writer, index=False, sheet_name="Quote")
        output.seek(0)

        st.download_button(
            label="📥 Download as Excel",
            data=output,
            file_name=f"{output_filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload the supplier flat file to begin.")
