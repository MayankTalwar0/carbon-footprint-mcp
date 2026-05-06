# Carbon Footprint Calculation Guide

## Overview

This guide explains how to calculate greenhouse gas (GHG) emissions using the EPA GHG Emission Factors Hub (January 2025). The tool computes emissions across all three scopes of the GHG Protocol.

## General Formula

**Emissions = Activity Data × Emission Factor**

**Total CO2e = (CO2 × 1) + (CH4 × 28) + (N2O × 265)**

GWP values are from the IPCC Fifth Assessment Report (AR5).

## Scope 1: Direct Emissions

Direct emissions from sources owned or controlled by the organization.

### Stationary Combustion (Boilers, Furnaces, Generators)
- **Activity Data:** Amount of fuel consumed (scf of Natural Gas, gallons of Fuel Oil, short tons of Coal)
- **Factors:** Table 1 — kg CO2/mmBtu, g CH4/mmBtu, g N2O/mmBtu (or per native unit)
- **Common fuels:** Natural Gas, Propane, Distillate Fuel Oil No. 2, Motor Gasoline

### Mobile Combustion (Company Vehicles)
- **Activity Data:** Gallons of fuel consumed
- **Factors:** Table 2 — kg CO2/gallon; Tables 3-5 for CH4/N2O by vehicle type
- **Common fuels:** Motor Gasoline (8.78 kg CO2/gallon), Diesel (10.21 kg CO2/gallon)

### Refrigerant Leakage
- **Activity Data:** kg of refrigerant leaked/recharged
- **Factors:** Tables 11-12 — GWP per gas type
- **Common refrigerants:** R-410A (GWP: 1924), R-404A (GWP: 3943), R-134a (GWP: 1300)

## Scope 2: Indirect Emissions (Purchased Energy)

### Electricity
- **Activity Data:** kWh of electricity consumed
- **Factors:** Table 6 — lb CO2/MWh, lb CH4/MWh, lb N2O/MWh by eGRID subregion
- **Key step:** Identify the correct eGRID subregion for your location
- **US Average:** 771.523 lb CO2/MWh

### Steam and Heat
- **Activity Data:** mmBtu of purchased steam/hot water
- **Factors:** Table 7 — 66.33 kg CO2/mmBtu, 1.25 g CH4/mmBtu, 0.125 g N2O/mmBtu

## Scope 3: Value Chain Emissions

### Transportation & Distribution (Categories 4 & 9)
- **Activity Data:** Ton-miles or vehicle-miles
- **Factors:** Table 8 — kg CO2/unit by vehicle type

### Waste (Categories 5 & 12)
- **Activity Data:** Short tons of waste by material type and disposal method
- **Factors:** Table 9 — metric tons CO2e/short ton
- **Methods:** Recycled, Landfilled, Combusted, Composted

### Business Travel & Employee Commuting (Categories 6 & 7)
- **Activity Data:** Passenger-miles by mode
- **Factors:** Table 10 — kg CO2/passenger-mile
- **Modes:** Air (short/medium/long haul), Rail, Bus, Car

## Unit Conversions

- 1 MWh = 1,000 kWh
- 1 lb = 0.453592 kg
- 1 short ton = 0.907185 metric tons
- 1 therm = 100,000 BTU = 0.1 mmBtu
- 1 gallon gasoline ≈ 0.125 mmBtu
