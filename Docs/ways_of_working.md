Dyce Energy – Ways of Working (Pricing Tools)

This document outlines key practices, conventions, and principles used by the Dyce Energy team when developing and maintaining internal gas pricing tools.

🧭 Purpose

To ensure a consistent, transparent, and collaborative approach when building, editing, and documenting logic used in gas pricing tools.

📁 File Organisation

All pricing tools are stored in the Gas-Pricing GitHub repo

Documentation lives in the Docs/ folder using .md markdown format

Flat files and mappings are stored in /data or pulled from GitHub URLs

💬 Naming Conventions

Entity

Format / Notes

Markdown Docs

snake_case.md (e.g., uplift_tool_logic.md)

Postcode column

Post Code (with space)

LDZ

Uppercase 2–3 letter codes (e.g., SC)

Duration

Represented in months (12, 24, 36)

Booleans

Use TRUE/FALSE not Yes/No

⚙️ Development Standards

Tools built in Python + Streamlit for transparency and auditability

Avoid hardcoded values in logic — use inputs, files, or toggles

Use st.data_editor for intuitive data entry where possible

Code is saved to GitHub; version control is expected for major changes

🧠 Logic Design

Logic must be documented in Docs/

Flat file structure is tightly controlled — no column renaming without doc + code update

Postcode matching logic uses decreasing prefix logic (7 → 3 chars)

Rate lookups prioritise lowest unit rate match within correct LDZ, duration, band

✅ QA & Testing

Validate all new flat files on upload (column check, nulls check)

Highlight unmatched LDZ or postcodes to user

Export only customer-safe columns (e.g., hide uplift and margin in output)

Total TAC must be shown and validated against site-level totals

🔄 Updating Docs

All logic changes should be reflected in the relevant .md file

Versioning via GitHub commit messages

New tools or workflows should get their own markdown document

🤝 Collaboration

Shared knowledge is preferred over siloed logic

Team members should refer to the Docs/ folder before editing tool logic

Use markdown to capture rationales behind design decisions

🚧 Work in Progress

Integrating persistent user memory (e.g., recent quotes)

Standardising margin targets + uplift back-calcs

Adding visualisations to final output

