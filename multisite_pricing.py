import pandas as pd
from datetime import datetime

# ---------------------------------------------------------
# Load Excel Sheets
# ---------------------------------------------------------
file_path = "Gas Multisite Tool Acquisitions MASTER.xlsx"

# Load Flat File
flat_df = pd.read_excel(file_path, sheet_name="Flat File")

# Load Post Code Mapping
postcode_df = pd.read_excel(file_path, sheet_name="Post Code")

# Load Matrix Input
matrix_df = pd.read_excel(file_path, sheet_name="Matrix")

# ---------------------------------------------------------
# Matrix Info (Validation Constants)
# ---------------------------------------------------------
MATRIX_VALID_FROM = datetime.strptime("29/05/2024", "%d/%m/%Y")
EARLIEST_START_DATE = datetime.strptime("05/03/2024", "%d/%m/%Y")
LATEST_START_MONTH = datetime.strptime("01/02/2025", "%d/%m/%Y")  # assuming Feb-25 = 01/02/2025
MIN_AQ = 1000
MAX_AQ = 731999

# ---------------------------------------------------------
# Helper Function: Parse Start Month to date
# ---------------------------------------------------------
def parse_start_month(month_str):
    try:
        return datetime.strptime(month_str, "%b-%y")
    except Exception:
        return None

# ---------------------------------------------------------
# Process Each Site
# ---------------------------------------------------------
results = []

for idx, row in matrix_df.iterrows():
    mprn = row["MPRN"]
    postcode = row["Postcode"]
    aq = row["AQ (kWh)"]
    start_month_str = str(row["Start Month"])

    # Validate AQ
    if not (MIN_AQ <= aq <= MAX_AQ):
        print(f"Row {idx}: AQ {aq} out of range.")
        continue

    # Validate Start Month
    start_month = parse_start_month(start_month_str)
    if not start_month:
        print(f"Row {idx}: Invalid Start Month format: {start_month_str}")
        continue

    if not (EARLIEST_START_DATE <= start_month <= LATEST_START_MONTH):
        print(f"Row {idx}: Start Month {start_month_str} out of range.")
        continue

    # Lookup LDZ/Exit Zone from Postcode
    postcode_match = postcode_df[postcode_df["Postcode"] == postcode]
    if postcode_match.empty:
        print(f"Row {idx}: Postcode {postcode} not found.")
        continue

    ldz = postcode_match.iloc[0]["LDZ"]
    exit_zone = postcode_match.iloc[0]["Exit Zone"]

    # Commission uplifts
    sc_commission = row["S/C Commission (p/day)"]
    unit_commission = row["Unit Rate Commission (p/kWh)"]

    site_result = {
        "MPRN": mprn,
        "Postcode": postcode,
        "AQ (kWh)": aq,
    }

    # Process 1, 2, 3 year tariffs
    for duration in [1, 2, 3]:
        # Filter tariffs by LDZ, Exit Zone, and contract length
        applicable_tariffs = flat_df[
            (flat_df["LDZ"] == ldz) &
            (flat_df["Exit Zone"] == exit_zone) &
            (flat_df["Contract Length"] == duration)
        ]

        if applicable_tariffs.empty:
            print(f"Row {idx}: No tariff found for {duration}-year.")
            continue

        # For simplicity, pick the first tariff
        tariff = applicable_tariffs.iloc[0]
        base_sc = tariff["Standing Charge (p/day)"]
        base_unit = tariff["Unit Rate (p/kWh)"]
        tariff_id = tariff["Tariff Name"]

        # Apply commission
        adj_sc = base_sc + sc_commission
        adj_unit = base_unit + unit_commission

        # Calculate forecast spend
        sc_cost = adj_sc * 365 / 100  # p to £
        consumption_cost = adj_unit * aq / 100
        total_spend = sc_cost + consumption_cost

        # Forecast Commission (£)
        sc_commission_value = sc_commission * 365 / 100
        consumption_commission_value = unit_commission * aq / 100
        total_commission = sc_commission_value + consumption_commission_value

        # Store in result
        site_result.update({
            f"{duration}Y Standing Charge (p/day)": adj_sc,
            f"{duration}Y Unit Rate (p/kWh)": adj_unit,
            f"{duration}Y Annual Spend (£)": total_spend,
            f"{duration}Y Annual Commission (£)": total_commission,
            f"{duration}Y Tariff ID": tariff_id,
        })

    results.append(site_result)

# ---------------------------------------------------------
# Create DataFrame and Export
# ---------------------------------------------------------
results_df = pd.DataFrame(results)
results_df.to_excel("Gas_Multisite_Pricing_Output.xlsx", index=False)

print("✅ Pricing calculation completed. Output saved to Gas_Multisite_Pricing_Output.xlsx.")
