import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Electricity LLF Grid Quoting Tool", layout="wide")
st.title("\ud83d\udd0c Electricity Grid-Style LLF Pricing Tool")

# --- Hardcoded LLF Mapping Table (expand as needed) ---
llf_mapping = pd.DataFrame({
    "DNO": ["10", "10", "10", "10"],
    "LLF": ["199", "202", "70", "80"],
    "Band": ["NDA Band 1", "NDA Band 2", "LV Band 1", "LV Sub Band 1"]
})

# --- File Upload ---
uploaded_file = st.file_uploader("Upload Electricity Flat File (.xlsx)", type=["xlsx"])

if uploaded_file:
    flat_file = pd.read_excel(uploaded_file)

    # --- Step 1: Grid Input ---
    st.subheader("Step 1: Enter Quote Inputs for Up to 10 Meters")
    default_data = pd.DataFrame({
        "DNO_ID": ["10"] * 10,
        "LLF_Code": ["199"] * 10,
        "Annual_Consumption": [2000] * 10,
        "Contract_Duration": [12] * 10,
        "Green_Energy": [False] * 10
    })

    edited_data = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

    if st.button("Generate Cost Prices"):
        results = []

        for _, row in edited_data.iterrows():
            dno = str(row["DNO_ID"])
            llf_code = str(row["LLF_Code"])
            consumption = row["Annual_Consumption"]
            duration = row["Contract_Duration"]
            green = row["Green_Energy"]

            # Map LLF to Band
            band_row = llf_mapping[
                (llf_mapping["DNO"].astype(str) == dno) &
                (llf_mapping["LLF"].astype(str) == llf_code)
            ]

            if band_row.empty:
                result = row.to_dict()
                result.update({"Error": "LLF Band Not Found"})
                results.append(result)
                continue

            llf_band = band_row.iloc[0]["Band"]

            # Filter flat file
            filtered = flat_file[
                (flat_file["DNO_ID"].astype(str) == dno) &
                (flat_file["LLF_Band"] == llf_band) &
                (flat_file["Contract_Duration"] == duration) &
                (flat_file["Green_Energy"].astype(str).str.upper() == str(green).upper()) &
                (flat_file["Minimum_Annual_Consumption"] <= consumption) &
                (flat_file["Maximum_Annual_Consumption"] >= consumption)
            ]

            if filtered.empty:
                result = row.to_dict()
                result.update({"Error": "No matching price found"})
                results.append(result)
                continue

            price = filtered.iloc[0]
            result = row.to_dict()
            result.update({
                "LLF_Band": llf_band,
                "Standing_Charge": price.get("Standing_Charge", 0),
                "Standard_Rate": price.get("Standard_Rate", 0),
                "Day_Rate": price.get("Day_Rate", 0),
                "Night_Rate": price.get("Night_Rate", 0),
                "Uplift_p/kWh": 0.0
            })
            results.append(result)

        results_df = pd.DataFrame(results)

        st.subheader("Step 2: Add Uplift to Each Quote")
        uplifted_df = st.data_editor(results_df, num_rows="fixed", use_container_width=True)

        for col in ["Standard_Rate", "Day_Rate", "Night_Rate"]:
            if col in uplifted_df.columns:
                uplifted_df[f"{col}_With_Uplift"] = uplifted_df[col] + uplifted_df["Uplift_p/kWh"]

        st.subheader("Step 3: Final Quoted Rates")
        st.dataframe(uplifted_df, use_container_width=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            uplifted_df.to_excel(writer, index=False, sheet_name="Quotes")
            writer.save()

        st.download_button(
            label="\ud83d\udcc5 Download Final Quotes as Excel",
            data=output.getvalue(),
            file_name="Electricity_Quote_Grid.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload your electricity flat file to begin.")
