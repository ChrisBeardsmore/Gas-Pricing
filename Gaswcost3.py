import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Dyce flat file Gas pricing with cost inputs V1", layout="wide")
st.title("🔹 Dyce Flat File Gas Pricing with Cost Inputs V1")

uploaded_file = st.file_uploader("Upload your pricing XLSX file:", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.drop(columns=[col for col in ["Minimum_Credit_Score", "Maximum_Credit_Score"] if col in df.columns])

    st.subheader("📄 Flat File Preview")
    st.dataframe(df.head())

    default_bands = [
        {"Min": 1000, "Max": 24999},
        {"Min": 25000, "Max": 49999},
        {"Min": 50000, "Max": 73199},
        {"Min": 73200, "Max": 124999},
        {"Min": 125000, "Max": 292999},
        {"Min": 293000, "Max": 449999},
        {"Min": 450000, "Max": 731999},
    ]

    year_inputs = {}

    for year in [1, 2, 3]:
        st.markdown(f"---\n## Year {year} Cost Inputs")

        cost_option = st.radio(
            f"Select Cost Input Method for Year {year}",
            ("Fixed £ per meter", "p/kWh uplift"),
            key=f"cost_option_{year}"
        )

        if cost_option == "Fixed £ per meter":
            fixed_cost = st.number_input(f"Fixed cost per meter (£) for Year {year}", min_value=0.0, key=f"fixed_cost_{year}")
            standing_pct = st.number_input(f"% to Standing Charge for Year {year}", min_value=0, max_value=100, key=f"standing_pct_{year}")
            unit_pct = st.number_input(f"% to Unit Rate for Year {year}", min_value=0, max_value=100, key=f"unit_pct_{year}")

            if standing_pct + unit_pct != 100:
                st.error(f"Year {year}: Standing % and Unit % must total 100%")

            year_inputs[year] = {"cost_method": "fixed", "fixed_cost": fixed_cost, "standing_pct": standing_pct, "unit_pct": unit_pct}

        else:
            ppkwh = st.number_input(f"Uplift per kWh (pence) for Year {year}", min_value=0.0, format="%.3f", key=f"ppkwh_{year}")
            year_inputs[year] = {"cost_method": "per_kwh", "ppkwh": ppkwh}

        st.markdown(f"### Year {year} Uplifts per Consumption Band")
        year_band_inputs = []

        for i, band in enumerate(default_bands):
            st.markdown(f"**Band {i+1}: {band['Min']} – {band['Max']} kWh**")
            cols = st.columns(4)

            std_unit = cols[0].number_input(f"Standard Unit Rate Uplift (p/kWh)", min_value=0.0, step=0.001, format="%.3f", key=f"std_unit_{year}_{i}")
            std_stand = cols[1].number_input(f"Standard Standing Charge Uplift (p/day)", min_value=0.0, step=0.1, format="%.4f", key=f"std_stand_{year}_{i}")
            carbon_unit = cols[2].number_input(f"Carbon Unit Rate Uplift (p/kWh)", min_value=0.0, step=0.001, format="%.3f", key=f"carbon_unit_{year}_{i}")
            carbon_stand = cols[3].number_input(f"Carbon Standing Charge Uplift (p/day)", min_value=0.0, step=0.1, format="%.4f", key=f"carbon_stand_{year}_{i}")

            year_band_inputs.append({
                "Min": band["Min"],
                "Max": band["Max"],
                "Standard_Unit": std_unit,
                "Standard_Standing": std_stand,
                "Carbon_Unit": carbon_unit,
                "Carbon_Standing": carbon_stand,
            })

        year_inputs[year]["bands"] = year_band_inputs

    def calculate_uplifts(row):
        duration_months = row["Contract_Duration"]
        duration = int(duration_months / 12)

        year_config = year_inputs.get(duration)

        if year_config is None:
            st.warning(f"No uplift configuration found for Contract Duration: {duration_months} months ({duration} years). Skipping uplift.")
            return pd.Series({"Uplift_Unit": 0, "Uplift_Standing": 0})

        cost_unit, cost_standing = 0, 0
        if year_config["cost_method"] == "fixed":
            fixed = year_config["fixed_cost"] * 100  # convert £ to pence
            cost_standing = (fixed * year_config["standing_pct"] / 100) / 365
            cost_unit = (fixed * year_config["unit_pct"] / 100) / row["Minimum_Annual_Consumption"]
        else:
            cost_unit = year_config["ppkwh"]

        band = next((b for b in year_config["bands"] if b["Min"] <= row["Minimum_Annual_Consumption"] <= b["Max"]), year_config["bands"][-1])
        carbon = str(row.get("Carbon_Offset", "")).strip().lower() in ["yes", "y", "true", "1"]

        uplift_unit = cost_unit + (band["Carbon_Unit"] if carbon else band["Standard_Unit"])
        uplift_standing = cost_standing + (band["Carbon_Standing"] if carbon else band["Standard_Standing"])

        return pd.Series({"Uplift_Unit": uplift_unit, "Uplift_Standing": uplift_standing})

    uplift_df = df.apply(calculate_uplifts, axis=1)
    df_final = pd.concat([df.reset_index(drop=True), uplift_df], axis=1)

    df_final["Unit Rate"] = (df_final["Unit_Rate"] + df_final["Uplift_Unit"]).round(4)
    df_final["Standing Charge"] = (df_final["Standing_Charge"] + df_final["Uplift_Standing"]).round(4)
    df_final["Total Annual Cost (£)"] = (
        (df_final["Standing Charge"] * 365) + (df_final["Unit Rate"] * df_final["Minimum_Annual_Consumption"])
    ) / 100

    st.subheader("✅ Final Price List Preview")
    st.dataframe(df_final.head())

    from datetime import datetime

# Broker Output File Name Input
broker_file_name = st.text_input("Enter file name for broker output (without extension):", value="broker_pricelist")

output_broker = io.BytesIO()
with pd.ExcelWriter(output_broker, engine="xlsxwriter") as writer:
    df_final[[
        "Broker_ID", "Production_Date", "Utility", "LDZ", "Exit_Zone",
        "Sale_Type", "Contract_Duration", "Minimum_Annual_Consumption", "Maximum_Annual_Consumption",
        "Minimum_Contract_Start_Date", "Maximum_Contract_Start_Date",
        "Minimum_Valid_Quote_Date", "Maximum_Valid_Quote_Date",
        "Product_Name", "Carbon_Offset",
        "Unit Rate", "Standing Charge", "Total Annual Cost (£)"
    ]].to_excel(writer, index=False, sheet_name="PriceList")

st.download_button(
    "⬇️ Download Broker Price List",
    data=output_broker.getvalue(),
    file_name=f"{broker_file_name}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# Internal Audit Output
audit_file_name = st.text_input("Enter file name for internal audit output (without extension):", value="internal_audit_report")

output_audit = io.BytesIO()
with pd.ExcelWriter(output_audit, engine="xlsxwriter") as writer:
    df_final.to_excel(writer, index=False, sheet_name="AuditData")

st.download_button(
    "⬇️ Download Internal Audit Report",
    data=output_audit.getvalue(),
    file_name=f"{audit_file_name}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

timestamp = datetime.now().strftime('%Y%m%d_%H%M')
file_name = f'broker_pricelist_{timestamp}.xlsx'

    st.download_button(
        "⬇️ Download Broker Price List",
        data=output.getvalue(),
        file_name="broker_pricelist.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
