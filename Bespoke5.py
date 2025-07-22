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

def calculate_annual_cost(sc, dr, nr, kva, mc, eac, kva_capacity):
    annual_sc = sc * 365
    annual_mc = mc * 365
    annual_kva = kva * kva_capacity * 365
    average_unit_rate = (dr + nr) / 2
    annual_unit = eac * average_unit_rate
    return round(annual_sc + annual_mc + annual_kva + annual_unit, 2)

# --- Streamlit App ---
st.title('Unified Electricity Pricing Uplift Tool (NHH & HH)')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_name=sheet_option)

    # Move Unit Rate to Standard Rate if populated
    if 'Standard Rate (p/kWh)' in df.columns and 'Unit Rate (p/kWh)' in df.columns:
        df['Standard Rate (p/kWh)'] = df.apply(
            lambda row: row['Standard Rate (p/kWh)'] if not pd.isna(row['Standard Rate (p/kWh)'])
            else row['Unit Rate (p/kWh)'], axis=1
        )

    # Drop Day 1 to Day 5 Rate columns if they exist
    day_rate_cols = [
        'Day 1 Rate (p/kWh)', 'Day 2 Rate (p/kWh)', 'Day 3 Rate (p/kWh)',
        'Day 4 Rate (p/kWh)', 'Day 5 Rate (p/kWh)'
    ]
    df.drop(columns=[col for col in day_rate_cols if col in df.columns], inplace=True)

    # Add common fields if missing for uniformity
    for col in ['Company Reg', 'kVa Capacity']:
        if col not in df.columns:
            df[col] = '' if col == 'Company Reg' else 0

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    df = initialize_uplift_columns(df, numeric_cols)

    st.subheader("Review & Enter Uplifts Per MPAN")
    uplift_cols = [col for col in df.columns if 'Uplift' in col]

    styled_df = df.style.applymap(
        lambda v: 'background-color: white' if isinstance(v, (int, float)) else '',
        subset=uplift_cols
    )

    st.dataframe(styled_df)

    if st.button("Apply Uplifts"):
        uplifted_df = apply_uplifts_per_row(df.copy(), numeric_cols)

        cost_columns = ['Standing Charge (p/day)', 'Day Rate (p/kWh)', 'Night Rate (p/kWh)',
                        'KVA (p/kVa/day)', 'Metering Charge (p/day)']

        for term in ['12m', '24m', '36m']:
            uplifted_df[f'{term} Base Cost'] = uplifted_df.apply(
                lambda row: calculate_annual_cost(
                    row.get('Standing Charge (p/day)', 0),
                    row.get('Day Rate (p/kWh)', 0),
                    row.get('Night Rate (p/kWh)', 0),
                    row.get('KVA (p/kVa/day)', 0),
                    row.get('Metering Charge (p/day)', 0),
                    row.get('EAC (kWh)', 0),
                    row.get('kVa Capacity', 0)
                ), axis=1
            )

            uplifted_df[f'{term} Uplifted Cost'] = uplifted_df.apply(
                lambda row: calculate_annual_cost(
                    row.get('Standing Charge (p/day) Final', 0),
                    row.get('Day Rate (p/kWh) Final', 0),
                    row.get('Night Rate (p/kWh) Final', 0),
                    row.get('KVA (p/kVa/day) Final', 0),
                    row.get('Metering Charge (p/day) Final', 0),
                    row.get('EAC (kWh)', 0),
                    row.get('kVa Capacity', 0)
                ), axis=1
            )

        st.success("Uplifts Applied with Base and Uplifted Costs:")
        st.dataframe(uplifted_df)

        excel_data = convert_df(uplifted_df)
        st.download_button(
            label="Download Unified Uplifted Pricing",
            data=excel_data,
            file_name='unified_uplifted_pricing.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
