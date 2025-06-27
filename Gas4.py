import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gas Pricing Uplift Tool", layout="wide")

st.title("🔧 Gas Pricing Uplift Tool")

# Step 1: Upload CSV
st.subheader("Step 0: Upload Supplier Flat File (.csv)")
uploaded_file = st.file_uploader("Upload your flat file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Standardize column names (strip leading/trailing whitespace)
    df.columns = df.columns.str.strip()

    if "Minimum Annual Consumption" not in df.columns or "Maximum Annual Consumption" not in df.columns:
        st.error("The file must include 'Minimum Annual Consumption' and 'Maximum Annual Consumption' columns.")
    else:
       # Step 2: Define uplift values for each consumption band
st.subheader("Step 1: Enter uplift per consumption band (in points of a penny)")

uplift_table = (
    df[["Minimum Annual Consumption", "Maximum Annual Consumption"]]
    .drop_duplicates()
    .sort_values(by="Minimum Annual Consumption")
    .reset_index(drop=True)
)

uplift_table["StandingChargeUpliftPoints"] = 0.0
uplift_table["UnitRateUpliftPoints"] = 0.0

uplift_table = st.data_editor(
    uplift_table,
    num_rows="dynamic",
    hide_index=True,
    use_container_width=True,
    height=600,
    key="uplift_table",
    column_config={
        "Minimum Annual Consumption": st.column_config.NumberColumn(
            "Min Consumption", disabled=True
        ),
        "Maximum Annual Consumption": st.column_config.NumberColumn(
            "Max Consumption", disabled=True
        ),
        "StandingChargeUpliftPoints": st.column_config.NumberColumn(
            "Standing Charge Uplift (pts)", 
            help="Enter uplift in points of a penny (e.g., 2.5 = 0.025)",
            step=0.1
        ),
        "UnitRateUpliftPoints": st.column_config.NumberColumn(
            "Unit Rate Uplift (pts)",
            help="Enter uplift in points of a penny (e.g., 1.0 = 0.01)",
            step=0.1
        )
    }
)
        

        # Step 3: Select weighting logic
        st.subheader("Step 2: Define weighting between Standing Charge and Unit Rate")

        col1, col2 = st.columns(2)
        with col1:
            standing_weight = st.slider("Standing Charge Weight (%)", 0, 100, 50, step=1)
        with col2:
            unit_weight = 100 - standing_weight
            st.markdown(f"**Unit Rate Weight (%):** {unit_weight}")

        # Helper function to find matching band
        def get_uplifts(min_cons, max_cons):
            match = uplift_table[
                (uplift_table["Minimum Annual Consumption"] == min_cons) &
                (uplift_table["Maximum Annual Consumption"] == max_cons)
            ]
            if not match.empty:
                return (
                    match["StandingChargeUpliftPoints"].values[0],
                    match["UnitRateUpliftPoints"].values[0]
                )
            else:
                return (0.0, 0.0)

        # Apply uplift logic
        df["StandingChargeUpliftPoints"] = df.apply(
            lambda row: get_uplifts(
                row["Minimum Annual Consumption"],
                row["Maximum Annual Consumption"]
            )[0],
            axis=1
        )

        df["UnitRateUpliftPoints"] = df.apply(
            lambda row: get_uplifts(
                row["Minimum Annual Consumption"],
                row["Maximum Annual Consumption"]
            )[1],
            axis=1
        )

        # Convert points to pence
        df["Adjusted Standing Charge"] = (
            df["Standing Charge"] + df["StandingChargeUpliftPoints"] / 100
        ).round(3)

        df["Adjusted Unit Rate"] = (
            df["Unit Rate"] + df["UnitRateUpliftPoints"] / 100
        ).round(3)

        # Step 4: Apply weighting (for internal analysis or UI display)
        df["Weighted Price"] = (
            df["Adjusted Standing Charge"] * (standing_weight / 100)
            + df["Adjusted Unit Rate"] * (unit_weight / 100)
        ).round(3)

        # Step 5: Show results
        st.subheader("Step 3: Uplifted Pricing Preview")
        st.dataframe(df[[
            "Minimum Annual Consumption",
            "Maximum Annual Consumption",
            "Standing Charge",
            "Unit Rate",
            "StandingChargeUpliftPoints",
            "UnitRateUpliftPoints",
            "Adjusted Standing Charge",
            "Adjusted Unit Rate",
            "Weighted Price"
        ]], use_container_width=True)

        # Step 6: Download option
        st.subheader("Step 4: Download Uplifted File")
        output_csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download CSV", output_csv, file_name="uplifted_prices.csv", mime="text/csv")
