from mcp.server.fastmcp import FastMCP
import json
import logging
from pathlib import Path

from .compute_emissions import compute_all
from .render_report import render_markdown, render_html
from .emission_factors import list_egrid_subregions, list_fuels, list_waste_materials

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("carbon_footprint_mcp")

# Initialize FastMCP server
mcp = FastMCP(
    "Carbon Footprint Calculator",
    dependencies=["mcp"]
)

# Set up paths to resources
PROJECT_ROOT = Path(__file__).parent.parent.parent
REFERENCES_DIR = PROJECT_ROOT / "references"

@mcp.resource("file://references/calculation_guide.md")
def get_calculation_guide() -> str:
    """Provides EPA GHG emission calculation methodology and factor references."""
    path = REFERENCES_DIR / "calculation_guide.md"
    return path.read_text(encoding="utf-8") if path.exists() else "Calculation guide not found."

@mcp.resource("file://references/validation_rules.md")
def get_validation_rules() -> str:
    """Provides strict validation rules for the emissions engine."""
    path = REFERENCES_DIR / "validation_rules.md"
    return path.read_text(encoding="utf-8") if path.exists() else "Validation rules not found."

@mcp.resource("file://references/worked_example.md")
def get_worked_example() -> str:
    """Provides a worked example of carbon footprint computation."""
    path = REFERENCES_DIR / "worked_example.md"
    return path.read_text(encoding="utf-8") if path.exists() else "Worked example not found."

@mcp.prompt()
def analyzeEmissions() -> str:
    """
    Prompt template to calculate a company's carbon footprint like an expert sustainability analyst.
    """
    return '''You are an expert Sustainability Analyst and Carbon Accounting specialist.

## Step 1: Gather Information

Start by asking the user to provide the following. Be friendly and concise:

**Required:**
- Bank statement CSV, Xero P&L export, or QBO export

**Optional — but you MUST ask before proceeding, never assume:**
- Geographic location / state (determines electricity emission factors)
- Number of employees (headcount)
- Annual revenue

Do NOT proceed to Step 2 until you have either received these values from the user
or the user has explicitly said to skip them. If skipped, pass null — never invent them.

## Step 1b: Scoring Inputs Gate (MANDATORY)

**STOP after receiving the CSV and ask:**

> "To calculate your carbon intensity score (emissions per employee and per $1M revenue),
> I need two more pieces of information:
> - **Number of employees** (headcount)
> - **Annual revenue** (in USD)
>
> These are optional — if you'd prefer to skip scoring, just say so and I'll proceed
> without it. Otherwise, please share the numbers."

**Rules:**
- If the user provides both → use them exactly as given.
- If the user says skip → pass `null` for both. Do NOT compute scores.
- If the user provides one → use it, pass `null` for the other.
- **NEVER invent, estimate, or assume these numbers.** Do not use round numbers like
  $1,000,000 or 10 employees as defaults. There are no defaults. Only real user-provided
  values are valid.

## Step 2: Categorize Transactions into Emission Categories

When you receive bank/financial data, categorize EACH transaction into these emission
categories using your judgment:

### Scope 1 — Direct Emissions (owned/controlled sources)
- **Stationary Combustion:** Natural gas bills, heating oil, propane purchases, boiler fuel
- **Mobile Combustion:** Fleet fuel (gasoline, diesel), company vehicle fuel cards
- **Refrigerants:** HVAC maintenance/recharge, refrigerant purchases

### Scope 2 — Purchased Energy
- **Electricity:** Electric utility bills, electricity payments
- **Steam/Heat:** District heating, purchased steam

### Scope 3 — Value Chain
- **Business Travel:** Airlines, hotels with flights, rental cars, rail tickets, ride-shares for business
- **Employee Commuting:** Transit subsidies, parking benefits, commuter reimbursements
- **Transportation & Distribution:** Shipping/freight charges (FedEx, UPS, freight forwarders)
- **Waste:** Waste disposal fees, recycling services, dumpster charges

### EXCLUDE from emissions:
- Payroll, rent, insurance, legal, software subscriptions, marketing, bank fees
- Internal transfers between own accounts
- These are operational expenses, not emission sources

### CRITICAL RULES:
1. **NEVER assume a percentage.** Do NOT estimate any value as a fraction of another.
2. **NEVER hardcode or invent numbers.** If no transactions belong to a category, pass null.
3. **Categorization IS allowed.** You MAY assign "PG&E Electric" to electricity or "Shell Gas
   Station" to mobile combustion based on description.
4. **When uncertain**, pass null. It is better to return insufficient_data than to fabricate.
5. **NEVER invent annual_revenue or headcount.** These MUST come from the user verbally.
   If the user did not state them, pass null — even if you think you can infer them from
   the bank data. Inventing these values produces a false carbon intensity score, which is
   more harmful than showing no score at all.

## Step 2b: Determine eGRID Subregion

For Scope 2 electricity calculations, identify the eGRID subregion:
1. If the user provided their location/state in Step 1, map it to the correct eGRID subregion.
2. If not provided, use "US Average" as the default and note this in the report.
3. Common mappings: California→CAMX, Texas→ERCT, New York City→NYCW, Florida→FRCC,
   Pacific Northwest→NWPP, New England→NEWE, Mid-Atlantic→RFCE, Midwest→MROW

## Step 3: Structure the Data and Compute Emissions

Build a JSON payload from the categorized transactions and call `computeEmissions`.

**Scoring fields (`annual_revenue`, `headcount`) must be null unless the user explicitly
provided those values in this conversation. Do not fill them with guesses.**

```json
{
  "source": "bank_csv_categorized",
  "period": "<period from the CSV, e.g. Q1 2026, or Annual 2025>",
  "period_months": "<integer 1 to 12, e.g. 3 for Q1, 12 for Annual>",
  "egrid_subregion": "<from Step 2b>",
  "annual_revenue": null,
  "headcount": null,
  "electricity_kwh": null,
  "steam_mmbtu": null,
  "stationary_combustion": [],
  "mobile_combustion": [],
  "business_travel": [],
  "employee_commuting": [],
  "transportation": [],
  "waste": [],
  "refrigerants": []
}
```

Replace null with real values only when you have them. Leave null for everything else.

### Key conversion guidance for the AI:
- **Electricity:** If you see dollar amounts for utility bills, ask the user for kWh or estimate
  from the bill amount using average rates (~$0.12–0.15/kWh US average). State the assumption.
- **Natural Gas:** If you see dollar amounts, ask for therms/ccf/mcf or estimate.
  1 therm = 100,000 BTU = 0.1 mmBtu. State the assumption.
- **Fuel:** If you see gas station charges, estimate gallons from the dollar amount using
  average fuel prices (~$3.50/gallon). State the assumption clearly.
- **Travel:** If you see airline charges, estimate passenger-miles from ticket cost and
  route if identifiable.
- **Period:** It is critical to accurately set `period_months` based on the CSV data
  (e.g., 3 for a quarter, 12 for a year) so that emissions can be annualized correctly
  against annual revenue. If you can't tell, ask the user.
- **Always state your assumptions** so the user can correct them.

## Step 4: Generate the Report (MANDATORY — do not skip)

After calling `computeEmissions`, you MUST immediately call `generateEmissionsReport`.
This is not optional. Do not present any results to the user before the report files are saved.

**RULE: Never end your turn after `computeEmissions` without also calling `generateEmissionsReport`.**

This saves BOTH:
- `carbon_footprint_report.html` — styled visual report, open in any browser
- `carbon_footprint_report.md` — plain-text fallback

**Always pass an explicit `output_dir`** — either a path the user specified, or the user's
Desktop. Do NOT use the default "." — when running under Claude Desktop the working
directory is not somewhere the user can find.

```json
{
  "emissions_json": "<full JSON string output from computeEmissions>",
  "output_dir": "C:\\Users\\<username>\\Desktop"
}
```

After saving, tell the user the exact absolute paths to both files.

## Step 5: Present Results

1. Show an inline summary of total emissions by scope.
2. If scores were computed (user provided revenue/headcount), highlight the carbon intensity
   score and what it means. If not, note: "Carbon intensity scoring was skipped - provide
   headcount and annual revenue to unlock it."
3. Tell the user both report files were saved and provide the full absolute paths.
4. If any emissions used AI-categorized transactions, add this disclaimer:
   > **AI Categorization Notice:** Some emissions were derived from AI-categorized bank
   > transactions. Only explicitly identified line items were used - no percentage-based
   > estimates were applied. Please review categorizations for accuracy.
5. List any categories that returned insufficient_data and what additional data would unlock them.
6. Suggest 2-3 actionable reduction strategies based on their largest emission sources.

Always rely on the `computeEmissions` tool rather than doing math yourself. Never invent
values for missing data.'''

@mcp.tool()
def computeEmissions(inputs_json: str) -> str:
    """
    Computes greenhouse gas emissions from structured activity data.

    IMPORTANT: After calling this tool, you MUST call generateEmissionsReport with the
    full output of this tool. Do not present results to the user without first saving
    the report files. The _required_next_step field in the response will remind you.

    Args:
        inputs_json: A JSON string containing categorized activity data.
                     Required fields vary by scope:
                     - Scope 1: stationary_combustion, mobile_combustion, refrigerants
                     - Scope 2: electricity_kwh, egrid_subregion, steam_mmbtu
                     - Scope 3: business_travel, employee_commuting, transportation, waste
                     Optional: annual_revenue, headcount (for scoring), period, source
    Returns:
        JSON string containing computed emissions by scope, totals, breakdown,
        carbon intensity scores, and a _required_next_step instruction.
    """
    try:
        inputs = json.loads(inputs_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse inputs_json: {e}")
        return json.dumps({"error": f"Invalid JSON input: {e}"})

    result = compute_all(inputs)
    result["_required_next_step"] = (
        "MANDATORY: You must now call generateEmissionsReport with this full JSON output "
        "and an explicit output_dir (user's Desktop or a path they specified). "
        "Do not present results to the user until the report files are saved. "
        "Pass the entire contents of this response as the emissions_json argument."
    )
    return json.dumps(result, indent=2)

@mcp.tool()
def generateEmissionsReport(emissions_json: str, output_dir: str = ".") -> str:
    """
    Generates a carbon footprint report in HTML + Markdown and saves to disk.

    Args:
        emissions_json: JSON string — the direct output from computeEmissions.
        output_dir: Directory to save reports to. Default is current directory.
    Returns:
        JSON with paths to both report files and the markdown content inline.
    """
    try:
        payload = json.loads(emissions_json)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse emissions_json: {e}")
        return json.dumps({"error": f"Invalid JSON input: {e}"})

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    md_content = render_markdown(payload)
    html_content = render_html(payload)

    md_path = out / "carbon_footprint_report.md"
    html_path = out / "carbon_footprint_report.html"

    md_path.write_text(md_content, encoding="utf-8")
    html_path.write_text(html_content, encoding="utf-8")

    logger.info(f"Reports saved: {md_path.resolve()}, {html_path.resolve()}")

    return json.dumps({
        "md_path": str(md_path.resolve()),
        "html_path": str(html_path.resolve()),
        "markdown_content": md_content,
    })

@mcp.tool()
def listEmissionFactors(category: str = "all") -> str:
    """
    Lists available emission factors for reference.

    Args:
        category: One of 'fuels', 'egrid', 'waste', or 'all'.
    Returns:
        JSON string listing available factors.
    """
    result = {}
    cat = category.lower().strip()
    if cat in ("fuels", "all"):
        result["stationary_fuels"] = list_fuels()
    if cat in ("egrid", "all"):
        result["egrid_subregions"] = list_egrid_subregions()
    if cat in ("waste", "all"):
        result["waste_materials"] = list_waste_materials()
    return json.dumps(result, indent=2)

if __name__ == "__main__":
    mcp.run()
