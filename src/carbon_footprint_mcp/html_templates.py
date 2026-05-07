"""HTML template fragments for the carbon footprint report."""
import math
from html import escape


def build_css():
    return """<style>
    :root {
      --bg: #0b1220; --panel: #111a2b; --panel-2: #0f1726;
      --text: #e5edf8; --muted: #9fb1c9; --line: #243247;
      --green: #10b981; --yellow: #f59e0b; --red: #ef4444; --blue: #3b82f6;
      --accent: #818cf8;
    }
    *{box-sizing:border-box}
    body{margin:0;font-family:"Segoe UI",system-ui,Arial,sans-serif;background:var(--bg);color:var(--text)}
    .wrap{max-width:1200px;margin:24px auto;padding:0 16px}
    .panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden;box-shadow:0 14px 36px rgba(0,0,0,.45);margin-bottom:20px}
    .head{padding:20px 24px;border-bottom:1px solid var(--line)}
    .section-head{padding:12px 24px;border-bottom:1px solid var(--line);background:var(--panel-2)}
    .section-head h2{margin:0;font-size:15px;color:var(--accent)}
    h1{margin:0 0 4px;font-size:26px;letter-spacing:-.5px}
    .meta{color:var(--muted);font-size:13px}
    .hero{padding:32px 24px;text-align:center;border-bottom:1px solid var(--line);background:linear-gradient(135deg,rgba(16,185,129,.06),rgba(59,130,246,.06))}
    .hero-value{font-size:56px;font-weight:700;letter-spacing:-1.5px}
    .hero-label{color:var(--muted);font-size:14px;margin-top:4px}
    table{width:100%;border-collapse:collapse}
    th,td{padding:10px 16px;border-bottom:1px solid var(--line);text-align:left;font-size:13px}
    th{background:var(--panel-2);font-weight:600}
    td.num{text-align:right;font-variant-numeric:tabular-nums}
    .label{display:inline-block;border-radius:999px;padding:2px 10px;font-size:11px;border:1px solid currentColor}
    .computed{color:var(--green)} .insufficient_data{color:var(--muted)}
    .scores{display:flex;gap:16px;padding:16px 24px;flex-wrap:wrap}
    .score-card{flex:1;min-width:200px;background:var(--panel-2);border:1px solid var(--line);border-radius:8px;padding:16px;text-align:center}
    .score-title{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:8px}
    .score-value{font-size:36px;font-weight:700}
    .score-unit{color:var(--muted);font-size:11px;margin:4px 0 8px}
    .score-label{display:inline-block;border:1px solid;border-radius:999px;padding:2px 12px;font-size:12px;text-transform:uppercase;letter-spacing:.5px}
    .score-reason{color:var(--muted);font-size:12px;margin-top:8px}
    .two-col{display:flex;gap:0;flex-wrap:wrap}
    .two-col>div{flex:1;min-width:320px}
    .pie-wrap{padding:24px;display:flex;align-items:center;justify-content:center;gap:24px;flex-wrap:wrap}
    .pie-legend{display:flex;flex-direction:column;gap:6px}
    .pie-legend-item{display:flex;align-items:center;gap:8px;font-size:12px}
    .pie-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
    .pie-pct{color:var(--muted);min-width:36px;text-align:right;font-variant-numeric:tabular-nums}
    .scope-bars{padding:20px 24px}
    .bar-row{display:flex;align-items:center;gap:12px;margin-bottom:10px}
    .bar-label{width:180px;font-size:13px;flex-shrink:0}
    .bar-track{flex:1;height:24px;background:var(--panel-2);border-radius:4px;overflow:hidden;position:relative}
    .bar-fill{height:100%;border-radius:4px;transition:width .6s ease}
    .bar-val{width:100px;text-align:right;font-size:13px;color:var(--muted);font-variant-numeric:tabular-nums;flex-shrink:0}
    .top-rank{display:inline-flex;align-items:center;justify-content:center;width:22px;height:22px;border-radius:50%;font-size:11px;font-weight:700;margin-right:6px}
    .opp-card{padding:16px 24px;border-bottom:1px solid var(--line)}
    .opp-title{font-weight:600;font-size:14px;margin-bottom:4px}
    .opp-body{color:var(--muted);font-size:13px;line-height:1.6}
    .disclaimer{padding:12px 24px;background:rgba(245,158,11,.08);border-left:3px solid var(--yellow);font-size:12px;color:var(--muted);line-height:1.6}
    .footer{padding:12px 24px;color:var(--muted);font-size:11px;border-top:1px solid var(--line)}
    </style>"""


def build_pie_svg(source_distribution, size=200):
    """Build an SVG donut pie chart from source distribution data."""
    if not source_distribution:
        return ""
    cx, cy, r = size / 2, size / 2, size / 2 - 8
    r_inner = r * 0.55
    paths = []
    cumulative = 0.0
    for item in source_distribution:
        pct = item.get("pct_of_total", 0)
        if pct <= 0:
            continue
        start_angle = cumulative / 100 * 2 * math.pi - math.pi / 2
        end_angle = (cumulative + pct) / 100 * 2 * math.pi - math.pi / 2
        large = 1 if pct > 50 else 0
        # Outer arc
        x1o = cx + r * math.cos(start_angle)
        y1o = cy + r * math.sin(start_angle)
        x2o = cx + r * math.cos(end_angle)
        y2o = cy + r * math.sin(end_angle)
        # Inner arc
        x1i = cx + r_inner * math.cos(end_angle)
        y1i = cy + r_inner * math.sin(end_angle)
        x2i = cx + r_inner * math.cos(start_angle)
        y2i = cy + r_inner * math.sin(start_angle)
        d = (f"M {x1o:.2f},{y1o:.2f} A {r},{r} 0 {large} 1 {x2o:.2f},{y2o:.2f} "
             f"L {x1i:.2f},{y1i:.2f} A {r_inner},{r_inner} 0 {large} 0 {x2i:.2f},{y2i:.2f} Z")
        paths.append(f'<path d="{d}" fill="{item["color"]}" opacity="0.85"/>')
        cumulative += pct
    svg = f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">{"".join(paths)}</svg>'
    return svg


def build_pie_section(source_distribution):
    """Build the full pie chart section with legend."""
    if not source_distribution:
        return ""
    svg = build_pie_svg(source_distribution)
    legend_items = ""
    for item in source_distribution:
        pct = item.get("pct_of_total", 0)
        if pct <= 0:
            continue
        legend_items += f"""<div class="pie-legend-item">
            <span class="pie-dot" style="background:{item['color']}"></span>
            <span style="flex:1">{escape(item['display_name'])}</span>
            <span class="pie-pct">{pct}%</span>
            <span style="color:var(--muted);font-size:11px;min-width:60px;text-align:right">{item['metric_tons_co2e']:,.2f} mt</span>
        </div>"""
    return f"""<div class="section-head"><h2>Emissions by Source Category</h2></div>
    <div class="pie-wrap">
        {svg}
        <div class="pie-legend">{legend_items}</div>
    </div>"""


def build_scope_bars(payload):
    """Build CSS horizontal bar chart for scope breakdown."""
    breakdown = payload.get("totals", {}).get("breakdown", {})
    if not breakdown:
        return ""
    bars = ""
    for key, name, color in [
        ("scope_1", "Scope 1 — Direct", "#ef4444"),
        ("scope_2", "Scope 2 — Energy", "#f59e0b"),
        ("scope_3", "Scope 3 — Value Chain", "#3b82f6"),
    ]:
        pct = breakdown.get(f"{key}_pct", 0) or 0
        mt = payload.get(key, {}).get("total_metric_tons_co2e", 0) or 0
        bars += f"""<div class="bar-row">
            <div class="bar-label"><span style="color:{color}">●</span> {name}</div>
            <div class="bar-track"><div class="bar-fill" style="width:{pct}%;background:{color}"></div></div>
            <div class="bar-val">{mt:,.2f} mt · {pct}%</div>
        </div>"""
    return f'<div class="section-head"><h2>Emissions by Scope</h2></div><div class="scope-bars">{bars}</div>'


def build_top_sources(top_sources):
    """Build ranked top sources table."""
    if not top_sources:
        return ""
    rows = ""
    for src in top_sources:
        rank = src["rank"]
        bg = src["color"] + "22"
        rows += f"""<tr>
            <td><span class="top-rank" style="background:{bg};color:{src['color']}">{rank}</span></td>
            <td><span style="color:{src['color']}">●</span> {escape(src['category'])}</td>
            <td class="num">{src['metric_tons_co2e']:,.2f}</td>
            <td class="num">{src['pct_of_total']}%</td>
            <td style="color:var(--muted)">{escape(src['scope'])}</td>
        </tr>"""
    return f"""<div class="section-head"><h2>Top Emission Sources</h2></div>
    <table>
        <thead><tr><th style="width:40px">#</th><th>Category</th><th style="text-align:right">Metric Tons CO2e</th><th style="text-align:right">Share</th><th>Scope</th></tr></thead>
        <tbody>{rows}</tbody>
    </table>"""


def build_score_cards(scores):
    """Build score card HTML."""
    if not scores:
        return ""
    label_colors = {
        "excellent": "#10b981", "good": "#10b981",
        "moderate": "#f59e0b", "high": "#ef4444", "very_high": "#dc2626",
    }
    card_titles = {
        "carbon_intensity_revenue": "Revenue Intensity",
        "carbon_intensity_headcount": "Headcount Intensity",
    }
    cards = ""
    for key, score in scores.items():
        label = score.get("label", "moderate")
        color = label_colors.get(label, "#60a5fa")
        title = card_titles.get(key, key.replace("_", " ").title())
        cards += f"""<div class="score-card">
            <div class="score-title">{escape(title)}</div>
            <div class="score-value" style="color:{color}">{score.get('value', '—')}</div>
            <div class="score-unit">{escape(str(score.get('unit', '')))}</div>
            <div class="score-label" style="border-color:{color};color:{color}">{escape(label)}</div>
            <div class="score-reason">{escape(str(score.get('reason', '')))}</div>
        </div>"""
    return f'<div class="section-head"><h2>Carbon Intensity Score</h2></div><div class="scores">{cards}</div>'


def build_detail_sections(payload):
    """Build detailed scope breakdown tables."""
    from . import render_report
    sections = ""
    for scope_key, scope_name in [
        ("scope_1", "Scope 1: Direct Emissions"),
        ("scope_2", "Scope 2: Purchased Energy"),
        ("scope_3", "Scope 3: Value Chain"),
    ]:
        scope_data = payload.get(scope_key, {})
        categories = scope_data.get("categories", {})
        if not categories:
            continue
        cat_rows = ""
        for cat_key, cat_data in categories.items():
            cat_name = escape(cat_key.replace("_", " ").title())
            label = cat_data.get("label", "")
            val = cat_data.get("value")
            if label == "insufficient_data":
                missing = escape(", ".join(cat_data.get("missing_inputs", [])))
                cat_rows += f'<tr><td>{cat_name}</td><td class="num">—</td><td><span class="label insufficient_data">insufficient data</span></td><td style="color:var(--muted);font-size:12px">{missing}</td></tr>'
            else:
                cat_rows += f'<tr><td>{cat_name}</td><td class="num">{render_report._fmt_kg(val)}</td><td><span class="label computed">computed</span></td><td></td></tr>'
        total_mt = scope_data.get("total_metric_tons_co2e", 0) or 0
        sections += f"""<div class="section-head"><h2>{escape(scope_name)} — {total_mt:,.2f} metric tons CO2e</h2></div>
        <table>
            <thead><tr><th>Category</th><th style="text-align:right">Emissions</th><th>Status</th><th>Notes</th></tr></thead>
            <tbody>{cat_rows}</tbody>
        </table>"""
    return sections


def build_reduction_opportunities(top_sources, payload):
    """Generate contextual reduction recommendations based on top emission sources."""
    if not top_sources:
        return ""
    egrid = payload.get("egrid_subregion", "US Average")
    tips = {
        "Employee Commuting": (
            "🚌 Reduce Employee Commuting Emissions",
            "Implement a remote/hybrid work policy (2–3 days/week from home) to cut commuting emissions by 40–60%. "
            "Offer transit subsidies or bike-to-work incentives. If your team drives, consider an EV incentive program."
        ),
        "Fleet Fuel": (
            "⚡ Electrify Your Fleet",
            "Transitioning company vehicles to electric eliminates Scope 1 mobile emissions entirely. "
            "For mixed fleets, start with the highest-mileage vehicles. Consider fuel cards that track consumption for better data next quarter."
        ),
        "Electricity": (
            "🔌 Reduce Electricity Emissions",
            f"Your electricity estimate is benchmarked using the {escape(egrid)} EPA eGRID region. "
            "Consider purchasing Renewable Energy Certificates (RECs) or signing a green power agreement. "
            "LED lighting, smart thermostats, and Energy Star equipment reduce kWh consumption 15–30%."
        ),
        "Business Travel": (
            "✈️ Optimize Business Travel",
            "Replace short-haul flights (<300 mi) with rail or video calls — short-haul flights have the highest per-mile emissions. "
            "For unavoidable travel, purchase carbon offsets and prefer direct flights (takeoff/landing use the most fuel)."
        ),
        "Shipping & Freight": (
            "📦 Optimize Shipping & Freight",
            "Consolidate shipments to reduce total vehicle-miles. Shift from air freight to ground where timelines allow — "
            "ground shipping emits ~90% less CO2 per ton-mile. Negotiate with carriers who report emissions data."
        ),
        "Waste Disposal": (
            "♻️ Reduce Waste Emissions",
            "Divert waste from landfill to recycling or composting — landfill generates methane (28x CO2 potency). "
            "Implement paperless policies, compost food waste, and audit your waste stream quarterly."
        ),
        "Natural Gas / Heating": (
            "🔥 Reduce Heating Emissions",
            "Improve building insulation and switch to electric heat pumps to eliminate Scope 1 stationary combustion. "
            "Smart thermostats and zone heating can reduce gas consumption 15–25% with no capital expenditure."
        ),
    }
    cards = ""
    count = 0
    for src in top_sources:
        if count >= 3:
            break
        cat = src["category"]
        if cat in tips:
            title, body = tips[cat]
            pct = src["pct_of_total"]
            mt = src["metric_tons_co2e"]
            cards += f"""<div class="opp-card">
                <div class="opp-title">{title} <span style="color:var(--muted);font-weight:400">({mt:,.2f} mt · {pct}% of total)</span></div>
                <div class="opp-body">{body}</div>
            </div>"""
            count += 1
    if not cards:
        return ""
    return f'<div class="section-head"><h2>Reduction Opportunities</h2></div>{cards}'
