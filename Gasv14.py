import streamlit as st
import pandas as pd
from io import BytesIO

# App title
st.set_page_config(page_title="Gas Pricing Uplift Tool", layout="wide")
st.title("💼 Gas Pricing Uplift Tool")

st.markdown(
    """
    **Instructions:**
    - Upload your flat file CSV.
    - Enter uplifts for each contract length (p/kWh and p/day).
    - Differentiate uplifts for CarbonOffset: Yes or No.
    - Preview uplifted prices.
    - Download as Excel.
    """
)

# File upload
uploaded_file = st.file_uploader("Upload your gas flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Show original columns to verify
    st.subheader("Original Data Sample")
    st.dataframe(df.head())

    # Confirm required columns exist
    expected_cols = [
        "Postcode", "MPAN", "StartDate", "EndDate",
        "ContractLength", "ConsumptionBand",
        "StandingCharge", "UnitRate", "CarbonOffset"
    ]
    if not all(col in df.columns for col in expected_cols):
        st.error("One or more expected columns are missing.")
        st.stop()

    st.subheader("Set Uplifts (in pence)")

    # Create dictionaries for uplifts by contract length and CarbonOffset
    uplifts = {}
    for contract_length in [1, 2, 3]:
        st.markdown(f"**Contract Length: {contract_length} Year(s)**")
        col1, col2 = st.columns(2)
        with col1:
            unit_no = st.number_input(
                f"Unit Rate Uplift (p/kWh) - CarbonOffset NO (Year {contract_length})",
                min_value=0.0, step=0.01, key=f"unit_no_{contract_length}")
            standing_no = st.number_input(
                f"Standing Charge Uplift (p/day) - CarbonOffset NO (Year {contract_length})",
                min_value=0.0, step=0.01, key=f"standing_no_{contract_length}")
        with col2:
            unit_yes = st.number_input(
                f"Unit Rate Uplift (p/kWh) - CarbonOffset YES (Year {contract_length})",
                min_value=0.0, step=0.01, key=f"unit_yes_{contract_length}")
            standing_yes = st.number_input(
                f"Standing Charge Uplift (p/day) - CarbonOffset YES (Year {contract_length})",
                min_value=0.0, step=0.01, key=f"standing_yes_{contract_length}")

        uplifts[(contract_length, False)] = {"unit": unit_no, "standing": standing_no}
        uplifts[(contract_length, True)] = {"unit": unit_yes, "standing": standing_yes}

    # Function to apply uplift
    def apply_uplift(row):
        contract_length = int(row["ContractLength"])
        carbon = str(row["CarbonOffset"]).strip().lower() in ["yes", "y", "true", "1"]

        uplift = uplifts.get((contract_length, carbon), {"unit": 0, "standing": 0})
        uplifted_unit = row["UnitRate"] + uplift["unit"]
        uplifted_standing = row["StandingCharge"] + uplift["standing"]
        total_annual_cost = (
            uplifted_unit * float(row["ConsumptionBand"]) +
            uplifted_standing * 365 / 100  # assuming pence/day
        )
        return pd.Series({
            "UpliftedUnitRate": round(uplifted_unit, 4),
            "UpliftedStandingCharge": round(uplifted_standing, 4),
            "TotalAnnualCost": round(total_annual_cost, 2)
        })

    # Apply uplift calculations
    uplifted_results = df.apply(apply_uplift, axis=1)

    # Merge results with original data
    df_final = pd.concat([df, uplifted_results], axis=1)

    st.subheader("Preview Uplifted Pricing")
    st.dataframe(df_final.head(20))

    # Excel download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_final.to_excel(writer, index=False, sheet_name="UpliftedPrices")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Download Excel File",
        data=excel_data,
        file_name="uplifted_gas_prices.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
