import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Energy Pricing Uplift Tool", layout="wide")
st.title("🔹 Energy Pricing Uplift Calculator")

# Upload CSV
uploaded_file = st.file_uploader("Upload your flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File loaded successfully.")
    st.write("Preview of your data:")
    st.dataframe(df.head())

    st.markdown("---")
    st.subheader("Step 1 – Define Uplifts Per Band and Contract Length")

    default_bands = [
        {"Min": 0, "Max": 999},
        {"Min": 1000, "Max": 24999},
        {"Min": 25000, "Max": 49999},
        {"Min": 50000, "Max": 73199},
        {"Min": 73200, "Max": 124999},
        {"Min": 125000, "Max": 292999},
        {"Min": 293000, "Max": 731999},
    ]

    band_inputs = []
    st.markdown("### 🔸 Configure Uplifts per Consumption Band")
    for i, band in enumerate(default_bands):
        st.markdown(f"**Band {i+1}: {band['Min']}–{band['Max']} kWh**")
        cols = st.columns(6)
        inputs = {}
        for j, (label, key_suffix) in enumerate([
            ("Uplift 1yr (p/unit)", "1yr_unit"),
            ("Uplift 1yr (p/standing)", "1yr_standing"),
            ("Uplift 2yr (p/unit)", "2yr_unit"),
            ("Uplift 2yr (p/standing)", "2yr_standing"),
            ("Uplift 3yr (p/unit)", "3yr_unit"),
            ("Uplift 3yr (p/standing)", "3yr_standing"),
        ]):
            inputs[key_suffix] = cols[j].number_input(
                label,
                min_value=0.0,
                value=0.5,
                key=f"{key_suffix}_{i}"
            )
        band_inputs.append({
            "Min": band["Min"],
            "Max": band["Max"],
            **inputs
        })

    st.markdown("---")
    st.subheader("Step 2 – Define Additional Settings")
    standing_weight = st.slider("Standing Charge Weight (%)", 0.0, 100.0, 70.0, step=1.0)
    unit_weight = 100.0 - standing_weight

    annual_consumption = st.number_input(
        "Annual Consumption (kWh)", min_value=1, value=20000, step=500
    )

    st.markdown(f"""
    **Settings Summary:**
    - Standing Weight: {standing_weight}%
    - Unit Weight: {unit_weight}%
    - Annual Consumption: {annual_consumption} kWh
    """)

    days_per_year = 365

    def get_band_uplift(row):
        # Determine band
        uplift_band = None
        for b in band_inputs:
            if b["Min"] <= row["MinimumAnnualConsumption"] <= b["Max"]:
                uplift_band = b
                break
        if uplift_band is None:
            uplift_band = band_inputs[-1]

        # Determine contract length uplift
        contract_length = int(row["ContractLength"])
        if contract_length not in [1, 2, 3]:
            contract_length = 1

        # Determine Carbon Offset
        carbon_raw = str(row.get("Carbonoffset", "")).strip().lower()
        carbon = carbon_raw in ["yes", "y", "true", "1"]

        # For now, same uplifts for carbon/no-carbon. You can customize if desired.
        uplift_unit = uplift_band[f"{contract_length}yr_unit"]
        uplift_standing = uplift_band[f"{contract_length}yr_standing"]
        return pd.Series({"Uplift_Unit": uplift_unit, "Uplift_Standing": uplift_standing})

    uplifts = df.apply(get_band_uplift, axis=1)
    df = pd.concat([df, uplifts], axis=1)

    # New uplifted rates
    df["StandingCharge_Uplifted"] = (df["StandingCharge"] + df["Uplift_Standing"]).round(3)
    df["UnitRate_Uplifted"] = (df["UnitRate"] + df["Uplift_Unit"]).round(3)

    # Final uplifted annual cost
    df["EstimatedAnnualCost"] = (
        (df["StandingCharge_Uplifted"] * days_per_year) +
        (df["UnitRate_Uplifted"] * annual_consumption)
    ) / 100

    st.subheader("✅ Uplifted Data Preview")
    st.dataframe(df[[
        "ContractLength",
        "Carbonoffset",
        "StandingCharge_Uplifted",
        "UnitRate_Uplifted",
        "EstimatedAnnualCost"
    ]].head())

    # Prepare Broker-friendly dataframe
    broker_df = df[[
        "ContractLength",
        "Carbonoffset",
        "StandingCharge_Uplifted",
        "UnitRate_Uplifted",
        "EstimatedAnnualCost"
    ]].copy()

    broker_df.rename(columns={
        "StandingCharge_Uplifted": "Standing Charge (p/day)",
        "UnitRate_Uplifted": "Unit Rate (p/kWh)",
        "EstimatedAnnualCost": "Total Annual Cost (£)"
    }, inplace=True)

    # Excel download with formatting
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        broker_df.to_excel(writer, index=False, sheet_name="Price List")
        workbook = writer.book
        worksheet = writer.sheets["Price List"]

        # Format headers
        header_format = workbook.add_format({
            "bold": True,
            "text_wrap": True,
            "valign": "top",
            "fg_color": "#D7E4BC",
            "border": 1
        })
        for col_num, value in enumerate(broker_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 20)

    st.download_button(
        label="⬇️ Download Broker Excel File",
        data=output.getvalue(),
        file_name="broker_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
