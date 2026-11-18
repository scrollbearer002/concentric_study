# Plan: Fleetwood Prowler 272 All-Electric Rebuild Bible

## Objective
Produce an evidence-tagged, five-part modernization bible for VIN `1EA1F272941595598` (~2004 Fleetwood Prowler 272-series 27' bumper-pull), covering OEM anatomy, 48V all-electric architecture, 2026 smart stack, industrial design, and weight/BOM/build order.

## Constraints
- Network egress blocks NHTSA vPIC and most OEM brochure hosts; exact door-sticker numbers require physical verification.
- Do not invent steel gauge, tank gallons, or axle plate ratings; mark `unknown` / `era_typical` / `inferred`.
- Prefer non-regression of towability: stay under GAWR/GVWR with 10–15% tongue weight.
- Zero-propane architecture; no diesel hydronic as primary heat (conflicts with 100% electric objective).

## Research frame
- system_of_interest: Fleetwood Prowler 272 bumper-pull shell + chassis
- domain: RV structural/electrical/mechanical modernization
- environment: US travel-trailer regulations, 30A→50A shore path, lithium mobile installs
- stakeholder: tech-savvy young adult owner wanting 2026-standard aesthetics + capability
- success_criteria: complete 5-part bible with confidence tags, power budget, weight audit, phased BOM
- excluded_adjacent: motorhome chassis, Class B van builds, traction EV propulsion trailers (Slipstream range-neutral) except as analogy

## Checkpoints
1. VIN decode year/series stated with confidence
2. OEM anatomy table with verification gates
3. Primary 48V architecture selected with alternatives — **Lead 3 DONE** (`research/prowler_272_ev_rebuild/03_LEAD3_all_electric_offgrid_conversion.md`): Victron MultiPlus-II + 15–20 kWh LiFePO4 primary; power budget; solar/EVSE/HVAC/galley/running-gear; do-not-do; `[S]/[I]`/`[U]` tags
4. Weight delta table nets positive payload margin under dual-axle class
5. Canvas + markdown artifacts committed

## Stop / rollback
- Stop claiming exact OEM numbers if sticker/axle-plate photos are not available
- Do not recommend >GAWR battery placement without tongue-weight model
