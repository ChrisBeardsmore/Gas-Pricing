import streamlit as st
import pandas as pd
import numpy as np

# --- Helper Functions ---
def load_supplier_data(uploaded_file, sheet_name):
    return pd.read_excel(uploaded_file, sheet_name=sheet_name)

def apply_uplifts(df, uplifts):
    rate_columns = {
        'Standing Charge (p/day)': 'standing_charge',
        'All Year - Day Rate (p/kWh)': 'day_rate',
        'All Year - Night Rate (p/kWh)': 'night_rate'
    }

    for col, uplift_key in rate_columns.items():
        if col in df.columns:
            df[f'{col} (Uplifted)'] = (df[col].fillna(0) + uplifts.get(uplift_key, 0)).round(3)

    return df

# --- Streamlit App ---
st.title('Electricity Pricing Uplift Tool')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_option)

    st.subheader("Uplift Inputs (3 Decimal Places)")
    uplift_sc = st.number_input("Standing Charge uplift (p/day)", min_value=0.000, format="%.3f")
    uplift_day = st.number_input("Day Rate uplift (p/kWh)", min_value=0.000, format="%.3f")
    uplift_night = st.number_input("Night Rate uplift (p/kWh)", min_value=0.000, format="%.3f")

    uplifts = {
        'standing_charge': uplift_sc,
        'day_rate': uplift_day,
        'night_rate': uplift_night
    }

    if st.button("Apply Uplifts"):
        uplifted_df = apply_uplifts(df.copy(), uplifts)
        st.success("Uplifts Applied:")
        st.dataframe(uplifted_df)

        @st.cache_data
        def convert_df(df):
            return df.to_excel(index=False, engine='xlsxwriter')

        excel_data = convert_df(uplifted_df)
        st.download_button(
            label="Download Uplifted Pricing",
            data=excel_data,
            file_name='uplifted_pricing.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
