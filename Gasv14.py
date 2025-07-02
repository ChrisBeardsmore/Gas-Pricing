import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Gas Pricing Uplift Tool", layout="wide")
st.title("Gas Pricing Uplift Tool")

st.write("Upload your pricing CSV file:")

uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Remove all Unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    st.write("Detected columns:", df.columns.tolist())

    # Check expected columns
    expected_cols = [
        "ContractDuration",
        "MinimumAnnualConsumption",
        "MaximumAnnualConsumption",
        "StandingCharge",
        "UnitRate",
        "CarbonOffset"
    ]

    if not all(col in df.columns for col in expected_cols):
        st.error("One or more expected columns are missing.")
        st.stop()

    # Uplift inputs
    st.sidebar.header("Enter Uplifts")

    # Absolute uplifts in pence
    standing_uplift = st.sidebar.number_input("Standing Charge Uplift (p/day)", value=0.0, step=0.01)
    unit_uplift_1yr = st.sidebar.number_input("Unit Rate Uplift (1yr) (p/kWh)", value=0.0, step=0.01)
    unit_uplift_2yr = st.sidebar.number_input("Unit Rate Uplift (2yr) (p/kWh)", value=0.0, step=0.01)
    unit_uplift_3yr = st.sidebar.number_input("Unit Rate Uplift (3yr) (p/kWh)", value=0.01, step=0.01)

    # Carbon uplift
    carbon_uplift = st.sidebar.number_input("Carbon Offset Uplift (p/kWh)", value=0.0, step=0.01)

    # Function to calculate uplifted prices
    def apply_uplift(row):
        # Select unit uplift by contract duration
        duration = int(row["ContractDuration"])
        if duration == 1:
            unit_uplift = unit_uplift_1yr
        elif duration == 2:
            unit_uplift = unit_uplift_2yr
        elif duration == 3:
            unit_uplift = unit_uplift_3yr
        else:
            unit_uplift = 0.0

        # Carbon uplift
        if str(row["CarbonOffset"]).strip().lower() in ["yes", "y", "true", "1"]:
            carbon = carbon_uplift
        else:
            carbon = 0.0

        uplifted_unit_rate = row["UnitRate"] + unit_uplift + carbon
        uplifted_standing_charge = row["StandingCharge"] + standing_uplift

        # Estimated annual cost
        avg_consumption = (row["MinimumAnnualConsumption"] + row["MaximumAnnualConsumption"]) / 2
        annual_cost = (avg_consumption * uplifted_unit_rate / 100) + (uplifted_standing_charge * 365 / 100)

        return pd.Series([uplifted_unit_rate, uplifted_standing_charge, annual_cost])

    df[["UpliftedUnitRate", "UpliftedStandingCharge", "TotalAnnualCost"]] = df.apply(apply_uplift, axis=1)

    st.subheader("Preview of Uplifted Data")
    st.dataframe(df)

    # Download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="UpliftedPrices")
    st.download_button(
        label="Download Uplifted Prices as Excel",
        data=output.getvalue(),
        file_name="uplifted_prices.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
