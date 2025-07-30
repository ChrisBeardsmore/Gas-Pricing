Postcode to LDZ Mapping

This document describes the logic and structure used to determine a site's Local Distribution Zone (LDZ) from its postcode, used in Dyce Energy’s gas pricing tools.

🎯 Purpose

To map UK postcodes to their respective LDZs using a prefix-based lookup, enabling accurate filtering of base rates in the gas flat file.

📥 Source File

File name: postcode_ldz_full.csv

Stored in GitHub repo: Gas-Pricing

Format: CSV with columns:

Postcode: Prefix or full postcode segment

LDZ: Associated LDZ code (e.g., SC, NE, WM)

🔄 Matching Logic

Input:

User-provided postcode from the quote input grid (e.g., LS11 5AB)

Processing:

Remove spaces and convert to uppercase → LS115AB

Iteratively check for a match in the LDZ file using the first N characters:

Try first 7 characters → 6 → 5 → 4 → 3

Return the first match found in the CSV

If no match is found, return blank LDZ

Code reference:

for length in [7,6,5,4,3]:
    match = ldz_df[ldz_df["Postcode"].str.startswith(postcode[:length])]
    if not match.empty:
        return match.iloc[0]["LDZ"]

📦 Example

Input postcode: B1 1AA

Cleaned: B11AA

Matches with LDZ row: B1 → WM

Output: WM

⚠️ Known Limitations

If no 3+ character match exists in the mapping, LDZ will be blank

Postcodes with unusual formatting may fail to match without cleaning

📘 Best Practices

Ensure the postcode_ldz_full.csv file is pre-cleaned

All postcodes uppercase

No trailing/leading spaces

Always log unmapped postcodes during tool runs for audit/debugging

🔄 Update Procedure

If postcode boundaries change or a new mapping is needed:

Regenerate postcode_ldz_full.csv

Ensure prefix granularity covers at least 3-character level

Re-upload to GitHub and test mapping logic in the tool

