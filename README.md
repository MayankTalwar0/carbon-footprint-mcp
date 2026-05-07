# Carbon Footprint Calculator (MCP Server)

An MCP (Model Context Protocol) server for calculating organizational carbon footprints from bank statements, financial exports, and structured activity data using EPA GHG emission factors.

> **Privacy and security first**
> - Runs 100% locally on your machine or server
> - Sends no financial data to external APIs or cloud providers
> - Stores no data by default
> - Exposes read-only calculation and reporting tools
> - Works with Claude Desktop, Cursor, and other MCP clients

<!-- mcp-name: io.github.MayankTalwar0/carbon-footprint-mcp -->

## Why This Exists

If you are preparing ESG reporting, investor diligence materials, or internal sustainability reviews, getting to a usable emissions baseline is usually slow and manual.

This server helps turn raw bank statements, Xero or QBO exports, and structured operational inputs into a carbon footprint report in minutes. It maps activities to EPA-aligned emission factors and produces both HTML and Markdown outputs.

## What It Does

1. Ingests bank CSVs, Xero or QBO exports, and structured activity data.
2. Helps categorize transactions into likely emission sources such as electricity, fuel, travel, shipping, and waste.
3. Computes Scope 1, Scope 2, and Scope 3 emissions using EPA GHG emission factors.
4. Scores carbon intensity by revenue and headcount when those inputs are provided.
5. Generates polished HTML and Markdown reports.

## Emission Factor Source

All emission factors are based on the EPA GHG Emission Factors Hub (January 2025), including eGRID 2023 electricity factors and IPCC AR5 global warming potentials.

Covered categories include stationary combustion, mobile combustion, electricity, steam or heat, transportation, waste disposal, business travel, employee commuting, and refrigerants.

## Installation

### Claude Desktop

1. Install `uv`.
2. Open Claude Desktop settings and edit the MCP config.
3. Add this server:

```json
{
  "mcpServers": {
    "carbon-footprint": {
      "command": "uvx",
      "args": ["carbon-footprint-mcp"]
    }
  }
}
```

4. Restart Claude Desktop.

### Claude Code or Cursor

```bash
claude mcp add carbon-footprint -- uvx carbon-footprint-mcp
```

### Local Development

```bash
git clone https://github.com/MayankTalwar0/carbon-footprint-mcp.git
cd carbon-footprint-mcp
pip install -e .
carbon-footprint-mcp
```

## Available MCP Tools

| Tool | Description |
|------|-------------|
| `computeEmissions(inputs_json)` | Computes GHG emissions from structured activity data across all 3 scopes. |
| `generateEmissionsReport(emissions_json, output_dir)` | Renders a polished HTML and Markdown report and saves it to disk. |
| `listEmissionFactors(category)` | Lists available fuel, eGRID, and waste emission factors. |

## Supported Emission Categories

| Scope | Category | Input Required |
|-------|----------|----------------|
| 1 | Stationary Combustion | Fuel type and quantity |
| 1 | Mobile Combustion | Fuel type and gallons |
| 1 | Refrigerant Leakage | Gas type, leaked kg, and GWP |
| 2 | Purchased Electricity | kWh and eGRID subregion |
| 2 | Purchased Steam or Heat | mmBtu |
| 3 | Transportation and Distribution | Vehicle type and distance |
| 3 | Waste Disposal | Material, short tons, and disposal method |
| 3 | Business Travel | Travel mode and passenger-miles |
| 3 | Employee Commuting | Commute mode and passenger-miles |

## Carbon Intensity Scoring

| Score | tCO2e per $1M Revenue | Interpretation |
|-------|-----------------------|----------------|
| Excellent | < 5 | Best-in-class for low-footprint operations |
| Good | 5-20 | Low intensity |
| Moderate | 20-100 | Typical for services and tech |
| High | 100-500 | Heavy operations |
| Very High | > 500 | Very high intensity |

## License

MIT

## Built By SlickBooks

Built by Mayank, founder of [SlickBooks](https://slickbooks.online).
