"""
Render carbon footprint reports in Markdown and HTML from emissions JSON.
"""
import json
from datetime import UTC, datetime
from html import escape
from pathlib import Path


def _fmt_value(value, unit=""):
    if value is None:
        return "—"
    if isinstance(value, (int, float)):
        if abs(value) >= 1000:
            return f"{value:,.1f} {unit}".strip()
        return f"{value:,.4f} {unit}".strip()
    return str(value)


def _fmt_kg(value):
    """Format kg value with auto-scaling to metric tons if large."""
    if value is None:
        return "—"
    if abs(value) >= 1000:
        return f"{value/1000:,.2f} metric tons CO2e"
    return f"{value:,.2f} kg CO2e"


LABEL_EMOJI = {
    "excellent": "🟢",
    "good": "🟢",
    "moderate": "🟡",
    "high": "🟠",
    "very_high": "🔴",
    "computed": "✅",
    "insufficient_data": "⚪",
}


# ─── Markdown Renderer ─────────────────────────────────────────────

def render_markdown(payload):
    lines = []
    lines.append("# Carbon Footprint Report")
    lines.append("")
    lines.append(f"- **Generated:** {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"- **Source:** {payload.get('source', 'manual')}")
    lines.append(f"- **Period:** {payload.get('period', 'Not specified')}")
    lines.append(f"- **eGRID Subregion:** {payload.get('egrid_subregion', 'US Average')}")
    lines.append("")

    totals = payload.get("totals", {})
    lines.append("## Summary")
    lines.append("")
    lines.append(f"**Total Emissions: {_fmt_kg(totals.get('total_kg_co2e'))}**")
    lines.append("")

    breakdown = totals.get("breakdown", {})
    if breakdown:
        lines.append("| Scope | Emissions | Share |")
        lines.append("|---|---:|---:|")
        for scope_key, scope_name in [("scope_1", "Scope 1 (Direct)"), ("scope_2", "Scope 2 (Energy)"), ("scope_3", "Scope 3 (Value Chain)")]:
            scope_data = payload.get(scope_key, {})
            val = _fmt_kg(scope_data.get("total_kg_co2e"))
            pct = breakdown.get(f"{scope_key}_pct", 0)
            lines.append(f"| {scope_name} | {val} | {pct}% |")
        lines.append("")

    # Scores
    scores = payload.get("scores", {})
    if scores:
        lines.append("## Carbon Intensity Score")
        lines.append("")
        for key, score in scores.items():
            emoji = LABEL_EMOJI.get(score.get("label", ""), "")
            name = key.replace("_", " ").title()
            lines.append(f"- {emoji} **{name}:** {score.get('value')} {score.get('unit', '')} — {score.get('reason', '')}")
        lines.append("")

    # Top emission sources (ranked table)
    top_sources = payload.get("top_sources", [])
    if top_sources:
        lines.append("## Top Emission Sources")
        lines.append("")
        lines.append("| # | Category | Metric Tons CO2e | Share | Scope |")
        lines.append("|---|---|---:|---:|---|")
        for src in top_sources:
            lines.append(f"| {src['rank']} | {src['category']} | {src['metric_tons_co2e']:,.2f} | {src['pct_of_total']}% | {src['scope']} |")
        lines.append("")

    # Detailed breakdown by scope
    for scope_key, scope_name in [("scope_1", "Scope 1: Direct Emissions"), ("scope_2", "Scope 2: Purchased Energy"), ("scope_3", "Scope 3: Value Chain")]:
        scope_data = payload.get(scope_key, {})
        categories = scope_data.get("categories", {})
        if not categories:
            continue
        lines.append(f"## {scope_name}")
        lines.append(f"**Total: {_fmt_kg(scope_data.get('total_kg_co2e'))}**")
        lines.append("")

        for cat_key, cat_data in categories.items():
            cat_name = cat_key.replace("_", " ").title()
            label = cat_data.get("label", "")
            emoji = LABEL_EMOJI.get(label, "")

            if label == "insufficient_data":
                missing = ", ".join(cat_data.get("missing_inputs", []))
                lines.append(f"### {cat_name} {emoji}")
                lines.append(f"*Insufficient data.* Missing: {missing}")
                lines.append("")
                continue

            lines.append(f"### {cat_name} {emoji}")
            lines.append(f"**{_fmt_kg(cat_data.get('value'))}**")
            lines.append("")

            details = cat_data.get("details", [])
            if isinstance(details, list) and details:
                # Table for list details
                first = details[0]
                headers = [k for k in first.keys() if k != "error"]
                lines.append("| " + " | ".join(h.replace("_", " ").title() for h in headers) + " |")
                lines.append("|" + "|".join(["---:"] * len(headers)) + "|")
                for d in details:
                    if "error" in d:
                        lines.append(f"| ⚠️ {d.get('error', '')} |" + " |" * (len(headers) - 1))
                    else:
                        cells = [str(d.get(h, "")) for h in headers]
                        lines.append("| " + " | ".join(cells) + " |")
                lines.append("")
            elif isinstance(details, dict):
                for dk, dv in details.items():
                    lines.append(f"- {dk.replace('_', ' ').title()}: {dv}")
                lines.append("")

    # Disclaimer
    lines.append("---")
    lines.append("")
    lines.append("> **⚠️ AI Categorization Notice:** Some emissions in this report may have been "
                 "derived from AI-categorized bank/financial transactions. Transaction categorization "
                 "(e.g., identifying utility bills as electricity, fuel purchases as mobile combustion) "
                 "was based on description matching and business context. Please review categorizations "
                 "for accuracy before using this report for regulatory or investor disclosures.")
    lines.append("")
    lines.append("---")
    lines.append("*Emission factors: EPA GHG Emission Factors Hub (January 2025). GWP: IPCC AR5.*")
    lines.append("")

    return "\n".join(lines)


# ─── HTML Renderer ──────────────────────────────────────────────────

def render_html(payload):
    from .html_templates import (
        build_css, build_pie_section, build_scope_bars,
        build_top_sources, build_score_cards, build_detail_sections,
        build_reduction_opportunities,
    )
    totals = payload.get("totals", {})
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    total_mt = totals.get("total_metric_tons_co2e", 0) or 0
    source_dist = payload.get("source_distribution", [])
    top_sources = payload.get("top_sources", [])
    scores = payload.get("scores", {})

    css = build_css()
    pie_section = build_pie_section(source_dist)
    scope_bars = build_scope_bars(payload)
    top_sources_html = build_top_sources(top_sources)
    score_html = build_score_cards(scores)
    detail_html = build_detail_sections(payload)
    reduction_html = build_reduction_opportunities(top_sources, payload)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Carbon Footprint Report</title>
  {css}
</head>
<body>
  <div class="wrap">
    <div class="panel">
      <div class="head">
        <h1>Carbon Footprint Report</h1>
        <div class="meta">Generated: {escape(generated)} | Source: {escape(str(payload.get('source', 'manual')))} | Period: {escape(str(payload.get('period', '')))} | eGRID: {escape(str(payload.get('egrid_subregion', 'US Average')))}</div>
      </div>
      <div class="hero">
        <div class="hero-value">{total_mt:,.2f}</div>
        <div class="hero-label">Total Metric Tons CO2e</div>
      </div>
      {score_html}
      <div class="two-col">
        <div>{scope_bars}</div>
        <div>{pie_section}</div>
      </div>
      {top_sources_html}
      {reduction_html}
      {detail_html}
      <div class="disclaimer">
        ⚠️ <strong>AI Categorization Notice:</strong> Some emissions may have been derived from
        AI-categorized bank/financial transactions. Please review categorizations for accuracy
        before using for regulatory or investor disclosures.
      </div>
      <div class="footer">
        Emission factors: EPA GHG Emission Factors Hub (January 2025) · GWP: IPCC AR5 · Generated by Carbon Footprint MCP
      </div>
    </div>
  </div>
</body>
</html>"""


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="emissions_data.json")
    parser.add_argument("--md-out", default="carbon_footprint_report.md")
    parser.add_argument("--html-out", default="carbon_footprint_report.html")
    args = parser.parse_args()

    payload = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    Path(args.md_out).write_text(render_markdown(payload), encoding="utf-8")
    Path(args.html_out).write_text(render_html(payload), encoding="utf-8")
    print(json.dumps({"md": args.md_out, "html": args.html_out}, indent=2))


if __name__ == "__main__":
    main()
