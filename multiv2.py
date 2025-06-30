import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Multi-Site Gas Pricing", layout="wide")

st.title("Multi-Site Gas Pricing Tool")

# Define column names
customer_columns = [
    "MPRN",
    "Start Month",
    "AQ (kWh)",
    "AQ Band",
    "AQ Ref",
    "Postcode",
    "S/C Commission (p/day)",
    "Unit Rate Commission (p/kWh)",
    "LDZ"
]

pricing_columns = [
    # 1 Year
    "1Y Standing Charge (p/Day)",
    "1Y Unit Rate (p/kWh)",
    "1Y Forecast Annual Spend (£)",
    "1Y Forecast Annual Commission (£)",
    "1Y Tariff ID",
    # 2 Year
    "2Y Standing Charge (p/Day)",
    "2Y Unit Rate (p/kWh)",
    "2Y Forecast Annual Spend (£)",
    "2Y Forecast Annual Commission (£)",
    "2Y Tariff ID",
    # 3 Year
    "3Y Standing Charge (p/Day)",
    "3Y Unit Rate (p/kWh)",
    "3Y Forecast Annual Spend (£)",
    "3Y Forecast Annual Commission (£)",
    "3Y Tariff ID"
]

# Create empty DataFrame with 100 rows
initial_data = pd.DataFrame(
    "",
    index=range(100),
    columns=customer_columns
)

st.subheader("Input Data (Paste or Type Below)")
edited_df = st.data_editor(
    initial_data,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    key="matrix_editor"
)

# Button to trigger calculations
if st.button("Calculate Pricing"):
    st.subheader("Pricing Results")

    # Convert relevant columns to numeric
    for col in ["AQ (kWh)", "S/C Commission (p/day)", "Unit Rate Commission (p/kWh)"]:
        edited_df[col] = pd.to_numeric(edited_df[col], errors="coerce").fillna(0)

    # Create output DataFrame
    output_df = edited_df.copy()

    # Logic for pricing
    # For example purposes: base unit rate and standing charge
    BASE_STANDING_CHARGE = 25.0   # p/day
    BASE_UNIT_RATE = 4.5          # p/kWh
    TERM_MULTIPLIERS = {1: 1.0, 2: 0.98, 3: 0.95}  # longer contracts get discount

    # Loop through each row and calculate
    for i, row in output_df.iterrows():
        aq = row["AQ (kWh)"]
        sc_commission = row["S/C Commission (p/day)"]
        ur_commission = row["Unit Rate Commission (p/kWh)"]

        for term in [1, 2, 3]:
            multiplier = TERM_MULTIPLIERS[term]

            standing_charge = (BASE_STANDING_CHARGE + sc_commission) * multiplier
            unit_rate = (BASE_UNIT_RATE + ur_commission) * multiplier

            annual_standing = standing_charge * 365 / 100  # p to £
            annual_unit = unit_rate * aq / 100             # p to £
            annual_spend = annual_standing + annual_unit

            forecast_commission = (sc_commission * 365 / 100) + (ur_commission * aq / 100)

            output_df[f"{term}Y Standing Charge (p/Day)"] = standing_charge
            output_df[f"{term}Y Unit Rate (p/kWh)"] = unit_rate
            output_df[f"{term}Y Forecast Annual Spend (£)"] = np.round(annual_spend, 2)
            output_df[f"{term}Y Forecast Annual Commission (£)"] = np.round(forecast_commission, 2)
            output_df[f"{term}Y Tariff ID"] = f"TID-{term}"

    # Show the results
    st.dataframe(output_df, use_container_width=True)

    # Allow download
    csv = output_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Results as CSV",
        data=csv,
        file_name="multi_site_pricing_results.csv",
        mime="text/csv"
    )

st.info("Tip: Paste data directly into the table above. Then click Calculate Pricing.")
