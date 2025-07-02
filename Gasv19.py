import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Energy Pricing Uplift Tool", layout="wide")
st.title("🔹 Energy Pricing Uplift Tool")

uploaded_file = st.file_uploader("Upload your pricing CSV file:", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = [col.strip().replace(" ", "").lower() for col in df.columns]
    df = df.loc[:, ~df.columns.str.contains("^unnamed")]

    st.success("✅ File loaded successfully")

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
    with st.expander("Step 1 – Uplifts per Consumption Band", expanded=True):
        for i, band in enumerate(default_bands):
            st.markdown(f"**Band {i+1}: {band['Min']} - {band['Max']} kWh**")
            cols = st.columns(6)
            entry = {
                "Min": band["Min"],
                "Max": band["Max"],
                "1yr_unit_noncarbon": cols[0].number_input("1yr Unit NC", value=1.0, key=f"1u_nc_{i}"),
                "1yr_standing_noncarbon": cols[1].number_input("1yr Stand NC", value=1.0, key=f"1s_nc_{i}"),
                "2yr_unit_noncarbon": cols[2].number_input("2yr Unit NC", value=1.0, key=f"2u_nc_{i}"),
                "2yr_standing_noncarbon": cols[3].number_input("2yr Stand NC", value=1.0, key=f"2s_nc_{i}"),
                "3yr_unit_noncarbon": cols[4].number_input("3yr Unit NC", value=1.0, key=f"3u_nc_{i}"),
                "3yr_standing_noncarbon": cols[5].number_input("3yr Stand NC", value=1.0, key=f"3s_nc_{i}"),
                "1yr_unit_carbon": cols[0].number_input("1yr Unit C", value=1.5, key=f"1u_c_{i}"),
                "1yr_standing_carbon": cols[1].number_input("1yr Stand C", value=1.5, key=f"1s_c_{i}"),
                "2yr_unit_carbon": cols[2].number_input("2yr Unit C", value=1.5, key=f"2u_c_{i}"),
                "2yr_standing_carbon": cols[3].number_input("2yr Stand C", value=1.5, key=f"2s_c_{i}"),
                "3yr_unit_carbon": cols[4].number_input("3yr Unit C", value=1.5, key=f"3u_c_{i}"),
                "3yr_standing_carbon": cols[5].number_input("3yr Stand C", value=1.5, key=f"3s_c_{i}")
            }
            band_inputs.append(entry)

    annual_consumption = st.number_input("Annual Consumption (kWh)", min_value=1, value=20000)

    def get_band_uplift(row):
        consumption = row.get("minimumannualconsumption", 0)
        band = next((b for b in band_inputs if b["Min"] <= consumption <= b["Max"]), band_inputs[-1])

        try:
            contract_length = int(row.get("contractduration", 1))
        except:
            contract_length = 1
        if contract_length not in [1, 2, 3]:
            contract_length = 1

        carbon_raw = str(row.get("carbonoffset", "")).strip().lower()
        carbon = carbon_raw in ["yes", "y", "true", "1"]

        if carbon:
            unit = band[f"{contract_length}yr_unit_carbon"]
            standing = band[f"{contract_length}yr_standing_carbon"]
        else:
            unit = band[f"{contract_length}yr_unit_noncarbon"]
            standing = band[f"{contract_length}yr_standing_noncarbon"]

        return pd.Series({
            "uplift_unit": unit,
            "uplift_standing": standing
        })

    uplift_df = df.apply(get_band_uplift, axis=1)
    df_final = pd.concat([df, uplift_df], axis=1)

    df_final["Unit Rate"] = df_final["unitrate"] + df_final["uplift_unit"]
    df_final["Standing Charge"] = (df_final["standingcharge"] + df_final["uplift_standing"]) * 100  # Pence per day

    df_final["Total Annual Cost"] = (
        (df_final["Standing Charge"] / 100 * 365) +
        (df_final["Unit Rate"] * annual_consumption)
    ) / 100

    st.subheader("✅ Uplifted Pricing Preview")
    # You can change this to df_final if you prefer all columns in preview
    st.dataframe(df_final[["Unit Rate", "Standing Charge", "Total Annual Cost"]].head())

    # Create clean export DataFrame
    export_cols = [c for c in df.columns if not c.startswith("unnamed")]
    export_cols += ["Unit Rate", "Standing Charge", "Total Annual Cost"]

    df_export = df_final[export_cols].drop(
        columns=["unitrate", "standingcharge", "uplift_unit", "uplift_standing"],
        errors="ignore"
    )

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, index=False, sheet_name="UpliftedPrices")

    st.download_button(
        "⬇️ Download Excel Pricing",
        data=output.getvalue(),
        file_name="uplifted_pricing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
