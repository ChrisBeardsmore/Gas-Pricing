import streamlit as st
import pandas as pd

st.set_page_config(page_title="Tariff Selector", layout="wide")
st.title("Tariff Matrix Selector")

# Upload flat file
uploaded_file = st.file_uploader("Upload Flat File (CSV)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Ensure we can display ContractDuration and all relevant fields
    st.subheader("Available Tariffs")

    # Add selection checkboxes for each row
    df["Select"] = False
    selection = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Select": st.column_config.CheckboxColumn(required=False),
        },
        hide_index=True,
    )

    # Filter selected rows for processing
    selected_rows = selection[selection["Select"] == True]

    if not selected_rows.empty:
        st.subheader("Selected Tariffs")
        st.dataframe(selected_rows, use_container_width=True)

        # Optional download or process action
        st.download_button(
            "Download Selected Tariffs as CSV",
            selected_rows.to_csv(index=False).encode("utf-8"),
            file_name="selected_tariffs.csv",
            mime="text/csv"
        )
else:
    st.info("Please upload a flat file to begin.")
