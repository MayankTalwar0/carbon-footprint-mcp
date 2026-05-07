# Input Validation Rules

Run these checks before emission computation. If a check fails, ask for clarification.

## Universal Checks

- Confirm analysis period (monthly, quarterly, or annual).
- Confirm currency and units are consistent across all sources.
- If a required field is missing for a category, return `insufficient_data` and list `missing_inputs`.

## Bank CSV / Financial Export Checks

- Verify debit/credit direction is correct.
- Ensure amounts are numeric.
- Only categorize transactions that are clearly emission sources.
- Exclude: payroll, rent, insurance, legal, software, marketing, bank fees.
- Exclude: internal transfers between own accounts.

## Transaction Categorization Rules

When the agent categorizes transactions to derive emission inputs:

- **Allowed:** Assigning a clearly named utility bill to electricity, a fuel purchase to mobile combustion, or a shipping charge to transportation based on description.
- **Forbidden:** Assuming "electricity = 30% of utilities" or any percentage-based estimate.
- **Forbidden:** Hardcoding any numerical value that does not trace to a specific line item.
- **Required:** If no transactions match a category, pass `null` for that input.
- **Required:** Include AI categorization disclaimer in all reports using categorized data.

## Unit Conversion Assumptions

When converting spend amounts to activity data (for example, electricity bill -> kWh):

- **Required:** State the assumption explicitly (for example, "Assumed a local average electricity rate of 0.13 per kWh").
- **Required:** Flag as an estimate in the output.
- **Preferred:** Ask the user for actual consumption data instead.

## eGRID Subregion

- If the user provides city, region/state, or country, map to the closest available eGRID subregion.
- If not provided, default to "US Average" and note in the report that this is the current EPA/eGRID fallback benchmark.
- Do NOT silently assume a subregion without disclosing.

## Edge-Case Guardrails

- Electricity emissions require kWh and a valid eGRID subregion.
- Mobile combustion requires fuel type and gallons.
- Waste requires material type, quantity in short tons, and disposal method.
- Business travel requires mode and distance in passenger-miles or vehicle-miles.
- Refrigerant emissions require gas type, quantity in kg, and GWP value.
- Zero or negative values should be rejected with a clear error.
