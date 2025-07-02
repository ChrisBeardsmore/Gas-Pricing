# streamlit_app.py

import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Energy Pricing Uplift Tool", layout="wide")
st.title("🔹 Energy Pricing Uplift Calculator")

# Upload CSV
uploaded_file = st.file_uploader("Upload your flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = (
        df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")
    )

    st.success("✅ File loaded successfully.")
    st.write("Preview of your data:")
    st.dataframe(df.head())

    st.markdown("---")
    st.subheader("Step 1 – Enter Uplift Values (Pence)")

    # Contract length uplift inputs
    st.markdown("**Uplift for 1-Year Contracts**")
    col1_1, col1_2 = st.columns(2)
    uplift_1y_carbon_yes_unit = col1_1.number_input(
        "Carbon Offset = Yes – Unit Rate Uplift (p/kWh)", value=0.5, step=0.1
    )
    uplift_1y_carbon_yes_standing = col1_2.number_input(
        "Carbon Offset = Yes – Standing Charge Uplift (p/day)", value=5.0, step=0.1
    )

    col1_3, col1_4 = st.columns(2)
    uplift_1y_carbon_no_unit = col1_3.number_input(
        "Carbon Offset = No – Unit Rate Uplift (p/kWh)", value=0.3, step=0.1
    )
    uplift_1y_carbon_no_standing = col1_4.number_input(
        "Carbon Offset = No – Standing Charge Uplift (p/day)", value=3.0, step=0.1
    )

    st.markdown("**Uplift for 2-Year Contracts**")
    col2_1, col2_2 = st.columns(2)
    uplift_2y_carbon_yes_unit = col2_1.number_input(
        "Carbon Offset = Yes – Unit Rate Uplift (p/kWh)", value=0.4, step=0.1
    )
    uplift_2y_carbon_yes_standing = col2_2.number_input(
        "Carbon Offset = Yes – Standing Charge Uplift (p/day)", value=4.0, step=0.1
    )

    col2_3, col2_4 = st.columns(2)
    uplift_2y_carbon_no_unit = col2_3.number_input(
        "Carbon Offset = No – Unit Rate Uplift (p/kWh)", value=0.2, step=0.1
    )
    uplift_2y_carbon_no_standing = col2_4.number_input(
        "Carbon Offset = No – Standing Charge Uplift (p/day)", value=2.0, step=0.1
    )

    st.markdown("**Uplift for 3-Year Contracts**")
    col3_1, col3_2 = st.columns(2)
    uplift_3y_carbon_yes_unit = col3_1.number_input(
        "Carbon Offset = Yes – Unit Rate Uplift (p/kWh)", value=0.3, step=0.1
    )
    uplift_3y_carbon_yes_standing = col3_2.number_input(
        "Carbon Offset = Yes – Standing Charge Uplift (p/day)", value=3.0, step=0.1
    )

    col3_3, col3_4 = st.columns(2)
    uplift_3y_carbon_no_unit = col3_3.number_input(
        "Carbon Offset = No – Unit Rate Uplift (p/kWh)", value=0.1, step=0.1
    )
    uplift_3y_carbon_no_standing = col3_4.number_input(
        "Carbon Offset = No – Standing Charge Uplift (p/day)", value=1.0, step=0.1
    )

    st.markdown("---")
    st.subheader("Step 2 – Annual Consumption")
    annual_consumption = st.number_input(
        "Annual Consumption (kWh)", min_value=1, value=20000, step=500
    )

    days_per_year = 365

    def get_uplift(row):
        contract_length = int(row["contractlength"])
        carbon = str(row["carbonoffset"]).strip().lower() in ["yes", "y", "true", "1"]

        if contract_length == 1:
            if carbon:
                return uplift_1y_carbon_yes_unit, uplift_1y_carbon_yes_standing
            else:
                return uplift_1y_carbon_no_unit, uplift_1y_carbon_no_standing
        elif contract_length == 2:
            if carbon:
                return uplift_2y_carbon_yes_unit, uplift_2y_carbon_yes_standing
            else:
                return uplift_2y_carbon_no_unit, uplift_2y_carbon_no_standing
        elif contract_length == 3:
            if carbon:
                return uplift_3y_carbon_yes_unit, uplift_3y_carbon_yes_standing
            else:
                return uplift_3y_carbon_no_unit, uplift_3y_carbon_no_standing
        else:
            return 0.0, 0.0

    uplifts = df.apply(get_uplift, axis=1)
    df["unit_uplift_p"] = uplifts.apply(lambda x: x[0])
    df["standing_uplift_p"] = uplifts.apply(lambda x: x[1])

    df["unitrate_uplifted"] = df["unitrate"] + df["unit_uplift_p"]
    df["standingcharge_uplifted"] = df["standingcharge"] + df["standing_uplift_p"]

    df["total_annual_cost_£"] = (
        (df["unitrate_uplifted"] * annual_consumption) / 100
        + (df["standingcharge_uplifted"] * days_per_year) / 100
    ).round(2)

    columns_to_keep = [
        c
        for c in df.columns
        if c not in ["unitrate", "standingcharge", "unit_uplift_p", "standing_uplift_p"]
    ]
    output_df = df[columns_to_keep].copy()

    output_df = output_df.rename(
        columns={
            "standingcharge_uplifted": "Standing Charge (p/day)",
            "unitrate_uplifted": "Unit Rate (p/kWh)",
        }
    )

    st.markdown("---")
    st.subheader("✅ Preview of Final Output")
    st.dataframe(output_df.head())

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        output_df.to_excel(writer, index=False, sheet_name="Uplifted Prices")
    st.download_button(
        label="⬇️ Download Uplifted Price List (.xlsx)",
        data=output.getvalue(),
        file_name="uplifted_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
