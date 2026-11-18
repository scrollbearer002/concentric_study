# Lead Researcher 3 — 100% All-Electric Off-Grid Conversion

**Territory:** Zero-propane architecture for Fleetwood Prowler ~27' bumper-pull (VIN class: Prowler 272-series; plan VIN `1EA1F272941595598`).  
**Audience:** 2026 tech-savvy owners.  
**Evidence hygiene:** `[S]` = sourced this research pass; `[I]` = inferred / industry-typical; `[U]` = unknown — verify on unit.  
**Environment basis:** Dual-axle travel-trailer chassis (~7000–7600 lb GVWR class if dual 3500 axles), US 30A/50A shore path, mobile lithium install constraints; egress blocked most OEM/NHTSA hosts — treat door-sticker numbers as physical verification gates.

---

## 0. Chassis / GVWR constraint gate (verify before buying iron)

| Constraint | Working assumption | Tag | Verification gate |
|---|---|---|---|
| Axle class | Dual 3500 lb axles → **7000 lb combined GAWR** | `[I]` for this VIN | Photograph axle tags |
| GVWR | Often **7000–7600 lb** for 27' dual-3500 TTs; may be **less than** GAWR sum | `[I]` | Door sticker / VIN plate |
| Tongue weight target | **10–15%** of loaded trailer weight | `[S]` industry tow practice / plan constraint | CAT scale before/after |
| Payload after conversion | Must remain positive after battery + solar + HVAC + gear | — | Weight audit §7 |

**Do not size a 30 kWh floor bank until tongue and axle scales clear the model.**

---

## 1. 48V LiFePO4 architecture + inverter ecosystems

### 1.1 Power budget (idle / cruise / peak)

Assumes envelope upgrade (spray foam + better seals) and heat-pump HVAC; 2 adults; temperate–hot US climate. Values are continuous AC-side watts unless noted.

| Mode | Definition | W (typ.) | Notes | Tag |
|---|---|---|---|---|
| **Idle** | Night / parked, fridge + controls + standby inverter | **80–180 W** | Victron zero-load ~20–28 W `[S]`; fridge average ~40–80 W `[I]`; 12 V bus via DC-DC ~20–40 W `[I]` | Mixed |
| **Cruise** | Day living: HVAC low–mid, fridge, lights, laptops, pump, Starlink | **600–1500 W** | Mini-split part-load often 400–900 W `[S]` rated-range context; HVAC dominates | Mixed |
| **Peak** | HVAC high + induction + microwave/oven overlap | **3500–5500 W** | Induction 1500–1800 W `[S/I]` + HVAC 1000–1500 W `[S]` + oven 1000–1500 W `[I]` | Mixed |
| **Simultaneous design case** | HVAC + induction **together** (must be continuous, not surge) | **≥3000–3500 W inverter continuous** | Size inverter for this; surge for compressor/oven start | `[I]` design rule |

**Daily energy (design):**

| Scenario | kWh/day | Bank implication (1 day @ ~90% usable) | Tag |
|---|---|---|---|
| Mild, HVAC light | 6–10 | 10–15 kWh | `[I]` |
| Hot, HVAC heavy + cooking | 12–20 | 20–30 kWh | `[I]` |
| Winter heat-pump heavy | 15–25+ | 20–30 kWh + shore/alt/solar assist | `[I]` |

### 1.2 Bank sizing options (48V LiFePO4)

| Option | Nominal | Usable (~90%) | Approx. mass | Fit on 27' TT | Verdict |
|---|---|---|---|---|---|
| **10 kWh** | ~200 Ah @ 48 V | ~9 kWh | ~80–100 lb/module class ×1–2; **~100–200 lb** pack | Easiest tongue | **Minimum** weekend / mild climate only |
| **15 kWh** | ~300 Ah | ~13.5 kWh | **~250–350 lb** | Sweet spot if solar ≥1.5 kW | **Primary for most owners** |
| **20 kWh** | ~400 Ah | ~18 kWh | **~350–450 lb** | Needs axle/tongue model | **Primary for HVAC+induction autonomy** |
| **30 kWh** | ~600 Ah | ~27 kWh | **~550–700 lb** | High risk of GAWR/tongue exceed | **Only with weight strip + CAT proof** |

**Module anchors `[S]`:**
- EG4 WallMount 48V 280 Ah ≈ **14.3 kWh** each (common build pair → 28.6 kWh).
- Generic 48V 100 Ah rack (~5.12 kWh) ≈ **45 kg / 99 lb** net (MUST LP16-48100 class datasheet).
- Generic 48V 200 Ah (~10.24 kWh) ≈ **80 kg / 176 lb** net (MUST LP16-48200).
- EcoFlow Power Kit battery class: ~**5 kWh** LFP modules; hub telemetry shows **totalOutWatts up to 7200 W** (protocol docs).

**LiFePO4 charge profile (configure inverter/charger) `[S/I]`:**
- Absorb / bulk ≈ **57.6 V** (3.60 V/cell) — Victron MultiPlus-II datasheet absorption.
- Float ≈ **55.2 V** — Victron datasheet.
- Do **not** equalize like flooded lead-acid. Follow BMS closed-loop when available.

### 1.3 Inverter / AIO comparison for **RV mobile** use

| Platform | Cont. power (batt) | Idle | Weight | Mobile fitness | Telemetry | RV verdict |
|---|---|---|---|---|---|---|
| **Victron MultiPlus-II 48 V** (prefer **2x120V** US models; Quattro if dual AC-in) | 3–5 kVA class common; higher available | **20–28 W** zero-load `[S]` (4–6 kW EU sheet) | ~**47–65 lb** class `[I]` for 3–5k; EU 4/6 kW sheets **21–29 kg** `[S]` | **Best** — datasheet explicitly marine/vehicle; PowerControl/PowerAssist for limited shore | Cerbo GX + VRM + Lynx | **PRIMARY** |
| **Victron Quattro 48 V** | Similar to Multi; **two AC inputs** | Similar low idle `[I]` | Heavier than Multi `[I]` | Excellent if shore + generator (or EVSE + generator) without external transfer | Same Victron stack | **PRIMARY alt** if dual-input needed |
| **EG4 12000XP / FlexBOSS21** | 12 kW batt-only; up to 15 kW w/ PV (12000XP) `[S]` | **<70 W** standby `[S]`; FlexBOSS **<60–80 W** `[S]` | **104.7 lb** (12000XP) `[S]`; FlexBOSS ~**88–115 lb** class `[S]` | Strong power/$; **residential AIO** — vibration, mounting, transfer, idle, and service network weaker for TT | EG4 app/Monitor; closed-loop EG4 batteries | **Alt** if budget/power; not mobile-first |
| **EcoFlow Power Kits** | Hub class **~3.6–7.2 kW** total out (telemetry max 7200 W) `[S]` | Higher than Victron `[I]` | Battery ~5 kWh modules; hub separate `[I]` | Fast install, app UX; **ecosystem lock-in**; Gen2 API limits reported `[S]` | App / limited local API | **Alt** for plug-and-play owners |
| **Sol-Ark 15K** | 12 kW batt-only / 15 kW w/ PV `[S]` | **90 W** idle `[S]` | **135 lb** `[S]` | Excellent home hybrid (UL1741); **too heavy / stationary-oriented** for 27' TT | Built-in Wi-Fi/LAN | **Not recommended** as primary mobile |
| **MidNite Rosie / MN15 “The One” AIO** | ~12–15 kW class AIO family `[I/S]` (community/Modbus refs) | Higher than Victron `[I]` | Heavy AIO `[I]` | US off-grid brand; some RV/camper mentions; less mature mobile ecosystem vs Victron | CAN/MQTT community bridges `[S]` | **Experimental alt** |

### 1.4 Primary recommendation + alternatives

**PRIMARY stack (mobile-first, 2026 tech owner):**
1. **48V LiFePO4 bank: 15–20 kWh** (start 15; leave busbar/space for 20).
2. **Victron MultiPlus-II 48/3000 2x120V** minimum; **48/5000** if induction + HVAC concurrent is non-negotiable.
3. **Cerbo GX** (+ GX Touch) + **Lynx Distributor / Lynx Smart BMS** or Lynx + **SmartShunt** + battery BMS CAN/RS485.
4. Separate **MPPT** (Victron SmartSolar) sized to array — do not force high-voltage residential AIO PV limits onto a short roof string without design.

**ALTERNATIVES:**
- **A — Dual AC-in:** Quattro 48/5000 with Input1 = shore/EVSE, Input2 = portable inverter-generator (emergency only; still zero-propane).
- **B — Budget power:** EG4 12000XP + EG4 48V batteries (closed-loop), accept weight/idle and reinforce mount.
- **C — Turnkey:** EcoFlow Power Kit 10–15 kWh for speed; plan exit path if API/lock-in hurts.

**BMS / shunt telemetry:**
| Layer | Choice | Role | Tag |
|---|---|---|---|
| System brain | Cerbo GX | DVCC, VRM, relays, tank/temp | `[S]` Victron ecosystem |
| DC bus | Lynx Distributor + class-T / mega fusing | Fault isolation | `[I]` best practice |
| Current | Lynx Smart Shunt or SmartShunt 500/1000 | Coulomb counting | `[S]` common |
| Pack BMS | Native CAN (EG4/Victron NG/Rec) | Cell protect, charge limits | `[S/I]` |
| Rec BMS | Rec Active/Master class | DIY/high-end cell-level | `[I]` — use if building custom pack |

---

## 2. Solar, alternator, and EVSE shore input

### 2.1 Roof solar max (~27' trailer)

**Usable roof after vents, AC hole (if kept temporarily), antenna, ladder clearance:**  
`[I]` ≈ **70–110 ft²** usable → with **RV-appropriate** 100–200 W modules or cut-to-fit flexible:

| Array | Est. STC watts | Est. weight | Tag |
|---|---|---|---|
| Conservative fixed roof | **1000–1400 W** | ~80–150 lb | `[I]` |
| Aggressive fixed roof | **1600–2000 W** | ~120–200 lb | `[I]` |
| Unrealistic residential 500–650 W TOPCon on TT roof | — | Module alone **52–74 lb** each; dims ~77×45"+ `[S]` Trina NEG18RC / larger | Fit rarely works |

**Cell tech recommendation:**
- **PRIMARY:** **N-type / TOPCon** mono in **RV-sized** rigid or semi-flex frames (higher temp coeff / low-light than older PERC) — prefer modules **sold for mobile** with proper walkability rating.
- **Bifacial:** Use only where **rear albedo exists** (tilted ground arrays, translucent canopy). Flat roof-bonded bifacial gain is usually **negligible** `[I]`. Residential bifacial TOPCon (Trina Vertex S+ etc., up to ~520 W, bifaciality ~80%) `[S]` is **ground-array** tech, not roof-default.

**Deployable ground arrays `[I]`:**
- 2–4 × folding 200–400 W blankets/cases (example catalog mats ~200–300 W, ~6–7 kg) for camp shade parking.
- Separate MPPT input or parallel into second tracker; overcurrent / polarity protection required.

### 2.2 DC-DC alternator charging (tow vehicle)

| Device | Notes | Tag |
|---|---|---|
| **Victron Orion XS 1400** | Smart alternator charger; appears as `alternator` service on Cerbo in Charger mode `[S]` | **PRIMARY** |
| Orion-Tr Smart isolated | Older; no built-in current sense like XS `[S]` | Alt |
| 12→48 V boost topology | Required if truck is 12 V and house is 48 V — size for **cable drop + alternator headroom** | `[I]` |
| Engine protection | Ignition/D+ sense; current limit so truck battery/alternator not cooked | `[I]` |

**Expect `[I]`:** ~50–80 A @ 12 V input class → roughly **0.5–1.0 kW** into 48 V after conversion losses — useful for transit top-up, **not** a substitute for solar/shore for HVAC days.

### 2.3 J1772 / NACS as **shore input to charger** (not traction)

**Architecture (correct):**
```
EVSE (J1772 or NACS→J1772 adapter) → EVSE-to-TT inlet adapter / dogbone
  → MultiPlus/Quattro AC-IN → LiFePO4 charge + PowerAssist loads
```

**Architecture (wrong):** wiring EVSE as if trailer were an EV traction pack / CCS DC fast charge.

| Item | Guidance | Tag |
|---|---|---|
| L2 EVSE | Often 16–48 A @ 240 V available at homes/camp hosts | `[S]` EV practice |
| MultiPlus PowerControl | Cap AC-in amps so EVSE breaker is not tripped; PowerAssist covers peaks `[S]` | Critical |
| NACS | Use **AC** NACS↔J1772 adapters only; **never** DC fast-charge pins into house inverter | `[I]` safety |
| 30A TT cord | Still supported via dogbone; charge rate limited | `[I]` |
| Upgrade path | Add **50A** TT inlet if inverter/charger and wiring support it | `[I]` |

---

## 3. HVAC + envelope

### 3.1 Remove roof AC + gas furnace

Strip propane furnace, propane lines to appliances, and legacy rooftop AC (weight recovery + roof real estate). Seal old roof cut carefully if relocating HVAC.

### 3.2 HVAC options

| Option | Capacity | Power | Pros | Cons | Verdict |
|---|---|---|---|---|---|
| **120V mini-split inverter 12–18k BTU** | 12k covers ~600 ft² rating; 18k ~800 ft² `[S]` Hessaire/Grainger sheets | 12k high-SEER cool **~975–1176 W** rated; 18k **~1388–1505 W** `[S]` | High SEER2 (20–22+), heat+cool, cheap, soft-start friendly | Outdoor unit mount (bumper/frame/side), vibration, freeze protection of lines, aesthetics | **PRIMARY** for most all-electric TT |
| **48V DC rooftop / split (Nomadic Cooling, Cruise N Comfort)** | Product-line dependent | CNC listed as **12/24/48 V split** systems `[S]`; exact W `[U]` — treat **600–1200 W** run as planning band `[I]` until datasheet on chosen SKU | True DC, less inverter conversion loss | Cost, service network, roof weight, confirm heat mode | **PRIMARY alt** if avoiding large AC inverter load |
| **Zero Breeze-class portable** | Spot cool | Battery/inverter limited | Cheap experiment | Not whole-trailer HVAC | **Do not** as primary |
| **RecPro / Houghton rooftop** | Typical 13.5–15k BTU **120V** class | High start / mediocre SEER | Familiar RV form | RecPro confirmed as Houghton/Carrier_AC128 IR class `[S]`; **no verified RecPro 48V SKU** this pass | Keep only as temporary; not 48V path |

**PRIMARY HVAC:** Soft-mounted **12k BTU 115V or 230V high-SEER2 inverter mini-split** (heat pump), outdoor unit on reinforced bumper or frame tray, indoor high-wall; pair with **5 kVA Victron**.  
**ALT:** Cruise N Comfort / Nomadic **48V** split if owner prioritizes DC efficiency and accepts cost — **require manufacturer run-watt datasheet before bank finalization**.

### 3.3 Closed-cell spray foam upgrades

| Assembly | Target | Tag / caveats |
|---|---|---|
| Walls (stick-built) | Closed-cell **~R-6 to R-7 per inch** into cavities; avoid crushing wiring | `[I]` industry SPF values; RICS guide notes SPF is serious irreversible mod + fire class concerns `[S]` |
| Floor | Closed-cell against underbelly after vapor/rodent strategy | Moisture design required `[I]` |
| Roof | Closed-cell underskin **or** rigid foam + new membrane; do not trap leaks unseen | RICS: foam can hide wet timber `[S]` |
| Windows/doors | Low-E replacements + seals often beat raw R chasing | `[I]` |

**Net effect `[I]`:** 30–50% HVAC energy reduction vs stock TT fiberglass is a common conversion claim — **measure** with power logging after foam, do not bank on brochure R alone.

---

## 4. Galley (all-electric)

| Load | Primary choice | Power | Weight | Notes | Tag |
|---|---|---|---|---|---|
| Cooktop | **Flush 2-burner induction** (RV/marine) or portable 1800 W | **1200–1800 W**/burner typical; avoid full 30" residential (40A/240V, 39–49 lb) `[S]` | ~10–25 lb RV unit `[I]` | Soft-start / power-share with HVAC in Cerbo Node-RED or manual | Mixed |
| Oven | **Convection / speed oven** (e.g. 0.5–1.0 cu ft) | **1000–1800 W** while running `[I]` | ~30–50 lb `[I]` | Schedule off HVAC peak | `[I]` |
| Fridge | **12V or 48→12V compressor** (Dometic CFX-class / built-in Isotherm/Vitrifrigo class) | Average **~40–80 W**; peaks higher `[I]` (CFX3 does not expose watts in BLE `[S]`) | 40–100 lb `[I]` | Prefer DC; avoid absorption | Mixed |
| Water heat | **PRIMARY: 120V heat-pump WH** (compact) **or** **point-of-use under-sink** + small buffered tank | HPWH run hundreds of W; POU 1200–1500 W short duty `[I]` | HPWH heavy `[I]` | Put WH on MultiPlus **AC-out-2** (shore-only) when possible `[S]` Victron pattern | Mixed |
| Water heat alt | 6–10 gal 120V element tank | 1000–1500 W | Moderate | Simple; hungry off-grid | `[I]` |

### Why NOT diesel hydronic for this bible’s goal
- Reintroduces **liquid fuel**, tank, exhaust, carbon monoxide, and service complexity.
- Breaks **100% all-electric / zero-propane** stakeholder objective (plan constraint).
- Acceptable only as a **documented emergency experimental branch**, not primary heat.

---

## 5. Running gear upgrades

| Upgrade | Primary | Alt | Est. weight delta | Tag |
|---|---|---|---|---|
| Axles | **Dexter-class torsion** matched to GAWR | Leaf with better equalizers | Swap weight ~neutral to +50–100 lb `[I]` | `[I]` |
| Brakes | **Electric-over-hydraulic (EoH) discs** (Kodiak / Tie Down Engineering class) | Upgrade electric drums | Actuator + discs + fluid **~40–80 lb** `[I]` | `[I]` — verify axle flange compatibility |
| TPMS | Flow-through or valve sensors + trailer display / phone | Integrated with Cerbo GPIO alert `[I]` | ~2–5 lb | `[I]` |
| Sway / WD | **ProPride 3P** or **Hensley Arrow** for active geometry control | **Curt TruTrack** WD+sway for lighter/cost | Hitch heads commonly **~60–110 lb** class `[I]` — **weigh your SKU** | `[I]` |

**Tongue weight impact:** Batteries prefer **axle-centered / slightly aft of axle** underbelly or pass-through; heavy tongue hitch + forward batteries can exceed TV payload. **CAT scale every major weight change.**

---

## 6. Code / safety flags

| Topic | Guidance | Tag |
|---|---|---|
| Electrical | Follow **NEC Article 551** (RVs) + inverter manufacturer instructions; use dual-listed mobile gear where possible | `[I]` code pointer |
| RVIA | Factory certification void after major electrical/chassis mods; document as **owner rebuild** | `[I]` |
| Battery compartment | LiFePO4 ≠ vented lead-acid H₂ rules, but still need: **mechanical protection, Class-T fusing, BMS, thermal sensing, no crushed cells, escape path for smoke, extinguisher rated for lithium electrical** | `[I]` |
| Fire | Closed-cell polyurethane is combustible (RICS notes Class E-type concerns for PU foam) `[S]` — keep foam away from heat sources; follow ignition barriers where required | Mixed |
| Charge profiles | BMS closed-loop preferred; Victron absorb/float 57.6/55.2 V `[S]`; never Pb equalize | `[S]` |
| Shore / EVSE | Treat EVSE as **limited AC source**; set PowerControl amps; GFCI/breaker coordination | `[S/I]` |
| Structural | Roof penetrations, mini-split mounts, torsion axle swaps = **qualified shop** | `[I]` |

---

## 7. Estimated major component weights (planning)

| Component | Est. lb | Tag |
|---|---|---|
| 15 kWh LiFePO4 | 250–350 | `[I]` from module datasheets |
| 20 kWh LiFePO4 | 350–450 | `[I]` |
| Victron MultiPlus-II 3–5k + Cerbo + Lynx | 70–120 | `[I]` (+ EU sheet anchors `[S]`) |
| EG4 12000XP alone | 105 | `[S]` |
| Sol-Ark 15K alone | 135 | `[S]` |
| Roof solar 1.5 kW + rack | 100–180 | `[I]` |
| Mini-split 12k (both units) | 80–120 | `[I]` |
| Induction + speed oven + compressor fridge | 100–180 | `[I]` |
| EoH discs + actuator | 40–80 | `[I]` |
| Hensley/ProPride-class hitch | 60–110 | `[I]` |
| **Removed:** roof AC + furnace + propane tanks/appliances | **−150 to −300** credit | `[I]` |

**Net `[I]`:** Expect **+400 to +900 lb** vs stock depending on bank size — must fit inside GVWR and tongue %.

---

## 8. Structured recommendations (summary)

### Primary system (Lead-3 recommendation)
| Domain | Primary |
|---|---|
| Voltage / chemistry | **48V LiFePO4** |
| Capacity | **15 kWh now, bus ready for 20 kWh** |
| Inverter/charger | **Victron MultiPlus-II 48/5000 2x120V** (or 3000 if strict diet on concurrent loads) |
| Monitoring | **Cerbo + Lynx + BMS CAN** |
| Solar | **1.4–2.0 kW N-type roof** + deployable ground kit |
| Alternator | **Orion XS** 12→48 path |
| Shore | **50A inlet** + **J1772/NACS→AC-IN** via PowerControl |
| HVAC | **12k high-SEER2 mini-split heat pump** + closed-cell foam |
| Galley | Induction + convection/speed oven + DC compressor fridge + HPWH or POU |
| Chassis | Torsion axles + EoH discs + TPMS + ProPride/Hensley-class |

### Alternatives ladder
1. Quattro dual-in; 2. EG4 AIO budget; 3. EcoFlow turnkey; 4. 48V DC HVAC instead of mini-split; 5. 10 kWh bank only if mostly plugged-in.

---

## 9. DO NOT DO list

1. **Do not** keep propane “just for winter” if the bible goal is 100% electric — it freezes the architecture and safety model.
2. **Do not** use **diesel hydronic** as primary heat for this objective.
3. **Do not** install **Sol-Ark / large residential AIO** as default on a 27' TT without a weight and vibration engineering case.
4. **Do not** put **30 kWh** on the tongue or in the bathroom without CAT-scale proof.
5. **Do not** use **residential 500–650 W bifacial modules** as roof panels without verifying length/width/walk/wind.
6. **Do not** feed **CCS/NACS DC fast charge** into the house battery.
7. **Do not** run **induction + oven + HVAC max** without a load manager / AC-out-2 strategy.
8. **Do not** spray foam over active leaks or skip fire/ignition planning.
9. **Do not** rely on **Zero Breeze-class** or uncertified portable AC as the rebuild HVAC.
10. **Do not** assume **RecPro 48V** exists — not verified this pass; RecPro path observed is **120V Houghton-class**.
11. **Do not** skip **Class-T fusing**, battery disconnect, and BMS.
12. **Do not** claim exact GVWR/GAWR until axle and door stickers are photographed for this VIN.

---

## 10. Confidence & research limits

| Area | Status |
|---|---|
| Victron / EG4 / Sol-Ark datasheet numbers | Strong `[S]` this pass |
| EcoFlow Power Kit telemetry ceilings | Strong `[S]` (protocol); retail brochure weights partial |
| Mini-split watt ratings | Strong `[S]` (Hessaire/Grainger 2026 sheets) |
| Nomadic / CNC exact watts & weights | **Weak** — product existence `[S]`; specs `[U]` |
| Exact Prowler 272 GVWR for VIN | **`[U]`** — physical sticker |
| Hitch brand weights | **`[I]`** — weigh installed SKU |
| Spray foam R/inch | **`[I]`** typical closed-cell; RICS caveats `[S]` |

**Network note:** Agent egress allowlist blocked most manufacturer sites (e.g. nomadiccooling.com); results used GitHub + indexed datasheet PDFs.

---

## 11. Handoff to other leads / build bible

- Lead 1 (OEM anatomy): supply axle tag photos → lock GVWR table.  
- Lead 2 (structure/underbelly): battery bay location for tongue model.  
- Lead 4 (smart stack / UX): Cerbo/Node-RED load shed for induction↔HVAC.  
- Integrator: merge this file into five-part bible as **Part 3 — Energy & Chassis Electrification**.

---

*Lead Researcher 3 deliverable — Fleetwood Prowler all-electric off-grid territory.*
