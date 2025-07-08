import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool")

# --- Load postcode-to-LDZ mapping ---
LDZ_DATA_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/postcode_ldz.csv"

@st.cache_data

def load_ldz_data():
    return pd.read_csv(LDZ_DATA_URL)

ldz_df = load_ldz_data()
ldz_df["Postcode"] = ldz_df["Postcode"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)

# --- Upload Supplier File ---
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["LDZ"] = df["LDZ"].astype(str).str.upper().str.strip()
    df["Exit_Zone"] = df["Exit_Zone"].astype(str).str.upper().str.strip()

    st.subheader("Quote Details")
    customer_name = st.text_input("Customer Name")
    contract_filter = st.selectbox("Contract Duration (years)", options=[1, 2, 3])
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    st.subheader("Multi-site Input")

    # --- Input table ---
    input_rows = []
    for i in range(10):
        cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
        site = cols[0].text_input(f"Site {i+1}", key=f"site_{i}")
        postcode = cols[1].text_input("Postcode", key=f"postcode_{i}").replace(" ", "").upper()
        kwh = cols[2].number_input("kWh", min_value=0, value=0, step=1000, key=f"kwh_{i}")

        if postcode and kwh > 0:
            match = ldz_df[ldz_df["Postcode"] == postcode]
            if not match.empty:
                ldz = match.iloc[0]["LDZ"]
                exit_zone = match.iloc[0]["Exit Zone"]

                tariffs = df[
                    (df["LDZ"] == ldz) &
                    (df["Exit_Zone"] == exit_zone) &
                    (df["Minimum_Annual_Consumption"] <= kwh) &
                    (df["Maximum_Annual_Consumption"] >= kwh) &
                    (df["Contract_Duration"] == contract_filter)
                ]

                if not tariffs.empty:
                    cost_unit = tariffs.iloc[0]["Unit_Rate"]
                    cost_sc = tariffs.iloc[0]["Standing_Charge"]
                    uplift_unit = cols[5].number_input("Uplift Unit", min_value=0.0, value=0.0, step=0.01, key=f"uplift_unit_{i}")
                    uplift_sc = cols[6].number_input("Uplift SC", min_value=0.0, value=0.0, step=0.1, key=f"uplift_sc_{i}")
                    final_unit = cost_unit + uplift_unit
                    final_sc = cost_sc + uplift_sc
                    total_cost = round((final_unit * kwh + final_sc * 365) / 100, 2)
                else:
                    cost_unit = cost_sc = final_unit = final_sc = total_cost = "No Match"
                    uplift_unit = uplift_sc = 0
                    tariffs = pd.DataFrame()
            else:
                ldz = exit_zone = "Not found"
                cost_unit = cost_sc = final_unit = final_sc = total_cost = "Postcode not found"
                uplift_unit = uplift_sc = 0
                tariffs = pd.DataFrame()

            input_rows.append({
                "Customer": customer_name,
                "Site": site,
                "Postcode": postcode,
                "Annual Consumption (kWh)": kwh,
                "LDZ": ldz,
                "Exit Zone": exit_zone,
                "Cost Unit Rate (p/kWh)": cost_unit,
                "Cost SC (p/day)": cost_sc,
                "Uplift Unit Rate (p/kWh)": uplift_unit,
                "Uplift SC (p/day)": uplift_sc,
                "Final Unit Rate (p/kWh)": final_unit,
                "Final SC (p/day)": final_sc,
                "Total Annual Cost (£)": total_cost
            })

    if input_rows:
        st.subheader("Quote Results")
        results_df = pd.DataFrame(input_rows)
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
