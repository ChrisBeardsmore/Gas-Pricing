import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# --- Streamlit Config ---
st.set_page_config(layout="wide")

# --- Helper Functions ---
def load_supplier_data(uploaded_file, sheet_name):
    return pd.read_excel(uploaded_file, sheet_name=sheet_name)

def calculate_annual_cost(sc, unit_rate, eac):
    annual_sc = sc * 365
    annual_unit = unit_rate * eac
    return round(annual_sc + annual_unit, 2)

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
    df = load_supplier_data(uploaded_file, sheet_name=sheet_option)

    if 'Standard Rate (p/kWh)' in df.columns and 'Unit Rate (p/kWh)' in df.columns:
        df['Standard Rate (p/kWh)'] = df.apply(
            lambda row: row['Standard Rate (p/kWh)'] if not pd.isna(row['Standard Rate (p/kWh)'])
            else row['Unit Rate (p/kWh)'], axis=1
        )

    # Prepare Uplift Inputs
    st.subheader("Enter Uplifts Per MPXN")
    df['S/C Uplift (p/day)'] = 0.000
    df['Unit Rate Uplift (p/kWh)'] = 0.000

    required_columns = ['MPXN', 'Contract Length', 'Standing Charge (p/day)', 'Standard Rate (p/kWh)', 'EAC (kWh)',
                        'S/C Uplift (p/day)', 'Unit Rate Uplift (p/kWh)']

    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(f"Missing columns in input file: {', '.join(missing_cols)}")
    else:
        uplift_editor = st.data_editor(df[['MPXN', 'S/C Uplift (p/day)', 'Unit Rate Uplift (p/kWh)']].drop_duplicates(),
                                       num_rows='dynamic', use_container_width=True)

        if st.button("Apply Uplifts and Generate Broker Output"):
            df = df.merge(uplift_editor, on='MPXN', suffixes=('', '_input'))
            df['S/C Uplift (p/day)'] = df['S/C Uplift (p/day)_input']
            df['Unit Rate Uplift (p/kWh)'] = df['Unit Rate Uplift (p/kWh)_input']

            df['Standing Charge (p/day) Final'] = (df['Standing Charge (p/day)'] + df['S/C Uplift (p/day)']).round(3)
            df['Unit Rate (p/kWh) Final'] = (df['Standard Rate (p/kWh)'] + df['Unit Rate Uplift (p/kWh)']).round(3)

            df['Dyce Price'] = df.apply(
                lambda row: calculate_annual_cost(
                    row['Standing Charge (p/day) Final'],
                    row['Unit Rate (p/kWh) Final'],
                    row['EAC (kWh)']
                ), axis=1
            )

            pivot_df = df.pivot_table(
                index=['Company Name', 'Company Reg', 'MPXN', 'Standard/Green', 'Contract Start Date', 'EAC (kWh)'],
                columns='Contract Length',
                values='Dyce Price'
            ).reset_index()

            pivot_df.columns.name = None  # remove hierarchy name

            # Rename contract length columns to include 'Dyce Price'
            pivot_df = pivot_df.rename(columns={
                12: '12m Dyce Price',
                24: '24m Dyce Price',
                36: '36m Dyce Price'
            })

            st.success("Broker Output Generated (Dyce Prices Only):")
            st.dataframe(pivot_df, use_container_width=True)

            excel_data = convert_df(pivot_df)
            st.download_button(
                label="Download Broker Output",
                data=excel_data,
                file_name='broker_output_dyce_prices.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
