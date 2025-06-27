import streamlit as st
import pandas as pd

st.title("Gas Pricing Uplift Tool")

# Step 1: Upload CSV
st.header("Step 1: Upload your flat file CSV")
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    st.write("Preview of uploaded data:")
    st.dataframe(df.head())

    # Ensure expected columns exist
    required_cols = ["Minimum Annual Consumption", "Maximum Annual Consumption", "Standing Charge", "Unit Rate"]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Column '{col}' not found in your file. Please check.")
            st.stop()

    # Create unique band table
    st.header("Step 2: Enter uplift per consumption band (points of a penny)")

    uplift_table = (
        df[["Minimum Annual Consumption", "Maximum Annual Consumption"]]
        .drop_duplicates()
        .sort_values(by="Minimum Annual Consumption")
        .reset_index(drop=True)
    )
    uplift_table["StandingChargeUpliftPoints"] = 0.0
    uplift_table["UnitRateUpliftPoints"] = 0.0

    # Show editable table
    st.caption("Adjust uplifts below. Scroll to see all bands.")
    uplift_table = st.data_editor(
        uplift_table,
        use_container_width=True,
        hide_index=True,
        height=500,
        num_rows="dynamic",
        column_config={
            "Minimum Annual Consumption": st.column_config.NumberColumn(
                "Min Consumption", disabled=True
            ),
            "Maximum Annual Consumption": st.column_config.NumberColumn(
                "Max Consumption", disabled=True
            ),
            "StandingChargeUpliftPoints": st.column_config.NumberColumn(
                "Standing Uplift (pts)", step=0.1
            ),
            "UnitRateUpliftPoints": st.column_config.NumberColumn(
                "Unit Uplift (pts)", step=0.1
            )
        }
    )

    # Step 3: Enter weighting percentages
    st.header("Step 3: Define weighting between standing charge and unit rate")
    standing_weight = st.slider("Standing Charge Weight (%)", 0, 100, 50)
    unit_weight = 100 - standing_weight
    st.write(f"Unit Rate Weight: {unit_weight}%")

    # Convert points to pounds (1 point = 0.0001 pounds)
    def get_uplifts(row):
        band = uplift_table[
            (row["Minimum Annual Consumption"] == uplift_table["Minimum Annual Consumption"]) &
            (row["Maximum Annual Consumption"] == uplift_table["Maximum Annual Consumption"])
        ]
        if not band.empty:
            sc_uplift = band["StandingChargeUpliftPoints"].values[0] * 0.0001
            ur_uplift = band["UnitRateUpliftPoints"].values[0] * 0.0001
            return pd.Series([sc_uplift, ur_uplift])
        else:
            return pd.Series([0.0, 0.0])

    df[["StandingChargeUplift", "UnitRateUplift"]] = df.apply(get_uplifts, axis=1)

    # Apply weighting
    standing_weight_factor = standing_weight / 100
    unit_weight_factor = unit_weight / 100

    df["FinalStandingCharge"] = df["Standing Charge"] + df["StandingChargeUplift"] * standing_weight_factor
    df["FinalUnitRate"] = df["Unit Rate"] + df["UnitRateUplift"] * unit_weight_factor

    # Round to 3 decimals
    df["FinalStandingCharge"] = df["FinalStandingCharge"].round(3)
    df["FinalUnitRate"] = df["FinalUnitRate"].round(3)

    # Show preview
    st.header("Step 4: Preview uplifted pricing")
    st.dataframe(df[["Minimum Annual Consumption", "Maximum Annual Consumption", "FinalStandingCharge", "FinalUnitRate"]])

    # Download
    st.header("Step 5: Download results")
    output_csv = df.to_csv(index=False)
    st.download_button(
        "Download uplifted pricing CSV",
        output_csv,
        file_name="uplifted_prices.csv",
        mime="text/csv"
    )
