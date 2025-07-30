Flat File Structure – Yu Energy Gas Pricing

This document outlines the required structure, columns, and formatting of the Yu Energy gas pricing flat file used within the Dyce Energy uplift tool.

📦 File Format

Accepted type: Excel (.xlsx)

Sheet structure: Single sheet

Column names must match exactly (case-sensitive)

📋 Required Columns

Column Name

Description

LDZ

Local Distribution Zone (e.g., SC, NE, WM)

Contract_Duration

Contract term in months (e.g., 12, 24, 36)

Minimum_Annual_Consumption

Lower limit of the annual consumption band (kWh)

Maximum_Annual_Consumption

Upper limit of the annual consumption band (kWh)

Carbon_Offset

Boolean flag – TRUE if carbon offset included, else FALSE

Standing_Charge

Daily standing charge in pence (e.g., 55.00 for 55p/day)

Unit_Rate

Commodity unit rate in pence per kWh (e.g., 7.250 for 7.250p/kWh)

🧹 Pre-processing Applied

The tool applies the following clean-up steps:

LDZ column uppercased and stripped of spaces

Contract_Duration converted to integer

Minimum_Annual_Consumption and Maximum_Annual_Consumption converted to numeric (float)

🧪 Matching Logic in Uplift Tool

When pricing a site, the tool selects matching rows from the flat file using:

Exact match on LDZ

Exact match on Contract_Duration

Banding match: Minimum_Annual_Consumption ≤ kWh ≤ Maximum_Annual_Consumption

Match on Carbon_Offset value (based on product type selected)

From these matches, it selects the row with the lowest Unit_Rate.

⚠️ Common Issues

Misnamed or misspelled columns (e.g., UnitRate instead of Unit_Rate)

LDZ entries with trailing spaces or inconsistent casing

Missing values in consumption band fields (must not be blank)

✅ Example Row

LDZ

Contract_Duration

Minimum_Annual_Consumption

Maximum_Annual_Consumption

Carbon_Offset

Standing_Charge

Unit_Rate

SC

12

0

73000

FALSE

48.00

6.450

🔄 Update Procedure

If a new flat file format is received:

Check for new columns or renamed fields

Update the parser logic in load_flat_file() accordingly

Document changes in this file
