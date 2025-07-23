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
    return round((sc * 365) + (unit_rate * eac), 2)

@st.cache_data
def convert_df(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

st.title('Electricity Pricing Uplift Tool')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_name=sheet_option)

    if 'Standard Rate (p/kWh)' in df.columns and 'Unit Rate (p/kWh)' in df.columns:
        df['Standard Rate (p/kWh)'] = df.apply(
            lambda row: row['Standard Rate (p/kWh)'] if not pd.isna(row['Standard Rate (p/kWh)'])
            else row['Unit Rate (p/kWh)'], axis=1
        )

    if 'Contract Length' not in df.columns:
        st.error("Missing 'Contract Length' column in the uploaded file.")
        st.stop()

    pivoted = df.pivot_table(
        index=['MPXN', 'EAC'],
        columns='Contract Length',
        values=['Standing Charge (p/day)', 'Standard Rate (p/kWh)'],
        aggfunc='first'
    )

    pivoted.columns = [f"{col[0]} {col[1]}m" for col in pivoted.columns]
    pivoted = pivoted.reset_index()

    # Add uplift input fields
    for term in [12, 24, 36]:
        pivoted[f"S/C Uplift {term}m"] = 0.000
        pivoted[f"Unit Rate Uplift {term}m"] = 0.000

    st.subheader("Enter Uplifts Per MPXN and Term")
    gb = GridOptionsBuilder.from_dataframe(pivoted)
    gb.configure_default_column(resizable=True, autoHeight=True)
    gb.configure_column("MPXN", pinned=True, width=140)

    for col in pivoted.columns:
        if col.startswith("S/C Uplift") or col.startswith("Unit Rate Uplift"):
            gb.configure_column(col, type=["numericColumn"], width=120)
        elif col.startswith("Standing") or col.startswith("Standard"):
            gb.configure_column(col, type=["numericColumn"], width=130)

    grid_options = gb.build()

    ag_grid = AgGrid(
        pivoted,
        gridOptions=grid_options,
        editable=True,
        height=500,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True
    )

    edited_df = ag_grid['data']

    if st.button("Generate Broker Output"):
        for term in [12, 24, 36]:
            sc_final = edited_df[f"Standing Charge (p/day) {term}m"] + edited_df[f"S/C Uplift {term}m"]
            unit_final = edited_df[f"Standard Rate (p/kWh) {term}m"] + edited_df[f"Unit Rate Uplift {term}m"]
            edited_df[f"Dyce Price {term}m"] = [
                calculate_annual_cost(sc, unit, eac)
                for sc, unit, eac in zip(sc_final, unit_final, edited_df['EAC'])
            ]

        broker_output = edited_df[['MPXN', 'EAC', 'Dyce Price 12m', 'Dyce Price 24m', 'Dyce Price 36m']]

        st.success("Broker Output Generated:")
        st.dataframe(broker_output, use_container_width=True)

        excel_data = convert_df(broker_output)
        st.download_button(
            label="Download Broker Output",
            data=excel_data,
            file_name='broker_output_dyce_prices.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
