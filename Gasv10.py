import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Energy Pricing Uplift Tool", layout="wide")
st.title("🔹 Energy Pricing Uplift Tool")
pip install XlsxWriter
# Upload CSV
uploaded_file = st.file_uploader("Upload your flat file CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip().replace(" ", "").lower() for col in df.columns]  # Normalize

    st.success("✅ File loaded successfully")
    st.write("Columns in your file:", list(df.columns))
    st.dataframe(df.head())

    st.markdown("---")
    st.subheader("Step 1 – Enter Uplifts (p / kWh and p / day)")

    default_bands = [
        {"Min": 0, "Max": 999},
        {"Min": 1000, "Max": 24999},
        {"Min": 25000, "Max": 49999},
        {"Min": 50000, "Max": 73199},
        {"Min": 73200, "Max": 124999},
        {"Min": 125000, "Max": 292999},
        {"Min": 293000, "Max": 731999},
    ]

    band_inputs = []
    with st.expander("Click to edit bands", expanded=True):
        for i, band in enumerate(default_bands):
            st.markdown(f"**Band {i+1}: {band['Min']} - {band['Max']} kWh**")
            cols = st.columns(6)
            entry = {
                "Min": band["Min"],
                "Max": band["Max"],
                "1yr_unit_noncarbon": cols[0].number_input(f"1yr Unit (NC)", value=1.0, key=f"1u_nc_{i}"),
                "1yr_standing_noncarbon": cols[1].number_input(f"1yr Stand (NC)", value=1.0, key=f"1s_nc_{i}"),
                "2yr_unit_noncarbon": cols[2].number_input(f"2yr Unit (NC)", value=1.0, key=f"2u_nc_{i}"),
                "2yr_standing_noncarbon": cols[3].number_input(f"2yr Stand (NC)", value=1.0, key=f"2s_nc_{i}"),
                "3yr_unit_noncarbon": cols[4].number_input(f"3yr Unit (NC)", value=1.0, key=f"3u_nc_{i}"),
                "3yr_standing_noncarbon": cols[5].number_input(f"3yr Stand (NC)", value=1.0, key=f"3s_nc_{i}")
            }
            entry["1yr_unit_carbon"] = cols[0].number_input(f"1yr Unit (C)", value=1.5, key=f"1u_c_{i}")
            entry["1yr_standing_carbon"] = cols[1].number_input(f"1yr Stand (C)", value=1.5, key=f"1s_c_{i}")
            entry["2yr_unit_carbon"] = cols[2].number_input(f"2yr Unit (C)", value=1.5, key=f"2u_c_{i}")
            entry["2yr_standing_carbon"] = cols[3].number_input(f"2yr Stand (C)", value=1.5, key=f"2s_c_{i}")
            entry["3yr_unit_carbon"] = cols[4].number_input(f"3yr Unit (C)", value=1.5, key=f"3u_c_{i}")
            entry["3yr_standing_carbon"] = cols[5].number_input(f"3yr Stand (C)", value=1.5, key=f"3s_c_{i}")

            band_inputs.append(entry)

    annual_consumption = st.number_input("Annual Consumption (kWh)", min_value=1, value=20000)

    def get_band_uplift(row):
        # Find matching band
        consumption = row.get("minimumannualconsumption", 0)
        band = next((b for b in band_inputs if b["Min"] <= consumption <= b["Max"]), band_inputs[-1])

        # Contract length
        try:
            contract_length = int(row.get("contractlength", 1))
        except:
            contract_length = 1
        if contract_length not in [1, 2, 3]:
            contract_length = 1

        # Carbon offset
        carbon_raw = str(row.get("carbonoffset", "")).strip().lower()
        carbon = carbon_raw in ["yes", "y", "true", "1"]

        if carbon:
            unit = band[f"{contract_length}yr_unit_carbon"]
            standing = band[f"{contract_length}yr_standing_carbon"]
        else:
            unit = band[f"{contract_length}yr_unit_noncarbon"]
            standing = band[f"{contract_length}yr_standing_noncarbon"]

        return pd.Series({
            "Uplift_Unit": unit,
            "Uplift_Standing": standing
        })

    # Apply uplift logic
    uplift_df = df.apply(get_band_uplift, axis=1)
    df_final = pd.concat([df, uplift_df], axis=1)

    df_final["UnitRate_Uplifted"] = df_final["unitrate"] + df_final["Uplift_Unit"]
    df_final["StandingCharge_Uplifted"] = df_final["standingcharge"] + df_final["Uplift_Standing"]

    df_final["TotalAnnualCost"] = (
        (df_final["StandingCharge_Uplifted"] * 365) +
        (df_final["UnitRate_Uplifted"] * annual_consumption)
    ) / 100

    st.subheader("✅ Uplifted Price List Preview")
    st.dataframe(df_final[[
        "UnitRate_Uplifted", "StandingCharge_Uplifted", "TotalAnnualCost"
    ]].head())

    # Prepare Excel output
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_final_out = df_final[[
            "UnitRate_Uplifted", "StandingCharge_Uplifted", "TotalAnnualCost"
        ]]
        df_final_out.to_excel(writer, index=False, sheet_name="PriceList")

    st.download_button(
        "⬇️ Download Broker Price List",
        data=output.getvalue(),
        file_name="broker_pricelist.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
