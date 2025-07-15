import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Direct Sales LLF Multi-tool", layout="wide")
st.title("Direct Sales LLF Multi-tool")

# --- Hardcoded LLF Mapping Table ---
llf_mapping = pd.DataFrame({
    "DNO": ["10", "10", "10", "10"],
    "LLF": ["199", "202", "70", "80"],
    "Band": ["NDA Band 1", "NDA Band 2", "LV Band 1", "LV Sub Band 1"]
})

# --- File Upload ---
uploaded_file = st.file_uploader("Upload Electricity Flat File (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Quote Details")
    customer_name = st.text_input("Customer Name")
    contract_duration = st.selectbox("Contract Duration (months)", options=[12, 24, 36])
    green_energy = st.radio("Green Energy", ["False", "True"])

    output_filename = st.text_input("Output file name (without .xlsx)", value="llf_multi_site_quote")

    st.subheader("Multi-site Input")
    input_rows = []

    for i in range(10):
        st.markdown(f"### Site {i+1}")
        cols = st.columns([1.2, 1.2, 1, 1, 1, 1, 1, 1.5])

        site = cols[0].text_input("Site Name", key=f"site_{i}")
        dno_id = cols[1].text_input("DNO ID", key=f"dno_{i}")
        llf_code = cols[2].text_input("LLF Code", key=f"llf_{i}")
        kwh = cols[3].number_input("Annual Consumption (kWh)", min_value=0, value=0, step=1000, key=f"kwh_{i}")

        llf_band_row = llf_mapping[
            (llf_mapping["DNO"] == dno_id) &
            (llf_mapping["LLF"] == llf_code)
        ]

        llf_band = llf_band_row.iloc[0]["Band"] if not llf_band_row.empty else "Not Found"

        matched = df[
            (df["DNO_ID"].astype(str) == dno_id) &
            (df["LLF_Band"] == llf_band) &
            (df["Contract_Duration"] == contract_duration) &
            (df["Green_Energy"].astype(str).str.upper() == green_energy.upper()) &
            (df["Minimum_Annual_Consumption"] <= kwh) &
            (df["Maximum_Annual_Consumption"] >= kwh)
        ]

        if not matched.empty:
            price = matched.iloc[0]

            standing_charge = price.get("Standing_Charge", 0)
            standard_rate = price.get("Standard_Rate", 0)
            day_rate = price.get("Day_Rate", 0)
            night_rate = price.get("Night_Rate", 0)
            evening_weekend_rate = price.get("Evening_And_Weekend_Rate", 0)

            # Show cost prices
            cols[4].metric("Standing Charge (p/day)", f"{standing_charge:.3f}")
            cols[5].metric("Standard Rate (p/kWh)", f"{standard_rate:.3f}")

            uplift_sc = cols[6].number_input("Uplift SC (p/day)", min_value=0.0, value=0.0, step=0.1, key=f"uplift_sc_{i}")
            uplift_standard = cols[7].number_input("Uplift Std Rate (p/kWh)", min_value=0.0, value=0.0, step=0.01, key=f"uplift_standard_{i}")

            final_sc = standing_charge + uplift_sc
            final_standard = standard_rate + uplift_standard

            total_cost = round((final_standard * kwh + final_sc * 365) / 100, 2) if kwh > 0 else 0

            input_rows.append({
                "Customer": customer_name,
                "Site": site,
                "DNO ID": dno_id,
                "LLF Code": llf_code,
                "LLF Band": llf_band,
                "Annual Consumption (kWh)": kwh,
                "Standing Charge (p/day)": standing_charge,
                "Standard Rate (p/kWh)": standard_rate,
                "Uplift SC (p/day)": uplift_sc,
                "Uplift Standard Rate (p/kWh)": uplift_standard,
                "Final Standing Charge (p/day)": final_sc,
                "Final Standard Rate (p/kWh)": final_standard,
                "Total Annual Cost (£)": total_cost
            })

        else:
            st.warning(f"No matching price found for Site {i+1}.")

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
    st.info("Please upload the electricity flat file to begin.")
