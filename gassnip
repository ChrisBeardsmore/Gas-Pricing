# Gas Direct V3.7 (Input Grid Only – Scrollable Site Inputs)
# ---------------------------------------------------------------------------------
# Replaces previous column layout with a scrollable editable input table
# No pricing or output logic yet — just the input capture and layout
# ---------------------------------------------------------------------------------

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Gas Multi-tool", layout="wide")
st.title("Gas Multi-tool (12/24/36 Month Quote Builder)")

st.subheader("Multi-site Input (Editable Grid)")

# Define empty input table for 10 sites
initial_data = pd.DataFrame({
    "Site Name": ["" for _ in range(10)],
    "Postcode": ["" for _ in range(10)],
    "Annual kWh": [0 for _ in range(10)],
    "Uplift Unit (12m)": [0.0 for _ in range(10)],
    "Uplift SC (12m)": [0.0 for _ in range(10)],
    "Uplift Unit (24m)": [0.0 for _ in range(10)],
    "Uplift SC (24m)": [0.0 for _ in range(10)],
    "Uplift Unit (36m)": [0.0 for _ in range(10)],
    "Uplift SC (36m)": [0.0 for _ in range(10)],
})

edited_data = st.data_editor(
    initial_data,
    use_container_width=True,
    num_rows="fixed",
    hide_index=True,
    key="editable_site_inputs"
)

st.markdown("---")
st.write("✅ Above: Editable input table for 10 sites.\nHorizontal scroll should now be working.\nNext step: Add postcode matching, pricing lookup, and TAC calc.")
