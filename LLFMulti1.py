import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Electricity LLF Pricing Tool", layout="wide")

st.title("🔌 Electricity LLF Pricing Tool with Uplift")

# --- Hardcoded LLF Mapping Table (sample - extend as needed) ---
llf_mapping = pd.DataFrame({
    "DNO": ["10", "10", "10", "10"],
    "LLF": ["199", "202", "70", "80"],
    "Band": ["NDA Band 1", "NDA Band 2", "LV Band 1", "LV Sub Band 1"]
})

# --- File Upload ---
uploaded_file = st.file_uploader("Upload Electricity Flat File (.xlsx)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # --- Sidebar Inputs ---
    st.sidebar.header("Quote Inputs")

    dno = st.sidebar.selectbox("DNO ID", sorted(df["DNO_ID"].dropna().unique()))
    llf_code = st.sidebar.text_input("LLF Code (e.g. 199, 202, X20)", value="")
    annual_consumption = st.sidebar.number_input("Annual Consumption (kWh)", min_value=0)
    contract_duration = st.sidebar.selectbox("Contract Duration (months)", sorted(df["Contract_Duration"].dropna().unique()))
    green_energy = st.sidebar.radio("Green Energy", ["False", "True"])
    uplift = st.sidebar.number_input("Uplift (p/kWh)", min_value=0.0, step=0.01)

    # --- Lookup LLF Band ---
    band_row = llf_mapping[
        (llf_mapping["DNO"].astype(str) == str(dno)) &
        (llf_mapping["LLF"].astype(str) == str(llf_code))
    ]

    if band_row.empty:
        st.error("No LLF Band found for this DNO and LLF combination.")
        st.stop()

    llf_band = band_row.iloc[0]["Band"]
    st.markdown(f"✅ **Matched LLF Band:** `{llf_band}`")

    # --- Filter Flat File ---
    filtered = df[
        (df["DNO_ID"] == int(dno)) &
        (df["LLF_Band"] == llf_band) &
        (df["Contract_Duration"] == int(contract_duration)) &
        (df["Green_Energy"].astype(str).str.upper() == green_energy.upper()) &
        (df["Minimum_Annual_Consumption"] <= annual_consumption) &
        (df["Maximum_Annual_Consumption"] >= annual_consumption)
    ]

    if filtered.empty:
        st.warning("No matching quotes found.")
    else:
        st.success(f"Found {len(filtered)} matching quote(s).")

        # --- Apply uplift to cost rates ---
        quote = filtered.copy()

        for col in ["Standard_Rate", "Day_Rate", "Night_Rate"]:
            if col in quote.columns:
                quote[f"{col}_With_Uplift"] = quote[col] + uplift

        # Reorder columns
        show_cols = [c for c in quote.columns if "Uplift" in c or "Charge" in c or "Rate" in c]
        st.dataframe(quote[show_cols], use_container_width=True)

        # --- Download as Excel ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            quote.to_excel(writer, index=False, sheet_name="Quotes")
            writer.save()
        st.download_button(
            label="📥 Download Quotes as Excel",
            data=output.getvalue(),
            file_name="Electricity_Quote.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Please upload your electricity flat file to begin.")
