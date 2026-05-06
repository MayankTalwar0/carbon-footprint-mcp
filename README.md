# Carbon Footprint Calculator (MCP Server)

An MCP (Model Context Protocol) server for calculating organizational carbon footprints from bank statements and financial exports using EPA GHG Emission Factors.

> **🔒 PRIVACY & SECURITY FIRST:**
> - **Zero Cloud Risk**: This tool runs 100% locally on your machine/server.
> - **No Data Sent Externally**: Financial data is **NEVER** sent to any external API, cloud provider, or third-party service.
> - **No Data Storage**: The server processes inputs in-memory and returns results directly. No data is stored, cached, or logged.
> - **Strictly Read-Only**: This server executes NO state changes. It is a strictly read-only calculation engine.
> - **Strictly Local Processing**: Safely integrates with Claude Desktop, Cursor, and other MCP clients while maintaining full data sovereignty.

## Why This Exists

If you're a sustainability officer, founder, or operations lead preparing for ESG reporting, investor due diligence, or regulatory compliance — you need to know your carbon footprint. Most organizations either don't track emissions, hire expensive consultants, or spend weeks pulling numbers from utility bills and spreadsheets.

This tool turns your raw bank statement (or Xero/QBO export) into a structured carbon footprint report in minutes, entirely on your own machine. The AI categorizes your transactions into emission sources, maps them to EPA-standard emission factors, and generates a professional report.

## What It Does

1. **Ingests Data**: Accepts bank CSVs, Xero/QBO P&L exports, or structured activity data.
2. **AI Transaction Categorization**: The AI classifies each transaction into emission categories (electricity, fuel, travel, shipping, waste) based on the description. **This step is AI-driven and can make mistakes** — always review the categorizations.
3. **Computes Emissions**: Calculates CO2e across Scope 1 (direct), Scope 2 (energy), and Scope 3 (value chain) using official EPA factors.
4. **Scores Carbon Intensity**: Benchmarks your emissions per $1M revenue and per employee.
5. **Generates Reports**: Creates polished HTML and Markdown reports with full scope breakdowns.

## Emission Factor Source

All emission factors are from the **EPA GHG Emission Factors Hub (January 2025)**:
- **eGRID 2023** electricity factors (28 subregions + US Average)
- **IPCC AR5** Global Warming Potentials (CH4: 28, N2O: 265)
- Covers: stationary combustion, mobile combustion, electricity, steam/heat, transportation, waste disposal, business travel, employee commuting, and refrigerants.

---
*mcp-name: io.github.MayankTalwar0/carbon-footprint-calculator*

## Setup & Installation

### Option 1: Claude Desktop (Manual Installation)

**Step 1: Install `uv`**
- **Mac/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Windows**: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`

**Step 2: Open Claude's Configuration**
1. Open Claude Desktop → **Claude** → **Settings** → **Developer** → **Edit Config**

**Step 3: Add the Server**
```json
{
  "mcpServers": {
    "carbon-footprint": {
      "command": "uvx",
      "args": [
        "carbon-footprint-mcp"
      ]
    }
  }
}
```

**Step 4: Restart Claude**

### Option 2: Claude Code or Cursor

```bash
claude mcp add carbon-footprint -- uvx carbon-footprint-mcp
```

### Option 3: Local Development

```bash
git clone https://github.com/MayankTalwar0/carbon-footprint-calculator.git
cd carbon-footprint-calculator
pip install -e .

# Run the server directly
carbon-footprint-mcp
```

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `computeEmissions(inputs_json)` | Computes GHG emissions from structured activity data across all 3 scopes. Returns emissions breakdown, totals, and carbon intensity scores. |
| `generateEmissionsReport(emissions_json, output_dir)` | Renders a polished HTML + Markdown carbon footprint report and saves to disk. |
| `listEmissionFactors(category)` | Lists available emission factors — fuels, eGRID subregions, or waste materials. |

## Supported Emission Categories

| Scope | Category | Input Required |
|-------|----------|----------------|
| **1** | Stationary Combustion | Fuel type + quantity (scf, gallons, short tons) |
| **1** | Mobile Combustion | Fuel type + gallons |
| **1** | Refrigerant Leakage | Gas type + kg leaked + GWP |
| **2** | Purchased Electricity | kWh + eGRID subregion |
| **2** | Purchased Steam/Heat | mmBtu |
| **3** | Transportation & Distribution | Vehicle type + distance |
| **3** | Waste Disposal | Material + short tons + disposal method |
| **3** | Business Travel | Travel mode + passenger-miles |
| **3** | Employee Commuting | Commute mode + passenger-miles |

## Carbon Intensity Scoring

| Score | tCO2e per $1M Revenue | Interpretation |
|-------|-----------------------|----------------|
| 🟢 Excellent | < 5 | Best-in-class (digital/remote businesses) |
| 🟢 Good | 5–20 | Low intensity |
| 🟡 Moderate | 20–100 | Typical for services/tech |
| 🟠 High | 100–500 | Heavy operations |
| 🔴 Very High | > 500 | Very high intensity (manufacturing/logistics) |

## License

MIT

## Built By SlickBooks

Built by Mayank, founder of [SlickBooks](https://slickbooks.online).
SlickBooks provides managed bookkeeping, bookkeeping automation, financial forecast automation, and custom finance agents.
