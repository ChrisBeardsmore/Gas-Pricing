import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool")

# --- Load postcode-to-LDZ mapping ---
LDZ_DATA_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/postcode_ldz_full.csv"

@st.cache_data
def load_ldz_data():
    df = pd.read_csv(LDZ_DATA_URL)
    df["Postcode"] = df["Postcode"].astype(str).str.upper().str.replace(r"\s+", "", regex=True)
    return df

ldz_df = load_ldz_data()

# --- Upload Supplier Flat File ---
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["LDZ"] = df["LDZ"].astype(str).str.strip().str.upper()
    df["Exit_Zone"] = df["Exit_Zone"].astype(str).str.strip().str.upper()
    df["Contract_Duration"] = pd.to_numeric(df["Contract_Duration"], errors='coerce').fillna(0).astype(int)
    df["Minimum_Annual_Consumption"] = pd.to_numeric(df["Minimum_Annual_Consumption"], errors='coerce').fillna(0)
    df["Maximum_Annual_Consumption"] = pd.to_numeric(df["Maximum_Annual_Consumption"], errors='coerce').fillna(0)

    st.subheader("Quote Details")
    customer_name = st.text_input("Customer Name")
    contract_duration = st.selectbox("Contract Duration (months)", options=[12, 24, 36])
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    st.subheader("Multi-site Input")
    input_rows = []

    for i in range(10):
        st.markdown(f"### Site {i+1}")
        cols = st.columns([1.2, 1.2, 1, 1, 1, 1, 1, 1, 1, 1.5])

        site = cols[0].text_input("Site Name", key=f"site_{i}")
        postcode_input = cols[1].text_input("Postcode", key=f"postcode_{i}")
        postcode = postcode_input.replace(" ", "").upper()
        kwh = cols[2].number_input("Annual Consumption (kWh)", min_value=0, value=0, step=1000, key=f"kwh_{i}")

        ldz = exit_zone = ""
        unit_rate = standing_charge = 0
        debug_info = ""

        if postcode:
            match = ldz_df[ldz_df["Postcode"] == postcode]
            if match.empty and len(postcode) >= 5:
                match = ldz_df[ldz_df["Postcode"].str.startswith(postcode[:5])]

            if not match.empty:
                ldz = match.iloc[0]["LDZ"]
                exit_zone = match.iloc[0]["Exit Zone"]

                debug_info += f"Matched Postcode {postcode} → LDZ: {ldz}, Exit Zone: {exit_zone}\n"
                st.write("DEBUG - LDZ:", ldz, "Exit Zone:", exit_zone)

                tariffs = df[
                    (df["LDZ"] == ldz) &
                    (df["Exit_Zone"] == exit_zone) &
                    (df["Contract_Duration"] == contract_duration) &
                    (df["Minimum_Annual_Consumption"] <= kwh) &
                    (df["Maximum_Annual_Consumption"] >= kwh)
                ]

                st.write("DEBUG - Tariffs found:", tariffs)

                if not tariffs.empty:
                    tariff = tariffs.iloc[0]
                    unit_rate = tariff["Unit_Rate"]
                    standing_charge = tariff["Standing_Charge"]
                    debug_info += f"Unit Rate: {unit_rate}, Standing Charge: {standing_charge}\n"
                else:
                    debug_info += "No matching tariff for consumption and contract duration.\n"
            else:
                debug_info += "No LDZ mapping found for postcode.\n"

        cols[3].metric("Unit Rate (p/kWh)", f"{unit_rate:.3f}")
        cols[4].metric("Standing Charge (p/day)", f"{standing_charge:.3f}")

        uplift_unit = cols[5].number_input("Uplift Unit (p/kWh)", min_value=0.0, value=0.0, step=0.01, key=f"uplift_unit_{i}")
        uplift_sc = cols[6].number_input("Uplift SC (p/day)", min_value=0.0, value=0.0, step=0.1, key=f"uplift_sc_{i}")

        final_unit = unit_rate + uplift_unit
        final_sc = standing_charge + uplift_sc
        total_cost = round((final_unit * kwh + final_sc * 365) / 100, 2) if kwh > 0 else 0

        cols[7].metric("Total £/year", f"£{total_cost:.2f}")

        if debug_info:
            st.text_area("Debug Info", debug_info, height=100)

        input_rows.append({
            "Customer": customer_name,
            "Site": site,
            "Postcode": postcode_input,
            "Annual Consumption (kWh)": kwh,
            "LDZ": ldz,
            "Exit Zone": exit_zone,
            "Unit Rate (p/kWh)": unit_rate,
            "Standing Charge (p/day)": standing_charge,
            "Uplift Unit Rate (p/kWh)": uplift_unit,
            "Uplift Standing Charge (p/day)": uplift_sc,
            "Final Unit Rate (p/kWh)": final_unit,
            "Final Standing Charge (p/day)": final_sc,
            "Total Annual Cost (£)": total_cost
        })

    if input_rows:
        st.subheader("Download Results")
        results_df = pd.DataFrame(input_rows)

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









Ask ChatGPT

