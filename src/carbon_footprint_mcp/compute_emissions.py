"""
Carbon footprint calculation engine.

Accepts categorized activity data from bank/financial transactions and computes
greenhouse gas emissions using EPA GHG Emission Factors Hub (Jan 2025).

Emissions = Activity Data x Emission Factor
Total CO2e = (CO2 x 1) + (CH4 x 28) + (N2O x 265)
"""
import csv
import json
import re
import sys

from .emission_factors import (
    GWP_CO2, GWP_CH4, GWP_N2O,
    lookup_stationary, lookup_mobile_co2, lookup_egrid,
    lookup_waste, lookup_transportation, lookup_business_travel,
    STEAM_HEAT, EGRID,
)


def _to_number(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", text)
    if cleaned in ("", "-", ".", "-."):
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _safe_round(value, decimals=4):
    if value is None:
        return None
    return round(value, decimals)


def _to_co2e(co2_kg=0, ch4_g=0, n2o_g=0):
    """Convert individual GHG amounts to CO2 equivalent in kg."""
    co2_kg = co2_kg or 0
    ch4_g = ch4_g or 0
    n2o_g = n2o_g or 0
    ch4_kg = ch4_g / 1000.0
    n2o_kg = n2o_g / 1000.0
    return (co2_kg * GWP_CO2) + (ch4_kg * GWP_CH4) + (n2o_kg * GWP_N2O)


def _metric(name, value, unit, missing_inputs):
    """Build a standardized metric result."""
    if missing_inputs:
        return {
            "value": None,
            "unit": unit,
            "label": "insufficient_data",
            "reason": "Cannot be determined from the provided inputs.",
            "missing_inputs": missing_inputs,
        }
    return {
        "value": _safe_round(value),
        "unit": unit,
        "label": "computed",
        "reason": "",
        "missing_inputs": [],
    }


def _required(inputs, names):
    missing = []
    values = {}
    for name in names:
        val = inputs.get(name)
        if val is None:
            missing.append(name)
        else:
            num = _to_number(val)
            if num is None:
                missing.append(name)
            else:
                values[name] = num
    return missing, values


def compute_scope1(inputs):
    """Compute Scope 1 (direct) emissions."""
    results = {}

    # --- Stationary Combustion ---
    stationary_items = inputs.get("stationary_combustion", [])
    if isinstance(stationary_items, list) and stationary_items:
        total_co2e = 0.0
        details = []
        for item in stationary_items:
            fuel = item.get("fuel_type")
            quantity = _to_number(item.get("quantity"))
            quantity_unit = item.get("quantity_unit", "mmbtu")  # mmbtu or native unit
            if not fuel or quantity is None:
                continue
            factors = lookup_stationary(fuel)
            if not factors:
                details.append({"fuel": fuel, "error": f"Unknown fuel type: {fuel}"})
                continue
            # Calculate based on unit
            if quantity_unit.lower() in ("mmbtu", "mm_btu"):
                co2_kg = quantity * factors["co2_per_mmbtu"]
                ch4_g = quantity * factors["ch4_per_mmbtu"]
                n2o_g = quantity * factors["n2o_per_mmbtu"]
            else:
                # Use per-unit factors (gallon, scf, short_ton)
                co2_kg = quantity * (factors["co2_per_unit"] or 0)
                ch4_g = quantity * (factors["ch4_per_unit"] or 0)
                n2o_g = quantity * (factors["n2o_per_unit"] or 0)
            co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
            total_co2e += co2e
            details.append({
                "fuel": fuel, "quantity": quantity, "unit": quantity_unit,
                "co2_kg": _safe_round(co2_kg), "ch4_g": _safe_round(ch4_g),
                "n2o_g": _safe_round(n2o_g), "co2e_kg": _safe_round(co2e),
            })
        results["stationary_combustion"] = {
            "value": _safe_round(total_co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": details,
            "missing_inputs": [],
        }
    else:
        results["stationary_combustion"] = _metric(
            "stationary_combustion", None, "kg CO2e",
            ["stationary_combustion (list of {fuel_type, quantity, quantity_unit})"]
        )

    # --- Mobile Combustion ---
    mobile_items = inputs.get("mobile_combustion", [])
    if isinstance(mobile_items, list) and mobile_items:
        total_co2e = 0.0
        details = []
        for item in mobile_items:
            fuel = item.get("fuel_type")
            gallons = _to_number(item.get("gallons"))
            if not fuel or gallons is None:
                continue
            factors = lookup_mobile_co2(fuel)
            if not factors:
                details.append({"fuel": fuel, "error": f"Unknown fuel type: {fuel}"})
                continue
            co2_kg = gallons * factors["kg_co2_per_unit"]
            # CH4/N2O from mobile are small; use default vehicle factors
            ch4_g = gallons * 0.0  # Needs vehicle-specific data
            n2o_g = gallons * 0.0
            co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
            total_co2e += co2e
            details.append({
                "fuel": fuel, "gallons": gallons,
                "co2_kg": _safe_round(co2_kg), "co2e_kg": _safe_round(co2e),
            })
        results["mobile_combustion"] = {
            "value": _safe_round(total_co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": details,
            "missing_inputs": [],
        }
    else:
        results["mobile_combustion"] = _metric(
            "mobile_combustion", None, "kg CO2e",
            ["mobile_combustion (list of {fuel_type, gallons})"]
        )

    # --- Refrigerant Leakage (if provided) ---
    refrigerant_items = inputs.get("refrigerants", [])
    if isinstance(refrigerant_items, list) and refrigerant_items:
        total_co2e = 0.0
        details = []
        for item in refrigerant_items:
            gas = item.get("gas")
            quantity_kg = _to_number(item.get("quantity_kg"))
            gwp = _to_number(item.get("gwp"))
            if gas and quantity_kg is not None and gwp is not None:
                co2e = quantity_kg * gwp
                total_co2e += co2e
                details.append({
                    "gas": gas, "quantity_kg": quantity_kg,
                    "gwp": gwp, "co2e_kg": _safe_round(co2e),
                })
        if details:
            results["refrigerants"] = {
                "value": _safe_round(total_co2e),
                "unit": "kg CO2e",
                "label": "computed",
                "details": details,
                "missing_inputs": [],
            }

    return results


def compute_scope2(inputs):
    """Compute Scope 2 (purchased energy) emissions."""
    results = {}

    # --- Purchased Electricity ---
    kwh = _to_number(inputs.get("electricity_kwh"))
    egrid_subregion = inputs.get("egrid_subregion", "US Average")
    if kwh is not None:
        factors = lookup_egrid(egrid_subregion)
        if factors is None:
            factors = lookup_egrid("US Average")
            egrid_subregion = "US Average (fallback)"
        # Convert lb/MWh to kg/kWh
        co2_kg = kwh * (factors["co2_lb_per_mwh"] / 2204.62) / 1000 * 1000  # lb/MWh -> kg/kWh
        # Correct: lb/MWh * kWh / 1000 (to MWh) / 2.20462 (lb to kg)
        mwh = kwh / 1000.0
        co2_kg = mwh * factors["co2_lb_per_mwh"] / 2.20462
        ch4_g = mwh * factors["ch4_lb_per_mwh"] / 2.20462 * 1000  # lb -> g
        n2o_g = mwh * factors["n2o_lb_per_mwh"] / 2.20462 * 1000
        co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
        results["electricity"] = {
            "value": _safe_round(co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": {
                "kwh": kwh, "egrid_subregion": egrid_subregion,
                "co2_kg": _safe_round(co2_kg),
                "ch4_g": _safe_round(ch4_g),
                "n2o_g": _safe_round(n2o_g),
            },
            "missing_inputs": [],
        }
    else:
        results["electricity"] = _metric(
            "electricity", None, "kg CO2e", ["electricity_kwh"]
        )

    # --- Purchased Steam/Heat ---
    steam_mmbtu = _to_number(inputs.get("steam_mmbtu"))
    if steam_mmbtu is not None:
        co2_kg = steam_mmbtu * STEAM_HEAT["co2_kg_per_mmbtu"]
        ch4_g = steam_mmbtu * STEAM_HEAT["ch4_g_per_mmbtu"]
        n2o_g = steam_mmbtu * STEAM_HEAT["n2o_g_per_mmbtu"]
        co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
        results["steam_heat"] = {
            "value": _safe_round(co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": {
                "mmbtu": steam_mmbtu,
                "co2_kg": _safe_round(co2_kg),
                "ch4_g": _safe_round(ch4_g),
                "n2o_g": _safe_round(n2o_g),
            },
            "missing_inputs": [],
        }

    return results


def compute_scope3(inputs):
    """Compute Scope 3 (value chain) emissions."""
    results = {}

    # --- Transportation & Distribution ---
    transport_items = inputs.get("transportation", [])
    if isinstance(transport_items, list) and transport_items:
        total_co2e = 0.0
        details = []
        for item in transport_items:
            vehicle = item.get("vehicle_type")
            distance = _to_number(item.get("distance"))
            unit_type = item.get("unit", "vehicle-mile")
            if not vehicle or distance is None:
                continue
            factors = lookup_transportation(vehicle)
            if not factors:
                details.append({"vehicle": vehicle, "error": f"Unknown vehicle: {vehicle}"})
                continue
            co2_kg = distance * factors["co2_kg_per_unit"]
            ch4_g = distance * (factors["ch4_g_per_unit"] or 0)
            n2o_g = distance * (factors["n2o_g_per_unit"] or 0)
            co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
            total_co2e += co2e
            details.append({
                "vehicle": vehicle, "distance": distance, "unit": unit_type,
                "co2e_kg": _safe_round(co2e),
            })
        results["transportation"] = {
            "value": _safe_round(total_co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": details,
            "missing_inputs": [],
        }

    # --- Waste ---
    waste_items = inputs.get("waste", [])
    if isinstance(waste_items, list) and waste_items:
        total_co2e = 0.0
        details = []
        for item in waste_items:
            material = item.get("material")
            short_tons = _to_number(item.get("short_tons"))
            method = item.get("disposal_method", "landfilled")
            if not material or short_tons is None:
                continue
            factors = lookup_waste(material)
            if not factors:
                details.append({"material": material, "error": f"Unknown material: {material}"})
                continue
            factor = factors.get(method)
            if factor is None:
                details.append({"material": material, "error": f"No factor for {method}"})
                continue
            # Factor is in metric tons CO2e per short ton
            co2e_mt = short_tons * factor
            co2e_kg = co2e_mt * 1000  # metric tons to kg
            total_co2e += co2e_kg
            details.append({
                "material": material, "short_tons": short_tons,
                "disposal_method": method, "co2e_kg": _safe_round(co2e_kg),
            })
        results["waste"] = {
            "value": _safe_round(total_co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": details,
            "missing_inputs": [],
        }

    # --- Business Travel ---
    travel_items = inputs.get("business_travel", [])
    if isinstance(travel_items, list) and travel_items:
        total_co2e = 0.0
        details = []
        for item in travel_items:
            mode = item.get("mode")
            distance = _to_number(item.get("distance"))
            if not mode or distance is None:
                continue
            factors = lookup_business_travel(mode)
            if not factors:
                details.append({"mode": mode, "error": f"Unknown travel mode: {mode}"})
                continue
            co2_kg = distance * factors["co2_kg_per_unit"]
            ch4_g = distance * (factors["ch4_g_per_unit"] or 0)
            n2o_g = distance * (factors["n2o_g_per_unit"] or 0)
            co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
            total_co2e += co2e
            details.append({
                "mode": mode, "distance": distance,
                "unit": factors["unit"], "co2e_kg": _safe_round(co2e),
            })
        results["business_travel"] = {
            "value": _safe_round(total_co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": details,
            "missing_inputs": [],
        }

    # --- Employee Commuting ---
    commute_items = inputs.get("employee_commuting", [])
    if isinstance(commute_items, list) and commute_items:
        total_co2e = 0.0
        details = []
        for item in commute_items:
            mode = item.get("mode")
            distance = _to_number(item.get("distance"))
            if not mode or distance is None:
                continue
            factors = lookup_business_travel(mode)
            if not factors:
                details.append({"mode": mode, "error": f"Unknown mode: {mode}"})
                continue
            co2_kg = distance * factors["co2_kg_per_unit"]
            ch4_g = distance * (factors["ch4_g_per_unit"] or 0)
            n2o_g = distance * (factors["n2o_g_per_unit"] or 0)
            co2e = _to_co2e(co2_kg, ch4_g, n2o_g)
            total_co2e += co2e
            details.append({
                "mode": mode, "distance": distance,
                "unit": factors["unit"], "co2e_kg": _safe_round(co2e),
            })
        results["employee_commuting"] = {
            "value": _safe_round(total_co2e),
            "unit": "kg CO2e",
            "label": "computed",
            "details": details,
            "missing_inputs": [],
        }

    return results


def _infer_period_months(inputs):
    """
    Determine how many months the analysis covers.
    Checks explicit `period_months` field first, then parses `period` string.
    Returns (months: float, label: str).
    """
    explicit = _to_number(inputs.get("period_months"))
    if explicit is not None and 0 < explicit <= 12:
        return explicit, f"{explicit}-month period"

    period_str = str(inputs.get("period", "")).lower().strip()
    # Quarter patterns: Q1, Q2, Q3, Q4, quarter
    if any(q in period_str for q in ("q1", "q2", "q3", "q4", "quarter")):
        return 3, "quarterly (3 months)"
    # Half-year
    if any(h in period_str for h in ("h1", "h2", "half", "semi")):
        return 6, "half-year (6 months)"
    # Monthly
    months_list = ["january","february","march","april","may","june",
                   "july","august","september","october","november","december"]
    if any(m in period_str for m in months_list) or "month" in period_str:
        return 1, "monthly (1 month)"
    # Annual / yearly
    if any(a in period_str for a in ("annual", "yearly", "year", "fy", "cy")):
        return 12, "annual (12 months)"
    # Default: assume annual if not specified
    return 12, "assumed annual (no period specified)"


def compute_score(total_co2e_kg, inputs, period_months=12, period_label="annual (12 months)"):
    """
    Compute a carbon intensity score based on total emissions
    relative to revenue or headcount.

    Revenue intensity annualises emissions before comparing to annual_revenue,
    so a quarterly analysis isn't understated vs. a full-year figure.
    Headcount intensity uses the period emissions as-is (point-in-time metric).
    """
    scores = {}
    annualisation_factor = 12.0 / period_months

    revenue = _to_number(inputs.get("annual_revenue"))
    if revenue is not None and revenue > 0:
        annual_co2e_kg = total_co2e_kg * annualisation_factor
        mt_per_million = (annual_co2e_kg / 1000) / (revenue / 1_000_000)
        if mt_per_million < 5:
            label = "excellent"
            reason = "< 5 tCO2e per $1M revenue - best-in-class"
        elif mt_per_million < 20:
            label = "good"
            reason = "5-20 tCO2e per $1M revenue - low intensity"
        elif mt_per_million < 100:
            label = "moderate"
            reason = "20-100 tCO2e per $1M revenue - typical for services/tech"
        elif mt_per_million < 500:
            label = "high"
            reason = "100-500 tCO2e per $1M revenue - high intensity"
        else:
            label = "very_high"
            reason = "> 500 tCO2e per $1M revenue - very high intensity"
        scores["carbon_intensity_revenue"] = {
            "value": _safe_round(mt_per_million, 2),
            "unit": "metric tons CO2e per $1M revenue (annualised)",
            "label": label,
            "reason": reason,
            "methodology": (
                f"Emissions annualised from {period_label} "
                f"(x{_safe_round(annualisation_factor, 4)}) before dividing by annual revenue."
            ),
        }

    headcount = _to_number(inputs.get("headcount"))
    if headcount is not None and headcount > 0:
        per_employee = (total_co2e_kg / 1000) / headcount
        if per_employee < 2:
            label = "excellent"
            reason = "< 2 tCO2e per employee - remote/digital business"
        elif per_employee < 5:
            label = "good"
            reason = "2-5 tCO2e per employee - low footprint"
        elif per_employee < 15:
            label = "moderate"
            reason = "5-15 tCO2e per employee - typical office-based"
        elif per_employee < 50:
            label = "high"
            reason = "15-50 tCO2e per employee - heavy operations"
        else:
            label = "very_high"
            reason = "> 50 tCO2e per employee - very high"
        scores["carbon_intensity_headcount"] = {
            "value": _safe_round(per_employee, 2),
            "unit": f"metric tons CO2e per employee ({period_label})",
            "label": label,
            "reason": reason,
            "methodology": f"Period emissions ({period_label}) divided by headcount. Not annualised.",
        }

    return scores


def compute_all(raw_inputs):
    """
    Main entry point. Accepts a dict of categorized activity data and returns
    a full emissions breakdown by scope, totals, and scoring.
    """
    inputs = dict(raw_inputs)

    scope1 = compute_scope1(inputs)
    scope2 = compute_scope2(inputs)
    scope3 = compute_scope3(inputs)

    def _sum_scope(scope_results):
        total = 0.0
        for key, item in scope_results.items():
            val = item.get("value")
            if val is not None and item.get("label") == "computed":
                total += val
        return total

    scope1_total = _sum_scope(scope1)
    scope2_total = _sum_scope(scope2)
    scope3_total = _sum_scope(scope3)
    grand_total = scope1_total + scope2_total + scope3_total

    # Scope breakdown percentages
    breakdown = {}
    if grand_total > 0:
        breakdown = {
            "scope_1_pct": _safe_round(scope1_total / grand_total * 100, 1),
            "scope_2_pct": _safe_round(scope2_total / grand_total * 100, 1),
            "scope_3_pct": _safe_round(scope3_total / grand_total * 100, 1),
        }

    period_months, period_label = _infer_period_months(inputs)
    scores = compute_score(grand_total, inputs, period_months, period_label)

    # ── Source distribution (for pie chart — by bank transaction category) ──
    CATEGORY_DISPLAY = {
        "stationary_combustion": ("Natural Gas / Heating", "#f97316", "1"),
        "mobile_combustion": ("Fleet Fuel", "#ef4444", "1"),
        "refrigerants": ("Refrigerants", "#f59e0b", "1"),
        "electricity": ("Electricity", "#3b82f6", "2"),
        "steam_heat": ("Steam & Heat", "#0ea5e9", "2"),
        "transportation": ("Shipping & Freight", "#06b6d4", "3"),
        "waste": ("Waste Disposal", "#84cc16", "3"),
        "business_travel": ("Business Travel", "#8b5cf6", "3"),
        "employee_commuting": ("Employee Commuting", "#ec4899", "3"),
    }

    source_distribution = []
    all_scopes = {**scope1, **scope2, **scope3}
    for cat_key, cat_data in all_scopes.items():
        val = cat_data.get("value")
        if val is not None and val > 0 and cat_data.get("label") == "computed":
            display_name, color, scope_num = CATEGORY_DISPLAY.get(
                cat_key, (cat_key.replace("_", " ").title(), "#a3a3a3", "?")
            )
            pct = _safe_round(val / grand_total * 100, 1) if grand_total > 0 else 0
            source_distribution.append({
                "category": cat_key,
                "display_name": display_name,
                "scope": f"Scope {scope_num}",
                "kg_co2e": _safe_round(val),
                "metric_tons_co2e": _safe_round(val / 1000, 2),
                "pct_of_total": pct,
                "color": color,
            })

    # Sort by emissions descending
    source_distribution.sort(key=lambda x: x["kg_co2e"], reverse=True)

    # Top sources (ranked table data)
    top_sources = []
    for rank, src in enumerate(source_distribution, 1):
        top_sources.append({
            "rank": rank,
            "category": src["display_name"],
            "scope": src["scope"],
            "metric_tons_co2e": src["metric_tons_co2e"],
            "pct_of_total": src["pct_of_total"],
            "color": src["color"],
        })

    return {
        "source": inputs.get("source", "manual"),
        "period": inputs.get("period", "Not specified"),
        "egrid_subregion": inputs.get("egrid_subregion", "US Average"),
        "scope_1": {
            "total_kg_co2e": _safe_round(scope1_total),
            "total_metric_tons_co2e": _safe_round(scope1_total / 1000, 2),
            "categories": scope1,
        },
        "scope_2": {
            "total_kg_co2e": _safe_round(scope2_total),
            "total_metric_tons_co2e": _safe_round(scope2_total / 1000, 2),
            "categories": scope2,
        },
        "scope_3": {
            "total_kg_co2e": _safe_round(scope3_total),
            "total_metric_tons_co2e": _safe_round(scope3_total / 1000, 2),
            "categories": scope3,
        },
        "totals": {
            "total_kg_co2e": _safe_round(grand_total),
            "total_metric_tons_co2e": _safe_round(grand_total / 1000, 2),
            "breakdown": breakdown,
        },
        "scores": scores,
        "source_distribution": source_distribution,
        "top_sources": top_sources,
    }


if __name__ == "__main__":
    raw = sys.stdin.read().strip()
    payload = json.loads(raw) if raw else {}
    result = compute_all(payload)
    print(json.dumps(result, indent=2))
