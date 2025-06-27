import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gas Pricing Uplift Tool", layout="wide")

st.title("Gas Pricing Uplift Tool")

# 1️⃣ File Upload
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    # Read data
    df = pd.read_csv(uploaded_file)

    st.subheader("Preview of Uploaded Data")
    st.dataframe(df)

    # 2️⃣ Define consumption bands for uplifts
    st.subheader("Step 1: Enter uplift per consumption band (in points of a penny)")

    # Create unique band table
    uplift_table = (
        df[["Minimum Annual Consumption", "Maximum Annual Consumption"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )
    uplift_table["UpliftPoints"] = 0.0

    # Scrollable data editor
    uplift_table = st.data_editor(
        uplift_table,
        num_rows="dynamic",
        height=600,   # Makes it scrollable
        key="uplift_table"
    )

    # 3️⃣ Input weighting
    st.subheader("Step 2: Define weighting between standing and unit charges (%)")

    standing_weight = st.slider(
        "Standing Charge Weight (%)", min_value=0, max_value=100, value=50
    )
    unit_weight = 100 - standing_weight

    st.markdown(
        f"**Standing Weight:** {standing_weight}% &nbsp;&nbsp;&nbsp; **Unit Weight:** {unit_weight}%"
    )

    # 4️⃣ Helper function for uplift lookup
    def get_band_uplift(min_consumption, max_consumption):
        row = uplift_table[
            (uplift_table["Minimum Annual Consumption"] == min_consumption)
            & (uplift_table["Maximum Annual Consumption"] == max_consumption)
        ]
        if not row.empty:
            return row["UpliftPoints"].iloc[0]
        return 0.0

    # 5️⃣ Apply uplift logic
    df["UpliftPoints"] = df.apply(
        lambda r: get_band_uplift(
            r["Minimum Annual Consumption"],
            r["Maximum Annual Consumption"]
        ),
        axis=1
    )

    df["StandingChargeUplift"] = (
        df["UpliftPoints"] * (standing_weight / 100)
    ) / 100  # Convert points to pounds
    df["UnitRateUplift"] = (
        df["UpliftPoints"] * (unit_weight / 100)
    ) / 100

    df["NewStandingCharge"] = (
        df["Standing Charge"] + df["StandingChargeUplift"]
    ).round(3)
    df["NewUnitRate"] = (
        df["Unit Rate"] + df["UnitRateUplift"]
    ).round(3)

    # 6️⃣ Display output
    st.subheader("Preview of Uplifted Prices")
    st.dataframe(
        df[
            [
                "Minimum Annual Consumption",
                "Maximum Annual Consumption",
                "Standing Charge",
                "Unit Rate",
                "NewStandingCharge",
                "NewUnitRate",
            ]
        ]
    )

    # 7️⃣ Download button
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Uplifted Prices as CSV",
        data=csv,
        file_name="uplifted_prices.csv",
        mime="text/csv"
    )
