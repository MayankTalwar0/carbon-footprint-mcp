# Worked Example

## Scenario

Small tech company, 25 employees, San Francisco (eGRID: CAMX)
Analysis period: Q1 2026
Annual revenue: $5,000,000

## Inputs

```json
{
  "source": "bank_csv_categorized",
  "period": "Q1 2026",
  "egrid_subregion": "CAMX",
  "annual_revenue": 5000000,
  "headcount": 25,
  "electricity_kwh": 45000,
  "stationary_combustion": [
    {"fuel_type": "Natural Gas", "quantity": 1200, "quantity_unit": "scf"}
  ],
  "mobile_combustion": [
    {"fuel_type": "Motor Gasoline", "gallons": 800}
  ],
  "business_travel": [
    {"mode": "Air Travel - Medium Haul", "distance": 25000},
    {"mode": "Passenger Car", "distance": 5000}
  ],
  "employee_commuting": [
    {"mode": "Passenger Car", "distance": 75000},
    {"mode": "Transit Rail", "distance": 30000}
  ],
  "waste": [
    {"material": "Mixed MSW", "short_tons": 3, "disposal_method": "landfilled"},
    {"material": "Mixed Paper (general)", "short_tons": 0.8, "disposal_method": "recycled"}
  ]
}
```

## Expected Output Shape

- Results are returned under `scope_1`, `scope_2`, `scope_3`.
- Each scope has `total_kg_co2e`, `total_metric_tons_co2e`, and `categories`.
- Each category has `value`, `unit`, `label`, `details`, and `missing_inputs`.
- Categories with incomplete inputs return `label: insufficient_data`.
- `totals` section has grand total and scope breakdown percentages.
- `scores` section has carbon intensity per revenue and per headcount.

## Expected Interpretation

- Scope 2 (electricity) likely dominates for a tech company.
- Scope 3 (travel, commuting) is the second largest contributor.
- Scope 1 (gas, fleet fuel) is relatively small.
- Carbon intensity score for a tech company at this revenue should be "good" or "moderate".
