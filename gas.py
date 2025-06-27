import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Energy Pricing Uplift Tool", layout="wide")

st.title("🔹 Energy Pricing Uplift Calculator (Per Band)")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("✅ File loaded successfully.")
    st.write("Preview of your data:")
    st.dataframe(df.head())

    st.markdown("---")

    st.subheader("Step 1 – Define Uplift % Per Consumption Band")
    st.markdown("Below, enter uplift % for each band. You can adjust as needed:")

    # Define default band uplift table
    default_bands = pd.DataFrame({
        "MinConsumption": [0, 25000, 50000],
        "MaxConsumption": [24999, 49999, 999999],
        "UpliftPercent": [5.0, 3.0, 2.0]
    })

    bands = st.experimental_data_editor(
        default_bands,
        num_rows="dynamic",
        use_container_width=True,
        key="band_table"
    )

    st.markdown("---")

    st.subheader("Step 2 – Define Weighting and Consumption")
    standing_weight = st.slider("Standing Charge Weight (%)", 0.0, 100.0, 70.0, step=1.0)
    unit_weight = 100.0 - standing_weight

    annual_consumption = st.number_input(
        "Annual Consumption (kWh)",
        min_value=1,
        value=20000,
        step=500
    )

    st.markdown(f"""
    **Settings Summary:**
    - Standing Weight: {standing_weight}%
    - Unit Weight: {unit_weight}%
    - Annual Consumption: {annual_consumption} kWh
    """)

    days_per_year = 365

    st.markdown("---")

    # Function to get uplift % per row
    def get_band_uplift(min_kwh, max_kwh):
        for _, row in bands.iterrows():
            if min_kwh >= row["MinConsumption"] and max_kwh <= row["MaxConsumption"]:
                return row["UpliftPercent"]
        return 0.0

    # Apply uplift % lookup
    df["UpliftPercent"] = df.apply(
        lambda r: get_band_uplift(r["MinimumAnnualConsumption"], r["MaximumAnnualConsumption"]),
        axis=1
    )

    # Original estimated cost
    df["EstimatedAnnualCost_Original"] = (
        (df["StandingCharge"] * days_per_year) +
        (df["UnitRate"] * annual_consumption)
    ) / 100

    # Uplift £
    df["Target_Uplift_GBP"] = df["EstimatedAnnualCost_Original"] * (df["UpliftPercent"] / 100)

    # Split uplift £
    df["Standing_Uplift_GBP"] = df["Target_Uplift_GBP"] * (standing_weight / 100)
    df["Unit_Uplift_GBP"] = df["Target_Uplift_GBP"] * (unit_weight / 100)

    # Convert to pence uplift
    df["Standing_Uplift_p"] = (df["Standing_Uplift_GBP"] / days_per_year) * 100
    df["Unit_Uplift_p"] = (df["Unit_Uplift_GBP"] / annual_consumption) * 100

    # Round
    df["Standing_Uplift_p"] = df["Standing_Uplift_p"].round(3)
    df["Unit_Uplift_p"] = df["Unit_Uplift_p"].round(3)

    # New uplifted rates
    df["StandingCharge_Uplifted"] = (df["StandingCharge"] + df["Standing_Uplift_p"]).round(3)
    df["UnitRate_Uplifted"] = (df["UnitRate"] + df["Unit_Uplift_p"]).round(3)

    # Uplifted annual cost
    df["EstimatedAnnualCost_Uplifted"] = (
        (df["StandingCharge_Uplifted"] * days_per_year) +
        (df["UnitRate_Uplifted"] * annual_consumption)
    ) / 100

    st.subheader("✅ Preview of Uplifted Data")
    st.dataframe(df.head())

    output = io.BytesIO()
    df.to_csv(output, index=False)

    st.download_button(
        label="⬇️ Download Uplifted CSV",
        data=output.getvalue(),
        file_name="uplifted_output_per_band.csv",
        mime="text/csv"
    )
