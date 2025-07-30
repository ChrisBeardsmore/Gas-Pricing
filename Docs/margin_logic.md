Margin Logic – Gas Pricing Tools

This document outlines how supplier margin is calculated, inferred, or applied within Dyce Energy’s internal gas pricing tools.

🎯 Purpose

To provide transparency on how margin is handled in multi-site quote tools, particularly when applying uplifts to standing charges and unit rates.

🧾 Definition

Margin is the difference between the total cost of delivering gas (based on base rates) and the sell price offered to the customer. It may be expressed:

As a fixed uplift (p/day or p/kWh)

As a monetary value (e.g., £ total across contract)

As a percentage of total contract value (TAC)

🧮 Margin Calculation Approach

Margin is not explicitly shown in the customer-facing quote but is implicitly created by applying uplifts to base prices:

1. Inputs

Base Standing Charge (SC) and Unit Rate from flat file

Uplifts entered per site and duration:

Standing Charge Uplift (p/day)

Unit Rate Uplift (p/kWh)

Annual Consumption (kWh)

2. Sell Price Calculation

Sell SC = Base SC + SC Uplift
Sell Unit Rate = Base Unit + Unit Uplift

3. TAC Calculation

TAC (£) = ((Sell Unit Rate × Annual kWh) + (Sell SC × 365)) / 100

4. Implied Margin (£)

Margin = (Uplift Unit × kWh + Uplift SC × 365) / 100

5. Optional: Margin % of TAC

Margin % = (Margin / TAC) × 100

📌 Notes

Uplift limits enforced:

Max SC Uplift = 100p/day

Max Unit Uplift = 3.000p/kWh

Margin logic is inferred from uplifts; not directly entered

Margin is not shown to customer in the final Excel export

🔄 Future Enhancements

Add a margin calculator mode: user inputs target margin, tool back-calculates required uplifts

Allow toggling between % margin and fixed uplift entry

Include margin per site in internal summary (optional toggle)

⚠️ Risks / Considerations

Very low consumption sites may distort margin %

Hardcoded uplift limits may limit flexibility on niche quotes

Always sanity-check TAC vs. expected customer value before finalising

