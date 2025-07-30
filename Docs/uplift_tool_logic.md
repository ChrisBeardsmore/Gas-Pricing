Uplift Tool Logic (Gas Direct Final 6)

This document outlines the logic and structure behind the Gas Direct uplift tool ("Final 6" version) used for multi-site gas pricing at Dyce Energy.

🔧 Purpose

To create custom gas quotes for customers by applying standing charge and unit rate uplifts to base prices from the Yu Energy flat file, filtered by LDZ, consumption band, and contract duration.

📥 Inputs

1. Supplier Flat File Upload

Source: Yu Energy

Required columns: LDZ, Contract_Duration, Minimum_Annual_Consumption, Maximum_Annual_Consumption, Carbon_Offset, Standing_Charge, Unit_Rate

2. LDZ Matching File

Maps postcode prefixes to LDZ

Cleaned to remove spaces and enforce uppercase

3. User Inputs via Grid

Editable fields for each site:

Site Name

Post Code

Annual KWH

Standing Charge Uplift (12m / 24m / 36m)

Unit Rate Uplift (12m / 24m / 36m)

🔄 Processing Logic

1. Postcode to LDZ Mapping

Matches using decreasing prefix length (7 to 3 characters)

Returns first match from LDZ file

2. Flat File Filtering

For each site and duration:

Match LDZ

Contract duration (exact match)

Minimum ≤ Annual KWH ≤ Maximum

Carbon Offset flag (based on product type)

3. Base Rates Selection

Among matches, select the row with the lowest unit rate

4. Apply Uplifts

Enforce limits: SC uplift ≤ 100p/day, Unit uplift ≤ 3.000p/kWh

Calculate:

Sell SC = Base SC + Uplift SC

Sell Unit = Base Unit + Uplift Unit

TAC = ((Sell Unit * kWh) + (Sell SC * 365)) / 100

📊 Outputs

Customer-Facing Table:

Site Name

Post Code

Annual KWH

Sell Standing Charge (12m / 24m / 36m)

Sell Unit Rate (12m / 24m / 36m)

TAC £(12m / 24m / 36m)

Summary:

Total TAC across all sites and durations

Excel export with just the sell rates and TACs

🧱 Additional Notes

Image logo (DYCE-DARK BG.png) displayed if available

Grid limited to 10 rows for now

st.data_editor used for intuitive editing

📦 Future Ideas

Save/load previous quotes

Add margin back-calc based on target TAC

Add visual charts for comparison (e.g., uplift impact)

Add uplift tool logic documentation
