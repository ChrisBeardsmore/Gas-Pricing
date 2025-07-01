import streamlit as st
import pandas as pd
import io

# Page configuration
st.set_page_config(page_title="Energy Pricing Uplift Tool", layout="wide")
st.title("🔹 Energy Pricing Uplift Calculator")

# Upload CSV file
uploaded_file = st.file_uploader("Upload your flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]

    st.success("✅ File loaded successfully.")
    st.write("Preview of your data:")
    st.dataframe(df.head())

    st.markdown("---")
    st.subheader("Step 1 – Define Uplifts by Band, Contract Length, Carbon Offset")

    # Define default bands
    default_bands = [
        {"Min": 0, "Max": 999},
        {"Min": 1000, "Max": 24999},
        {"Min": 25000, "Max": 49999},
        {"Min": 50000, "Max": 73199},
        {"Min": 73200, "Max": 124999},
        {"Min": 125000, "Max": 292999},
        {"Min": 293000, "Max": 731999},
    ]

    contract_lengths = ["1 Year", "2 Year", "3 Year"]

    st.write("**Enter uplift in pence for each band, contract length, and carbon offset status.**")

    band_uplifts = []

    with st.expander("Click to edit uplifts for all bands (scrollable)", expanded=True):
        for i, band in enumerate(default_bands):
            st.markdown(f"**Band {i+1}: {band['Min']} - {band['Max']} kWh**")
            cols = st.columns(6)
            for j, contract in enumerate(contract_lengths):
                uplift_sc_yes = cols[0].number_input(
                    f"{contract} | Carbon Offset YES | Standing Charge (p/day)",
                    value=0.0,
                    key=f"sc_yes_{i}_{j}",
                    step=0.1,
                )
                uplift_unit_yes = cols[1].number_input(
                    f"{contract} | Carbon Offset YES | Unit Rate (p/kWh)",
                    value=0.0,
                    key=f"unit_yes_{i}_{j}",
                    step=0.1,
                )
                uplift_sc_no = cols[2].number_input(
                    f"{contract} | Carbon Offset NO | Standing Charge (p/day)",
                    value=0.0,
                    key=f"sc_no_{i}_{j}",
                    step=0.1,
                )
                uplift_unit_no = cols[3].number_input(
                    f"{contract} | Carbon Offset NO | Unit Rate (p/kWh)",
                    value=0.0,
                    key=f"unit_no_{i}_{j}",
                    step=0.1,
                )
            band_uplifts.append(
                {
                    "Min": band["Min"],
                    "Max": band["Max"],
                    "Uplifts": {
                        contract: {
                            "CarbonOffsetYes": {
                                "Standing": uplift_sc_yes,
                                "Unit": uplift_unit_yes,
                            },
                            "CarbonOffsetNo": {
                                "Standing": uplift_sc_no,
                                "Unit": uplift_unit_no,
                            },
                        }
                        for contract in contract_lengths
                    },
                }
            )

    st.markdown("---")
    st.subheader("Step 2 – Define Other Settings")

    annual_consumption = st.number_input(
        "Annual Consumption (kWh)", min_value=1, value=20000, step=500
    )

    days_per_year = 365

    st.markdown("---")
    st.subheader("Step 3 – Select Contract Length")

    selected_contract = st.selectbox(
        "Choose contract length for this pricing:", contract_lengths
    )

    st.markdown("---")
    st.subheader("Step 4 – Calculate Uplifted Prices")

    # Ensure expected columns exist
    required_columns = ["minimumannualconsumption", "maximumannualconsumption", "standingcharge", "unitrate", "carbonoffset"]
    for col in required_columns:
        if col not in df.columns:
            st.error(f"Column '{col}' not found in your CSV. Please check your file.")
            st.stop()

    def get_uplift(row):
        consumption = row["maximumannualconsumption"]
        carbon = str(row["carbonoffset"]).strip().lower() in ["yes", "y", "true", "1"]
        carbon_key = "CarbonOffsetYes" if carbon else "CarbonOffsetNo"
        uplift_sc = 0.0
        uplift_unit = 0.0
        for b in band_uplifts:
            if b["Min"] <= consumption <= b["Max"]:
                uplift_sc = b["Uplifts"][selected_contract][carbon_key]["Standing"]
                uplift_unit = b["Uplifts"][selected_contract][carbon_key]["Unit"]
                break
        return pd.Series({"Uplift_SC": uplift_sc, "Uplift_Unit": uplift_unit})

    uplifts = df.apply(get_uplift, axis=1)
    df = pd.concat([df, uplifts], axis=1)

    # Calculate uplifted prices
    df["StandingCharge_Uplifted"] = (df["standingcharge"] + df["Uplift_SC"]).round(3)
    df["UnitRate_Uplifted"] = (df["unitrate"] + df["Uplift_Unit"]).round(3)

    # Calculate annual cost
    df["TotalAnnualCost"] = (
        (df["StandingCharge_Uplifted"] * days_per_year) +
        (df["UnitRate_Uplifted"] * annual_consumption)
    ) / 100
    df["TotalAnnualCost"] = df["TotalAnnualCost"].round(2)

    st.success("✅ Calculations complete.")
    st.write("**Internal Preview (full details):**")
    st.dataframe(df)

    # Prepare broker-facing output
    broker_cols = [
        "ContractLength",
        "carbonoffset",
        "minimumannualconsumption",
        "maximumannualconsumption",
        "StandingCharge_Uplifted",
        "UnitRate_Uplifted",
        "TotalAnnualCost",
    ]

    # Add ContractLength column
    df["ContractLength"] = selected_contract

    broker_df = df[broker_cols].rename(
        columns={
            "carbonoffset": "Carbon Offset",
            "StandingCharge_Uplifted": "Standing Charge (p/day)",
            "UnitRate_Uplifted": "Unit Rate (p/kWh)",
            "TotalAnnualCost": "Total Annual Cost (£)"
        }
    )

    # Download as Excel
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        broker_df.to_excel(writer, sheet_name="Price List", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Price List"]
        money_fmt = workbook.add_format({'num_format': '£#,##0.00'})
        pence_fmt = workbook.add_format({'num_format': '0.000'})
        worksheet.set_column("E:F", 15, pence_fmt)
        worksheet.set_column("G:G", 18, money_fmt)

    st.markdown("---")
    st.subheader("Step 5 – Download Broker-Ready Price List")

    st.download_button(
        label="⬇️ Download Broker Excel File",
        data=output.getvalue(),
        file_name="broker_price_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
