import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool")

# --- Load postcode-to-LDZ mapping from GitHub ---
LDZ_DATA_URL = "https://raw.githubusercontent.com/yourusername/yourrepo/main/data/postcode_ldz.csv.gz"

@st.cache_data
def load_ldz_data():
    return pd.read_csv(LDZ_DATA_URL, compression="gzip")

ldz_df = load_ldz_data()

# --- Upload supplier flat file ---
uploaded_file = st.file_uploader("Upload Supplier Flat File (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # --- Customer and Contract Info ---
    st.subheader("📋 Customer Details & Quote Options")
    customer_name = st.text_input("Customer Name")
    contract_filter = st.selectbox("Contract Duration (years)", options=[1, 2, 3], index=0)
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    # --- Meter Entry Section ---
    st.subheader("🔢 Multi-site Input (up to 10 meters)")
    initial_data = pd.DataFrame({
        "Site": [f"Site {i+1}" for i in range(10)],
        "Postcode": ["" for _ in range(10)],
        "Annual Consumption (kWh)": [0 for _ in range(10)],
    })
    site_inputs = st.data_editor(
        initial_data,
        use_container_width=True,
        key="multi_meter_input",
        num_rows="fixed"
    )

    # --- Uplift Input ---
    st.subheader("💰 Profit Uplift Settings")
    uplift_unit = st.number_input("Uplift to Unit Rate (p/kWh)", min_value=0.0, value=0.0, step=0.01)
    uplift_sc = st.number_input("Uplift to Standing Charge (p/day)", min_value=0.0, value=0.0, step=0.1)

    # --- Normalize for merge ---
    ldz_df["Postcode"] = ldz_df["Postcode"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)
    df["LDZ"] = df["LDZ"].astype(str).str.upper().str.strip()
    df["Exit_Zone"] = df["Exit_Zone"].astype(str).str.upper().str.strip()

    # --- Quoting Logic ---
    results = []

    for _, row in site_inputs.iterrows():
        postcode = str(row["Postcode"]).replace(" ", "").upper()
        kwh = row["Annual Consumption (kWh)"]

        if postcode and kwh > 0:
            match = ldz_df[ldz_df["Postcode"] == postcode]
            if not match.empty:
                ldz = match.iloc[0]["LDZ"]
                exit_zone = match.iloc[0]["Exit Zone"]

                matching_tariffs = df[
                    (df["LDZ"] == ldz) &
                    (df["Exit_Zone"] == exit_zone) &
                    (df["Minimum_Annual_Consumption"] <= kwh) &
                    (df["Maximum_Annual_Consumption"] >= kwh) &
                    (df["Contract_Duration"] == contract_filter)
                ]

                for _, t in matching_tariffs.iterrows():
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
                        "Total Annual Cost (£)": round(total_cost / 100, 2)  # pence to pounds
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

    # --- Display and Export Results ---
    if results:
        results_df = pd.DataFrame(results)
        st.subheader("📊 Quoted Results")
        st.dataframe(results_df, use_container_width=True)

        # Excel export
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
    st.info("Please upload the supplier flat file to begin."
