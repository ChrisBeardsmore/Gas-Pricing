import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gas Pricing Tool", layout="centered")

st.title("📊 Gas Pricing Model Tool")

# 1️⃣ Upload the flat file
st.subheader("Step 1: Upload your gas flat file")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("File uploaded successfully!")

    # Preview original data
    if st.checkbox("Show raw uploaded data"):
        st.dataframe(df.head())

    # 2️⃣ Enter uplift per consumption band
    st.subheader("Step 2: Enter uplift per consumption band (points of a penny)")
    st.caption("Adjust uplifts below. Scroll to see all bands.")

    # Create unique band table
    uplift_table = (
        df[["Minimum Annual Consumption", "Maximum Annual Consumption"]]
        .drop_duplicates()
        .sort_values("Minimum Annual Consumption")
        .reset_index(drop=True)
    )
    uplift_table["StandingChargeUpliftPoints"] = 0.0
    uplift_table["UnitRateUpliftPoints"] = 0.0

    # Editable input
    uplift_table = st.data_editor(
        uplift_table,
        use_container_width=True,
        hide_index=True,
        height=500,
        column_config={
            "Minimum Annual Consumption": st.column_config.NumberColumn(
                "Min Consumption", disabled=True
            ),
            "Maximum Annual Consumption": st.column_config.NumberColumn(
                "Max Consumption", disabled=True
            ),
            "StandingChargeUpliftPoints": st.column_config.NumberColumn(
                "Standing Uplift (pts)", step=0.1, required=True
            ),
            "UnitRateUpliftPoints": st.column_config.NumberColumn(
                "Unit Uplift (pts)", step=0.1, required=True
            )
        }
    )

    # 3️⃣ Set weighting between standing charge and unit rate
    st.subheader("Step 3: Define weighting between Standing Charge and Unit Rate")
    standing_weight = st.slider("Standing Charge Weighting (%)", 0, 100, 50)
    unit_weight = 100 - standing_weight
    st.markdown(
        f"- **Standing Charge Weight**: {standing_weight}%\n"
        f"- **Unit Rate Weight**: {unit_weight}%"
    )

    # 4️⃣ Apply uplifts and recalculate prices
    st.subheader("Step 4: Calculate final prices with uplifts")

    def get_band_uplift(consumption):
        for _, row in uplift_table.iterrows():
            if row["Minimum Annual Consumption"] <= consumption <= row["Maximum Annual Consumption"]:
                return row["StandingChargeUpliftPoints"], row["UnitRateUpliftPoints"]
        return 0.0, 0.0

    # Apply uplift logic
    uplift_data = df.apply(
        lambda r: get_band_uplift(r["Annual Consumption"]),
        axis=1,
        result_type='expand'
    )
    df["StandingChargeUpliftPoints"], df["UnitRateUpliftPoints"] = uplift_data[0], uplift_data[1]

    # Convert points of a penny to pounds (1 point = £0.0001)
    df["StandingChargeUplift"] = (df["StandingChargeUpliftPoints"] / 10000) * (standing_weight / 100)
    df["UnitRateUplift"] = (df["UnitRateUpliftPoints"] / 10000) * (unit_weight / 100)

    df["FinalStandingCharge"] = (df["Standing Charge"] + df["StandingChargeUplift"]).round(3)
    df["FinalUnitRate"] = (df["Unit Rate"] + df["UnitRateUplift"]).round(3)

    # Display result
    st.markdown("### 📈 Final Output Table")
    st.dataframe(
        df[[
            "Annual Consumption", "Standing Charge", "Unit Rate",
            "StandingChargeUpliftPoints", "UnitRateUpliftPoints",
            "FinalStandingCharge", "FinalUnitRate"
        ]].round(3),
        use_container_width=True
    )

    # Option to download result
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Updated CSV", csv, "updated_gas_prices.csv", "text/csv")
