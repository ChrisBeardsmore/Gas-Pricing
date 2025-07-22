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
st.title('Electricity Pricing Uplift Tool')

uploaded_file = st.file_uploader("Upload Supplier Tender File (Excel)", type=["xlsx"])

if uploaded_file:
    sheet_option = st.selectbox("Select Pricing Type:", ('Standard', 'Green'))
    df = load_supplier_data(uploaded_file, sheet_option)

    # Identify numeric rate columns for potential uplift
    rate_columns = [col for col in df.columns if df[col].dtype in [np.float64, np.int64]]

    # Initialize uplift columns
    df = initialize_uplift_columns(df, rate_columns)

    st.subheader("Review & Enter Uplifts")
    edited_df = st.data_editor(df, num_rows="dynamic")

    if st.button("Apply Uplifts"):
        uplifted_df = apply_uplifts_per_row(edited_df.copy(), rate_columns)
        st.success("Uplifts Applied to All Rate Columns:")
        st.dataframe(uplifted_df)

        excel_data = convert_df(uplifted_df)
        st.download_button(
            label="Download Uplifted Pricing",
            data=excel_data,
            file_name='uplifted_pricing.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
