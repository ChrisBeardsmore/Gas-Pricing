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

# --- Upload Supplier File ---
uploaded_file = st.file_uploader("Upload Supplier Flat File (XLSX)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df["LDZ"] = df["LDZ"].astype(str).str.upper().str.strip()
    df["Exit_Zone"] = df["Exit_Zone"].astype(str).str.upper().str.strip()
    df["Contract_Duration"] = pd.to_numeric(df["Contract_Duration"], errors="coerce")
    df["Minimum_Annual_Consumption"] = pd.to_numeric(df["Minimum_Annual_Consumption"], errors="coerce")
    df["Maximum_Annual_Consumption"] = pd.to_numeric(df["Maximum_Annual_Consumption"], errors="coerce")

    st.subheader("Quote Details")
    customer_name = st.text_input("Customer Name")
    contract_filter = st.selectbox("Contract Duration (years)", options=[1, 2, 3])
    output_filename = st.text_input("Output file name (without .xlsx)", value="multi_site_quote")

    st.subheader("Multi-site Input")
    input_rows = []

    for i in range(10):
        st.markdown(f"### Site {i+1}")
        cols = st.columns([1.2, 1.2, 1, 1, 1, 1, 1, 1, 1, 1.5])

        site = cols[0].text_input("Site Name", key=f"site_{i}")
        postcode_input = cols[1].text_input("Postcode", key=f"postcode_{i}")
        postcode = postcode_input.replace(" ", "").upper()
        cols[1].caption("(Upper case, no spaces)")
        kwh = cols[2].number_input("Annual kWh", min_value=0, value=0, step=1000, key=f"kwh_{i}")

        ldz = exit_zone = ""
        cost_unit = cost_sc = 0

        debug_info = ""
        debug_tariffs = pd.DataFrame()

        if postcode and kwh > 0:
            match = ldz_df[ldz_df["Postcode"] == postcode]
            if match.empty and len(postcode) >= 5:
                match = ldz_df[ldz_df["Postcode"].str.startswith(postcode[:5])]

            if not match.empty:
                ldz = match.iloc[0]["LDZ"]
                exit_zone = match.iloc[0]["Exit Zone"]
                debug_info += f"Postcode match: {postcode} → LDZ: {ldz}, Exit Zone: {exit_zone}\n"

                # Apply filtering with debug capture
                contract_months = contract_filter * 12
                tariffs = df[
                    (df["LDZ"] == ldz) &
                    (df["Exit_Zone"] == exit_zone) &
                    (df["Minimum_Annual_Consumption"] <= kwh) &
                    (df["Maximum_Annual_Consumption"] >= kwh) &
                    (df["Contract_Duration"] == contract_months)
                ]

                debug_info += f"Applied Filters:\nLDZ = {ldz}, Exit Zone = {exit_zone}, kWh = {kwh}, Contract = {contract_months} months\n"
                debug_info += f"Tariffs found: {len(tariffs)}\n"
                debug_tariffs = tariffs.copy()

                if not tariffs.empty:
                    best = tariffs.sort_values("Unit_Rate").iloc[0]
                    cost_unit = best["Unit_Rate"]
                    cost_sc = best["Standing_Charge"]
                else:
                    cols[3].warning("No price match found")
            else:
                cols[3].warning("Postcode not found")
                debug_info += "Postcode not found in mapping\n"

        uplift_unit = cols[5].number_input("Uplift Unit (p/kWh)", min_value=0.0, value=0.0, step=0.01, key=f"uplift_unit_{i}")
        uplift_sc = cols[6].number_input("Uplift SC (p/day)", min_value=0.0, value=0.0, step=0.1, key=f"uplift_sc_{i}")

        final_unit = cost_unit + uplift_unit
        final_sc = cost_sc + uplift_sc
        total_cost = round((final_unit * kwh + final_sc * 365) / 100, 2) if kwh > 0 else 0

        cols[3].metric("Cost Unit (p/kWh)", f"{cost_unit:.2f}")
        cols[4].metric("Cost SC (p/day)", f"{cost_sc:.2f}")
        cols[7].metric("Final Unit (p/kWh)", f"{final_unit:.2f}")
        cols[8].metric("Final SC (p/day)", f"{final_sc:.2f}")
        cols[9].metric("Total £/year", f"£{total_cost:.2f}")

        if debug_info:
            st.text_area("Debug Info", debug_info, height=100)
        if not debug_tariffs.empty:
            st.dataframe(debug_tariffs.head(), use_container_width=True)

        input_rows.append({
            "Customer": customer_name,
            "Site": site,
            "Postcode": postcode_input,
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
