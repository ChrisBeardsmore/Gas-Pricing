import streamlit as st
import pandas as pd
import io
import json
from datetime import datetime

st.set_page_config(page_title="Dyce Gas Pricing Tool with Configurable Bands", layout="wide")
st.title("🔹 Dyce Gas Pricing Tool with Configurable Bands & Version Control")

uploaded_file = st.file_uploader("Upload your supplier flat file (.xlsx):", type="xlsx")

# Load Margin Template
st.sidebar.subheader("🔖 Load Margin Template")
margin_template_file = st.sidebar.file_uploader("Upload Margin Template (JSON)", type="json")
loaded_template = json.load(margin_template_file) if margin_template_file else {}

# Configurable Bands
st.subheader("Step 1 – Configure Consumption Bands")

default_bands = loaded_template.get("bands", [
    {"Min": 1000, "Max": 24999},
    {"Min": 25000, "Max": 49999},
    {"Min": 50000, "Max": 73199},
    {"Min": 73200, "Max": 124999},
    {"Min": 125000, "Max": 292999},
    {"Min": 293000, "Max": 449999},
    {"Min": 450000, "Max": 731999},
])

bands = []
for i in range(len(default_bands)):
    st.markdown(f"**Band {i+1}**")
    cols = st.columns(2)
    min_val = cols[0].number_input(f"Minimum Consumption (kWh) Band {i+1}", min_value=0, value=default_bands[i]['Min'], key=f"band_min_{i}")
    max_val = cols[1].number_input(f"Maximum Consumption (kWh) Band {i+1}", min_value=0, value=default_bands[i]['Max'], key=f"band_max_{i}")
    bands.append({"Min": min_val, "Max": max_val})

# Validate bands for overlaps
for idx in range(1, len(bands)):
    if bands[idx]['Min'] <= bands[idx-1]['Max']:
        st.error(f"Bands {idx} and {idx+1} are overlapping. Please correct them!")

version_label = st.text_input("Enter version label for this pricing configuration:", value=loaded_template.get('template_name', 'v1'))

# Yearly cost inputs and band uplifts
year_inputs = {}
for year in [1,2,3]:
    st.markdown(f"---\n### Year {year} Cost Inputs")
    year_data = loaded_template.get('years', {}).get(str(year), {})
    cost_option = st.radio(
        f"Cost Input Method for Year {year}",
        ("Fixed £ per meter", "p/kWh uplift"),
        index=0 if year_data.get("cost_method", "fixed") == "fixed" else 1,
        key=f"cost_option_{year}"
    )

    if cost_option == "Fixed £ per meter":
        fixed_cost = st.number_input(f"Fixed cost per meter (£) Year {year}", min_value=0.0, value=year_data.get('fixed_cost', 0.0))
        standing_pct = st.number_input(f"% to Standing Charge Year {year}", min_value=0, max_value=100, value=year_data.get('standing_pct', 50))
        unit_pct = st.number_input(f"% to Unit Rate Year {year}", min_value=0, max_value=100, value=year_data.get('unit_pct', 50))
    else:
        ppkwh = st.number_input(f"Uplift per kWh (pence) Year {year}", min_value=0.0, value=year_data.get('ppkwh', 0.0))

    st.markdown(f"#### Year {year} Uplifts per Band")
    band_inputs = []
    loaded_bands = year_data.get("bands", [])
    for i, band in enumerate(bands):
        st.markdown(f"**Band {i+1}: {band['Min']} – {band['Max']} kWh**")
        cols = st.columns(4)
        defaults = loaded_bands[i] if i < len(loaded_bands) else {}
        std_unit = cols[0].number_input("Standard Unit Uplift (p/kWh)", min_value=0.0, value=defaults.get('Standard_Unit', 0.0), key=f"std_unit_{year}_{i}")
        std_stand = cols[1].number_input("Standard Standing Uplift (p/day)", min_value=0.0, value=defaults.get('Standard_Standing', 0.0), key=f"std_stand_{year}_{i}")
        carbon_unit = cols[2].number_input("Carbon Unit Uplift (p/kWh)", min_value=0.0, value=defaults.get('Carbon_Unit', 0.0), key=f"carbon_unit_{year}_{i}")
        carbon_stand = cols[3].number_input("Carbon Standing Uplift (p/day)", min_value=0.0, value=defaults.get('Carbon_Standing', 0.0), key=f"carbon_stand_{year}_{i}")
        band_inputs.append({
            "Min": band["Min"], "Max": band["Max"],
            "Standard_Unit": std_unit, "Standard_Standing": std_stand,
            "Carbon_Unit": carbon_unit, "Carbon_Standing": carbon_stand
        })

    if cost_option == "Fixed £ per meter":
        year_inputs[year] = {
            "cost_method": "fixed",
            "fixed_cost": fixed_cost,
            "standing_pct": standing_pct,
            "unit_pct": unit_pct,
            "bands": band_inputs
        }
    else:
        year_inputs[year] = {
            "cost_method": "per_kwh",
            "ppkwh": ppkwh,
            "bands": band_inputs
        }

# Margin Template Save
if st.button("💾 Save Margin Template"):
    template = {
        "template_name": version_label,
        "bands": bands,
        "years": {str(y): year_inputs[y] for y in year_inputs}
    }
    json_data = json.dumps(template, indent=4)
    st.download_button(
        "⬇️ Download Margin Template",
        data=json_data,
        file_name=f"margin_template_{version_label}.json",
        mime="application/json"
    )

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = df.drop(columns=[col for col in ["Minimum_Credit_Score", "Maximum_Credit_Score"] if col in df.columns])

    def calculate_uplifts(row):
        duration = int(row["Contract_Duration"] / 12)
        year_config = year_inputs.get(duration)
        if not year_config:
            return pd.Series({"Uplift_Unit": 0, "Uplift_Standing": 0})

        cost_unit = cost_standing = 0
        if year_config["cost_method"] == "fixed":
            fixed = year_config["fixed_cost"] * 100
            cost_standing = (fixed * year_config["standing_pct"] / 100) / 365
            cost_unit = (fixed * year_config["unit_pct"] / 100) / max(row["Minimum_Annual_Consumption"],1)
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
    df_final["Total Annual Cost (£)"] = ((df_final["Standing Charge"] * 365) + (df_final["Unit Rate"] * df_final["Minimum_Annual_Consumption"])) / 100

    st.subheader("✅ Final Price List Preview")
    st.dataframe(df_final.head())

    broker_file_name = st.text_input("Broker File Name (without extension):", value="broker_pricelist")
    output_broker = io.BytesIO()
    with pd.ExcelWriter(output_broker, engine='xlsxwriter') as writer:
        df_final[[c for c in df_final.columns if c not in ["Uplift_Unit", "Uplift_Standing"]]].to_excel(writer, index=False, sheet_name='PriceList')

    st.download_button(
        "⬇️ Download Broker Price List",
        data=output_broker.getvalue(),
        file_name=f"{broker_file_name}_{version_label}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # Internal Audit Output
    st.subheader("🔍 Internal Audit Report")
    audit_file_name = st.text_input("Audit File Name (without extension):", value="internal_audit_report")
    output_audit = io.BytesIO()
    with pd.ExcelWriter(output_audit, engine='xlsxwriter') as writer:
        df_final.to_excel(writer, index=False, sheet_name='AuditData')

    st.download_button(
        "⬇️ Download Internal Audit Report",
        data=output_audit.getvalue(),
        file_name=f"{audit_file_name}_{version_label}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
