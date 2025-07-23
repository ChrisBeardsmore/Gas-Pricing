import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
from dateutil.relativedelta import relativedelta
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

def calculate_months(start, end):
    return (end.year - start.year) * 12 + (end.month - start.month)

st.title('Electricity Pricing Uplift Tool – Broker Output Format')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_name=sheet_option)

    # Convert date columns
    df['CSD'] = pd.to_datetime(df['CSD'], dayfirst=True)
    df['CED'] = pd.to_datetime(df['CED'], dayfirst=True)

    # Derive contract length in months
    df['Contract Length'] = df.apply(lambda row: calculate_months(row['CSD'], row['CED']), axis=1)

    # Only keep relevant terms
    df = df[df['Contract Length'].isin([12, 24, 36])]

    # Create pivot table structure per MPXN
    id_cols = ['Company Name', 'Company Reg', 'MPXN', 'Standard/Green', 'CSD', 'EAC', 'kVa Capacity']
    df['Contract Length'] = df['Contract Length'].astype(str)

    reshaped = df.pivot(index='MPXN', columns='Contract Length')
    reshaped.columns = ['{} {}m'.format(col[0], col[1]) for col in reshaped.columns]
    reshaped.reset_index(inplace=True)

    # Add back identifier fields
    id_values = df.groupby('MPXN')[id_cols].first().reset_index()
    full_df = pd.merge(id_values, reshaped, on='MPXN', how='left')

    # Add blank uplift columns
    for term in ['12', '24', '36']:
        full_df[f'S/C Uplift {term}m'] = 0.000
        full_df[f'Unit Rate Uplift {term}m'] = 0.000

    # Configure AgGrid
    st.subheader("Enter Uplifts Per MPXN & Contract Length")
    gb = GridOptionsBuilder.from_dataframe(full_df)
    gb.configure_default_column(resizable=True, autoHeight=True)

    for term in ['12', '24', '36']:
        gb.configure_column(f'S/C Uplift {term}m', type=['numericColumn'], width=100)
        gb.configure_column(f'Unit Rate Uplift {term}m', type=['numericColumn'], width=150)

    grid_options = gb.build()
    ag_grid = AgGrid(
        full_df,
        gridOptions=grid_options,
        editable=True,
        fit_columns_on_grid_load=True,
        height=500,
        reload_data=True
    )

    uplifted_df = ag_grid['data']

    if st.button("Generate Broker Output"):
        output_rows = []

        for _, row in uplifted_df.iterrows():
            base = {
                'Company Name': row['Company Name'],
                'Company Reg': row['Company Reg'],
                'MPXN': row['MPXN'],
                'Standard/Green': row['Standard/Green'],
                'Contract Start Date': row['CSD'],
                'EAC (kWh)': row['EAC'],
                'kVa Capacity': row['kVa Capacity']
            }

            for term in ['12', '24', '36']:
                sc_col = f'Standing Charge (p/day) {term}m'
                ur_col = f'Standard Rate (p/kWh) {term}m'

                sc_uplift = row.get(f'S/C Uplift {term}m', 0)
                ur_uplift = row.get(f'Unit Rate Uplift {term}m', 0)

                try:
                    sc = row.get(sc_col, 0) + sc_uplift
                    ur = row.get(ur_col, 0) + ur_uplift
                except:
                    sc, ur = 0, 0

                total_cost = calculate_annual_cost(sc, ur, row['EAC'])

                base.update({
                    f'Standing Charge {term}m (p/day)': round(sc, 3),
                    f'Unit Rate {term}m (p/kWh)': round(ur, 3),
                    f'Annual Cost {term}m (£)': total_cost
                })

            output_rows.append(base)

        final_output = pd.DataFrame(output_rows)
        st.success("Broker Output Generated")
        st.dataframe(final_output, use_container_width=True)

        excel_data = convert_df(final_output)
        st.download_button(
            label="Download Broker Output",
            data=excel_data,
            file_name='broker_output_dyce_prices.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
