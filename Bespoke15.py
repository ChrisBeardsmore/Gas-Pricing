import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from st_aggrid import AgGrid, GridOptionsBuilder

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

st.title('Electricity Pricing Uplift Tool with AgGrid Input')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_name=sheet_option)

    if 'Standard Rate (p/kWh)' in df.columns and 'Unit Rate (p/kWh)' in df.columns:
        df['Standard Rate (p/kWh)'] = df.apply(
            lambda row: row['Standard Rate (p/kWh)'] if not pd.isna(row['Standard Rate (p/kWh)'])
            else row['Unit Rate (p/kWh)'], axis=1
        )

    df['S/C Uplift (p/day)'] = 0.000
    df['Unit Rate Uplift (p/kWh)'] = 0.000

    st.subheader("Enter Uplifts Per MPXN")
    uplift_data = df[['MPXN', 'S/C Uplift (p/day)', 'Unit Rate Uplift (p/kWh)']].drop_duplicates()

    gb = GridOptionsBuilder.from_dataframe(uplift_data)
    gb.configure_default_column(resizable=True, autoHeight=True)
    gb.configure_column('MPXN', pinned=True, width=150)
    gb.configure_column('S/C Uplift (p/day)', type=['numericColumn'], width=100)
    gb.configure_column('Unit Rate Uplift (p/kWh)', type=['numericColumn'], width=150)
    grid_options = gb.build()

    ag_grid = AgGrid(
        uplift_data,
        gridOptions=grid_options,
        editable=True,
        fit_columns_on_grid_load=True,
        height=400,
        reload_data=True
    )

    uplift_editor = ag_grid['data']

    if st.button("Apply Uplifts and Generate Broker Output"):
        df = df.merge(uplift_editor, on='MPXN', suffixes=('', '_input'))
        df['S/C Uplift (p/day)'] = df['S/C Uplift (p/day)_input']
        df['Unit Rate Uplift (p/kWh)'] = df['Unit Rate Uplift (p/kWh)_input']

        df['Standing Charge (p/day) Final'] = (df['Standing Charge (p/day)'] + df['S/C Uplift (p/day)']).round(3)
        df['Unit Rate (p/kWh) Final'] = (df['Standard Rate (p/kWh)'] + df['Unit Rate Uplift (p/kWh)']).round(3)

        df['Annual Dyce Price'] = df.apply(
            lambda row: calculate_annual_cost(
                row['Standing Charge (p/day) Final'],
                row['Unit Rate (p/kWh) Final'],
                row['EAC']
            ), axis=1
        )

        df['12m Dyce Price'] = df['Annual Dyce Price']
        df['24m Dyce Price'] = df['Annual Dyce Price'] * 2
        df['36m Dyce Price'] = df['Annual Dyce Price'] * 3

        broker_output = df[['MPXN', 'EAC', '12m Dyce Price', '24m Dyce Price', '36m Dyce Price']]

        st.success("Broker Output Generated (Dyce Prices for 12/24/36 months):")
        st.dataframe(broker_output, use_container_width=True)

        excel_data = convert_df(broker_output)
        st.download_button(
            label="Download Broker Output",
            data=excel_data,
            file_name='broker_output_dyce_prices.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
