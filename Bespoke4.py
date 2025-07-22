import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- Streamlit Config ---
st.set_page_config(layout="wide")

# --- Helper Functions ---
def load_supplier_data(uploaded_file, sheet_name):
    return pd.read_excel(uploaded_file, sheet_name=sheet_name)

def initialize_uplift_columns(df, rate_columns):
    for col in rate_columns:
        uplift_col = f'{col} Uplift'
        df[uplift_col] = 0.000
    return df

def apply_uplifts_per_row(df, rate_columns):
    for col in rate_columns:
        uplift_col = f'{col} Uplift'
        final_col = f'{col} Final'
        df[final_col] = (df[col].fillna(0) + df[uplift_col].fillna(0)).round(3)
    return df

@st.cache_data
def convert_df(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

# --- Streamlit App ---
st.title('Unified Electricity Pricing Uplift Tool (NHH & HH)')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_option)

    # Add common fields if missing for uniformity
    if 'Company Reg' not in df.columns:
        df['Company Reg'] = ''
    if 'kVa Capacity' not in df.columns:
        df['kVa Capacity'] = 0

    # Identify numeric rate columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Initialize uplift columns for all numeric fields
    df = initialize_uplift_columns(df, numeric_cols)

    st.subheader("Review & Enter Uplifts Per MPAN")
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("Apply Uplifts"):
        uplifted_df = apply_uplifts_per_row(edited_df.copy(), numeric_cols)

        # Optional: Calculate Total Annual Cost for HH (if kVa Capacity > 0)
        def calculate_total_cost(row):
            if row['kVa Capacity'] > 0:
                sc = row.get('Standing Charge (p/day) Final', 0)
                dr = row.get('Day Rate (p/kWh) Final', 0)
                nr = row.get('Night Rate (p/kWh) Final', 0)
                kva = row.get('KVA (p/kVa/day) Final', 0)
                mc = row.get('Metering Charge (p/day) Final', 0)
                eac = row.get('EAC (kWh)', 0)
                kva_capacity = row['kVa Capacity']

                annual_sc = sc * 365
                annual_mc = mc * 365
                annual_kva = kva * kva_capacity * 365
                annual_unit = eac * ((dr + nr) / 2)  # simplistic average rate

                return round(annual_sc + annual_mc + annual_kva + annual_unit, 2)
            return np.nan

        uplifted_df['Total Annual Cost'] = uplifted_df.apply(calculate_total_cost, axis=1)

        st.success("Uplifts Applied with Final Rates:")
        st.dataframe(uplifted_df)

        excel_data = convert_df(uplifted_df)
        st.download_button(
            label="Download Unified Uplifted Pricing",
            data=excel_data,
            file_name='unified_uplifted_pricing.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
