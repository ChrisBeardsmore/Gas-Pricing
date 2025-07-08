st.subheader("Customer Quoting Tool")

postcode_input = st.text_input("Enter customer postcode")
consumption_input = st.number_input("Enter annual consumption (kWh)", min_value=0)

# Normalize postcode
if postcode_input:
    clean_postcode = postcode_input.replace(" ", "").upper()
    postcode_match = ldz_df[ldz_df["Postcode"] == clean_postcode]

    if postcode_match.empty:
        st.error("Postcode not found.")
    elif consumption_input > 0:
        # Extract LDZ & Exit Zone
        ldz = postcode_match.iloc[0]["LDZ"]
        exit_zone = postcode_match.iloc[0]["Exit Zone"]

        st.success(f"LDZ: {ldz} | Exit Zone: {exit_zone}")

        # Filter the supplier flat file based on LDZ, Exit Zone, and consumption
        filtered = df[
            (df["LDZ"] == ldz) &
            (df["Exit_Zone"] == exit_zone) &
            (df["Minimum_Annual_Consumption"] <= consumption_input) &
            (df["Maximum_Annual_Consumption"] >= consumption_input)
        ]

        if not filtered.empty:
            st.subheader("Matching Tariffs")
            st.dataframe(filtered[["Contract_Duration", "Product_Name", "Standing_Charge", "Unit_Rate"]])
        else:
            st.warning("No matching tariffs found for that consumption range."
