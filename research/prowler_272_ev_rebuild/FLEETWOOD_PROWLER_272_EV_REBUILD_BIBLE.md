# Fleetwood Prowler 272 — 100% All-Electric Rebuild Bible (2026 Standard)

**Platform:** Bumper-pull tandem-axle travel trailer  
**VIN:** `1EA1F272941595598`  
**Factory identity (decoded):** Fleetwood WMI `1EA` · series token `272` · model-year code `4` → **2004** · plant `1` · serial `595598`  
**Title/insurance note:** Reported titled/insured as **2013** — treat as registration anomaly; **do not** use title year for OEM construction assumptions.  
**Document class:** Engineering planning bible (not a stamped PE package)  
**Environment basis:** US travel-trailer rebuild constrained by OEM stick-built shell mass, dual-axle GAWR class, and mobile lithium/NEC-adjacent practice. Remote OEM brochure/NHTSA APIs were unavailable in the research environment; exact sticker values are gated to physical inspection.

### Confidence legend
| Tag | Meaning |
|---|---|
| `vin_structural` | Derived from VIN character positions |
| `era_typical` | Strong pattern for early-2000s Fleetwood stick-built travel trailers of this size |
| `analogical` | From comparable trailer rebuilds / modern product datasheets |
| `inferred` | Engineering inference for this footprint |
| `unknown_verify` | Must read door sticker / axle plate / open structure |

---

## Part 1 — Inside-Out OEM Anatomy & Structural Teardown Specs

### 1.0 VIN & platform identity

| Field | Value | Confidence |
|---|---|---|
| WMI | `1EA` — Fleetwood Enterprises trailer family | `vin_structural` |
| Series token | `272` embedded in VDS (`…1F272…`) → 272-series / ~27' floorplan family (27H/270-class) | `vin_structural` + `era_typical` |
| Model year | Position 10 = `4` → **2004** | `vin_structural` |
| Check digit / plant / serial | `9` / `1` / `595598` | `vin_structural` |
| Exact floorplan letter (H vs other) | Not recoverable from VIN alone | `unknown_verify` |
| Exact UVW / GVWR / hitch | On federal certification label (door/entry) + VIN plate | `unknown_verify` |

**Physical verification gate (do this before buying batteries):**
1. Photograph federal certification label: GVWR, GAWR-each, tires/PSI, UVW if printed.
2. Photograph both axle ID tags (Dexter/Lippert): capacity, brake type, spring center.
3. Photograph A-frame / coupler rating stamp and LP bottle tray mounts.
4. Measure exterior box L×W×H and roof clear flat area (excluding AC/vents).
5. Open underbelly: confirm joist direction, tank locations, and whether frame is C-channel ladder.

### 1.1 Chassis & running gear

| Attribute | Era-typical 2004 Fleetwood ~27' bumper-pull | Confidence | Rebuild note |
|---|---|---|---|
| Frame type | Hot-rolled **steel ladder** with **C-channel** main rails (not I-beam), stamped/welded outriggers | `era_typical` | Inspect welds at A-frame junction, outrigger tips, axle hangers |
| Main rail size | Commonly ~6–8" C-channel in this class; **exact gauge/web unknown without measurement** | `unknown_verify` | Caliper web/flange; ultrasonic thickness if rusted |
| Outriggers | Cross-members + outriggers supporting floor edge / slide if equipped; spacing often ~16–24" | `era_typical` | Critical if adding battery trays / torsion axle hangers |
| Axles | Dual **Dexter** (or Dexter-licensed) **leaf-spring** axles | `era_typical` | Read tags: **3,500 lb ×2** most common; some packages **4,400 lb ×2** |
| GAWR implication | Dual 3,500 → ~7,000 lb axle sum (trailer GVWR often slightly lower) | `inferred` | Never exceed lesser of GVWR vs sum GAWR |
| Suspension | Multi-leaf spring with equalizer, shackle hangers | `era_typical` | Leaf packs fatigue; bushings ovalize |
| Hubs / brakes | **10" electric drum** common; 12" on heavier packages; 5-lug or 6-lug depending axle | `era_typical` | Magnets, shoes, bearings are wear items — replace during rebuild |
| Coupler | 2-5/16" ball typical for this weight class | `era_typical` | Verify stamped rating ≥ GVWR |
| Jack | Manual A-frame jack OEM | `era_typical` | Upgrade later to electric / auto-level |
| Dry / hitch / GVWR | **Must read sticker.** Planning band for similar 27' Fleetwood stick-builts: UVW ~5,200–6,400 lb; hitch ~10–14% UVW; GVWR ~7,000–7,600 lb | `era_typical` | CAT-scale empty + loaded after rebuild |

### 1.2 Floor, wall & roof construction

This generation of Prowler was a **budget/mid stick-and-tin** product, not a welded aluminum cage coach.

#### Floor
| Layer | Typical OEM | Confidence |
|---|---|---|
| Joists | Dimensional lumber (often 2×3 / 2×4) spanning main rails / outriggers | `era_typical` |
| Spacing | ~16" o.c. common | `era_typical` |
| Decking | 5/8" or 3/4" **plywood or OSB** | `era_typical` |
| Finish floor | Vinyl / carpet / linoleum over underlayment | `era_typical` |
| Underbelly | Corrugated plastic / Darco / “Coroplast-like” enclosure; sometimes incomplete | `era_typical` |
| Insulation | Fiberglass batts or thin foam; **low effective R** once compressed/wet | `era_typical` |
| Tanks | Fresh often forward/mid; gray/black mid-aft under bath/galley | `era_typical` + `unknown_verify` |

#### Walls
| Attribute | Typical OEM | Confidence |
|---|---|---|
| Method | **Stick-built wood studs** (“stick-and-tin”), not welded aluminum cage | `era_typical` |
| Studs | 2×2 / 1.5" nom. verticals, often 16" o.c. | `era_typical` |
| Exterior skin | **Corrugated aluminum** or thin Filon/fiberglass over lauan (varies by trim year) | `era_typical` |
| Interior | Lauan / decorative panelboard stapled to studs | `era_typical` |
| Insulation | Fiberglass; marketed R-values often **optimistic** (thermal bridging through studs) | `era_typical` |
| Windows | Framed radius-corner acrylic/glass; gasket failure common | `era_typical` |

#### Roof
| Attribute | Typical OEM | Confidence |
|---|---|---|
| Structure | **Wood rafters/trusses** (not aluminum) | `era_typical` |
| Decking | Thin lauan / OSB / plywood sheet | `era_typical` |
| Membrane | **EPDM** rubber dominant in early-mid 2000s (TPO later industry shift) | `era_typical` |
| Edge | Aluminum drip rail / termination bar; prime leak path | `era_typical` |
| Penetrations | Roof AC, bath fan, fridge vent, antenna — all leak risks | `era_typical` |

### 1.3 OEM systems topology

#### Electrical (factory)
| Item | Era-typical | Confidence |
|---|---|---|
| Shore power | **30A / 120V** TT-30 most common for this size/era; 50A rare unless heavily optioned | `era_typical` |
| Converter/charger | Integrated power center (WFCO / Progressive Dynamics / Magnetek-era) ~35–55A 12V | `era_typical` |
| House battery | Single Group 24/27 flooded lead-acid in tongue box or under dinette | `era_typical` |
| 12V distribution | Automotive-style fuse block; wiring in walls/floor voids, often stapled | `era_typical` |
| 120V distribution | Breaker panel in power center; Romex-like NM in coach (mobile practice of era) | `era_typical` |
| Chassis bonding | Frame bond + 7-pin trailer connector (lights, electric brakes, charge line ~16–18AWG weak) | `era_typical` |

#### Plumbing
| Item | Era-typical | Confidence |
|---|---|---|
| Fresh tank | ~30–50 gal depending floorplan | `era_typical` / `unknown_verify` |
| Gray / black | ~25–45 gal each typical | `era_typical` / `unknown_verify` |
| Supply | Transition era: many still **polybutylene** or early **PEX**; fittings crimp/clamp | `era_typical` |
| Drain | ABS DWV with P-traps; dump valves mid-curbside | `era_typical` |
| Pump | 12V demand pump + accumulator sometimes | `era_typical` |
| Water heater | **6-gal** LP/electric (Atwood/Suburban) common; some 10-gal | `era_typical` |

#### LP / HVAC / appliances
| Item | Era-typical | Confidence | Strip for EV? |
|---|---|---|---|
| LP bottles | Dual **20-lb** or **30-lb** on A-frame | `era_typical` | Yes — remove |
| Regulator / copper-steel lines | Two-stage regulator → furnace, WH, range, fridge | `era_typical` | Yes — purge & remove |
| Furnace | Forced-air LP **16–30k BTU** (Suburban/Atwood) | `era_typical` | Yes |
| Roof AC | **13.5k BTU** Coleman-Mach / Duo-Therm class, loud | `era_typical` | Yes |
| Cooktop/oven | LP range | `era_typical` | Yes |
| Refrigerator | Absorption Dometic/Norcold LP/120V/12V | `era_typical` | Yes |
| Water heater | LP/electric tank | `era_typical` | Yes (replace electric) |

### 1.4 Known weak points & inspection priorities (this generation)

Prioritize these **before** any power or finish work:

1. **Roof membrane edges & termination bar** — chronic EPDM edge lift → wall top-plate rot.  
2. **Window buck seals & corner moldings** — water into stud cavities → delamination / soft walls.  
3. **Bath fan / skylight flanges** — soft ceiling decking.  
4. **Front cap / rock guard junction** — road spray + flex cracks.  
5. **Slide seals & roll-out (if equipped)** — floor delam at slide aperture.  
6. **Subfloor at galley / bath** — gray tank condensation + plumbing leaks.  
7. **Outrigger-to-floor fasteners** — rusted screws; soft edge.  
8. **A-frame / coupler welds & spring hangers** — fatigue cracks, elongated bolt holes.  
9. **Axle spring center & equalizer bushings** — wandering tracking, tire wear.  
10. **Polybutylene fittings** — brittle failure risk; replace entire supply with PEX-A/B.  
11. **Corrugated aluminum oil-canning / fastener pull-through** — exterior aesthetic + leak paths.  
12. **Underbelly “mouse highways”** — chewed wiring/insulation; reseal completely.

**Teardown decision rule:** If >30% of wall studs or >40% of subfloor show soft/rot, treat as **shell-off / reframe** candidate rather than patch-in-place. Otherwise: selective panel peel, sister studs, full subfloor sheet replacement in wet zones.

---

## Part 2 — 100% All-Electric Conversion & Mechanical Modernization

### Design equation (this trailer)
`(27' stick-built envelope)` × `(dual-axle ~7k-class GVWR)` × `(zero propane)` × `(HVAC + induction simultaneous)`  
→ **48V LiFePO4 spine**, **5–6 kVA hybrid inverter**, **heat-pump HVAC**, **roof + deployable PV**, **weight-managed battery placement**.

### 2.1 Recommended 48V high-capacity power architecture

#### Primary recommendation (professional RV-grade)
| Layer | Spec | Rationale |
|---|---|---|
| Battery | **16–20 kWh** LiFePO4 @ 48V nominal (e.g. 2× 48V 200Ah server-rack or RV-rated modules ≈ 19–20 kWh) | Covers overnight heat-pump + fridge + electronics; induction bursts via inverter |
| Alternate compact | **10–12 kWh** if strictly fair-weather / shore-frequent | Lighter tongue; less autonomy |
| Alternate expedition | **24–30 kWh** only if axle tags ≥4,400 lb ×2 **and** tongue model closes | Heavy; often wrong for OEM 3,500s |
| Inverter/charger | **Victron MultiPlus-II 48/5000/70-50 2x120V** (US) or Quattro 48/5000 | True hybrid, PowerAssist, dual 120V, Cerbo ecosystem; mobile-proven |
| Alt inverter | EG4 6000XP / similar 48V AIO | Lower $/W; heavier integration DIY burden; verify mobile vibration mounts |
| Alt all-in-one kit | EcoFlow Power Kit / newer 2026 PowerOcean-class kits | Faster install; more cloud coupling — conflict with local-first unless bridged |
| Solar charge | Victron **MPPT 150/70 or 250/70–100** (array Voc dependent) | Matches panel stringing |
| BMS / telemetry | Module BMS + **Victron SmartShunt or Lynx Shunt** + **Cerbo GX / Ekrano** | Local MQTT → Home Assistant |
| 12V house | Orion XS / Orion-Tr **48→12** isolated converter (30–60A) feeding cleaned 12V bus | Keep LED, pumps, brakes, fans on 12V |
| Protection | Class-T or Mega fuse at pack, midnite/ Victron DC distribution, dual-pole battery disconnect, AFCI/GFCI on AC as required | Fail closed |

**US shore / EVSE note:** Use inverter AC-in from **TT-30 or 14-50**. For J1772/NACS “shore,” use an **EVSE → portable 14-50 / hardwired charger input** strategy (you are charging the *house bank*, not a traction pack). Do not backfeed EVSE pins.

#### Power budget (planning)

| Mode | Loads | Demand |
|---|---|---|
| Idle / camping quiet | LED, router, HA, fridge compressor, USB | ~80–150 W |
| Comfort cruise | Above + mini-split maintain | ~400–900 W (climate dependent) |
| Peak coincident | Induction 1.8 kW + mini-split 1.0–1.5 kW + oven/microwave surge | **3.0–4.5 kW** → size inverter ≥5 kVA |
| Daily energy (mild) | Comfort + cooking + work | ~6–10 kWh/day |
| Daily energy (hot/cold extreme) | Heat pump hard work | ~12–18 kWh/day |

**Autonomy target:** 16–20 kWh usable @ 80–90% DoD → **~1.0–1.5 days** without sun in mild weather; deployable PV + tow DC-DC extends.

#### Solar & charging
| Source | Target | Notes |
|---|---|---|
| Roof array | **1.2–2.0 kW** high-efficiency N-type/TOPCon (or bifacial if rack air gap) | 27' roof after vents ≈ limited; low-profile flush mounts; reinforce rafters |
| Deployable | **800–1600 W** suitcase / blanket | Critical for trees / winter |
| Tow vehicle DC-DC | Victron Orion XS **48V** or 12→48 boost architecture from dual-alt truck | Size to alternator thermal limits |
| Shore | 30A PowerControl → upgrade inlet to **50A 14-50** when rewiring | PowerAssist covers peaks on 30A |

### 2.2 All-electric HVAC & thermal envelope

| Remove | Replace |
|---|---|
| Roof AC (13.5k) | **Primary:** 12k–18k BTU **inverter mini-split** (high SEER / HSPF), outdoor unit on reinforced bumper or frame-tied bracket (see joshgubler analog: Pioneer ~400–1000 W) |
| LP furnace | Mini-split heat pump + optional **48V DC rooftop heat pump** (Nomadic Cooling / Cruise N Comfort class) as redundant low-profile path |
| Fiberglass batts | **Closed-cell spray foam** or rigid polyiso + foam-in cavities; air-seal windows/doors |

**Envelope targets (inferred for stick-built rebuild):**
- Walls: effective **R-15–R-21** with thermal-break strategy  
- Roof: **R-21–R-30**  
- Floor: **R-15–R-21** + sealed underbelly  
Without envelope work, electric HVAC will punish the battery bank.

### 2.3 All-electric galley & water

| Function | Primary pick | Why |
|---|---|---|
| Cooktop | Flush **induction** 1800 W (2-burner share circuit) | Efficient, cool surface |
| Oven | 120V convection / speed oven | Avoids LP |
| Fridge | 12V or 48V **compressor** (Isotherm/Vitrifrigo/unique) | 1/5 the energy of absorption |
| Water heat | **Point-of-use electric** under sink + optional small **heat-pump WH** if space | Tank resistive (1500 W) only on AC-in or surplus solar |
| Avoid as primary | Diesel hydronic | Breaks zero-fossil / all-electric objective (ok only as emergency winter contingency, isolated) |
| Dump valves | Motorized gray/black (e.g. Valterra-style actuators) + **ultrasonic** tank sensors | HA automation |
| Fresh water | Multi-stage carbon + sediment + **UV** | City & tank modes |
| Plumbing redo | Full **PEX** supply, new ABS drains as needed | Kill poly-B |

### 2.4 Running gear & towing upgrades

| Upgrade | Spec | Priority |
|---|---|---|
| Axles | Matched **Torflex / torsion** or new Dexter leaf @ verified GAWR | High if bearings/springs shot |
| Brakes | **Electric-over-hydraulic disc** (Kodiak / Tie Down Engineering kits) | High — stopping with batteries aboard |
| TPMS | Internal or belt-on sensors → HA/Bluetooth | High |
| Sway | Passive hitch (**ProPride / Hensley**) or active WD sway (**Curt TruTrack** class) | High |
| Suspension assist | Wet bolts, new equalizer, or Timbren/MorRyde if keeping leaf | Medium |
| Tires | Load Range E, date-coded <6 yr, correct GAWR | Critical |

---

## Part 3 — 2026 Futuristic Smart-RV Tech Stack (Local-First)

### 3.1 Connectivity & edge compute

| Layer | Choice | Notes |
|---|---|---|
| LEO sat | **Starlink Mini** roof mount; vibration-isolated; in-motion plan compliance | Mount with clear sky; cable to router WAN |
| Cellular | **Peplink MAX** / Cradlepoint / GL.iNet 5G with external MIMO antennas | Bond Starlink + 5G; failover |
| Edge | **Home Assistant OS** on HA Yellow **or** mini-PC (NUC-class) + PoE switch | Local automations; no cloud lock-in |
| Matter / Thread | HA Matter Server + OTBR (Yellow / Connect ZBT-2) | Commission Thread devices locally |
| Victron bridge | Cerbo → MQTT → HA | Battery/solar as first-class entities |
| Starlink via Peplink | Add WAN management route to `192.168.100.1` if dish bypassed | Documented HA/Peplink pattern |

### 3.2 Interior tech & UX

- **Lighting:** Addressable RGBIC cove (WLED / ESP32) + tunable white circadian scenes in HA.  
- **Privacy:** Motorized shades (primary) or **PDLC** film on selected windows (power draw + wiring complexity).  
- **Work/gaming:** Fold-down or rail-mounted desk; ultrawide on **gas-spring arm**; concealed raceways; **USB-C PD 3.1 (140W)** outlets at desk/bed/lounge.  
- **AV:** Soundbar + short-throw or ultra-short-throw projector on blackout scene; local media (Plex/Jellyfin on same mini-PC).  
- **Access:** RV-rated **NFC/keypad** deadbolt + optional biometric (keep mechanical key override).  
- **Security:** 360° / multi-cam (front hitch, rear, curbside, roadside) → NVR local SSD; tow-away geofence.  
- **Leveling:** Lippert Ground Control / equivalent auto-level; HA status only (keep vendor controller for safety).  

**UX principle:** One wall tablet (Fully Kiosk) = “coach OS”; phone is remote; cloud is optional sync, never required for lights/HVAC/locks.

---

## Part 4 — Exterior & Interior Industrial Design Overhaul

### 4.1 Exterior (dated box → 2026 object)

| Move | Detail |
|---|---|
| Skin | Prefer **smooth composite / aluminum flat panel** over corrugated; or high-quality architectural vinyl wrap if structure sound |
| Graphics | Full de-chrome / delete 2000s swooshes |
| Windows | **Frameless** dark tint replacements (Hehr/Lippert ecosystem) |
| Nose | Modern rock guard + subtle aero fairing; LED strip under lip |
| Awning | Black cassette awning with integrated LED |
| Roof rack | Dark powdercoat crossbars for solar/Starlink (load into reinforced hard points) |
| Wheels | Blacked-out alloys matching new bolt pattern after axle work |
| Lighting | Slim LED tail/marker; sequential legal where allowed |

**Visual direction (anti-slop):** Graphite / bone / single accent (electric teal *or* oxide orange — pick one). Avoid purple nebula wraps, excessive gloss black piano, and sticker clutter.

### 4.2 Interior materials & 27' layout

| Element | Spec |
|---|---|
| Cabinetry | CNC birch ply / lightweight composite / aluminum extrusion skeletons — **not** solid oak boxes |
| Counters | Thin solid surface or micro-cement over honeycomb/foam core |
| Floor | Waterproof LVP or woven vinyl; full-spread adhesive |
| Soft goods | Performance fabric, wipeable |
| Bath | Wet-bath refresh: wall-hung or compact ceramic, wand shower, continuous waterproof membrane |

**Layout pattern for tech-adult 27':**
1. Open galley mid-coach facing lounge  
2. Convertible dinette → guest bed  
3. Rear or front queen with storage + battery bay under (weight-tuned)  
4. Dedicated **1.2–1.5 m work desk** zone with cable spine  
5. Minimal upper cabinets (visual lightness + mass reduction)

---

## Part 5 — Weight Budget, Phased Build Order & BOM

### 5.1 Weight audit (planning model)

> **Rule:** Until CAT-scale + sticker numbers exist, treat this as a **delta model**, not absolute mass.

#### Removals (typical ranges)

| Item | Δ lb (approx.) |
|---|---:|
| Dual LP bottles + regulator/lines | −60 to −100 |
| LP furnace | −50 to −80 |
| Absorption fridge | −100 to −150 |
| LP range/oven | −40 to −70 |
| Roof AC | −80 to −110 |
| Water heater (tank gas/electric) | −60 to −90 |
| Heavy wood cabinetry (partial) | −150 to −400 |
| Generator (if any) | −100 to −250 |
| **Subtotal removals** | **≈ −640 to −1,250** |

#### Additions (recommended package)

| Item | Δ lb (approx.) |
|---|---:|
| 16–20 kWh LiFePO4 + rack | +280 to +420 |
| Inverter/charger + bus + cabling | +70 to +120 |
| Solar 1.5–2.0 kW + rack | +80 to +140 |
| Mini-split + bracket | +90 to −20 net vs old AC (often near wash) |
| Compressor fridge | +60 to +100 |
| Induction + convection | +40 to +70 |
| Disc brake conversion | +40 to +80 |
| Auto-level / jacks | +80 to +160 |
| Smart tech + panels + cams | +30 to +60 |
| Insulation foam (net) | +40 to +120 |
| **Subtotal additions** | **≈ +810 to +1,350** |

**Net:** Often **+0 to +400 lb** vs starting UVW for a disciplined build — **or worse if cabinetry isn’t lightweighted**. Battery location dominates tongue %.

**Tongue strategy (from analog rebuilds):** Place pack near axle line / slightly forward of axle; joshgubler documented ~200 lb tongue change by moving batteries ~5 ft. Target **10–15% of total trailer weight** on coupler at loaded camp posture.

**Hard stops:**
- Sum of axle-scale weights ≤ GVWR  
- Each axle ≤ GAWR  
- Coupler load ≤ tow-vehicle payload & hitch rating  
- After rebuild: empty CAT scale, then loaded “camp-ready” CAT scale  

### 5.2 Sequenced build roadmap

1. **Document & weigh** — stickers, photos, empty CAT scale, moisture meter map.  
2. **Decommission** — purge LP, disconnect 120V/12V, remove appliances, tanks if replacing.  
3. **Strip to structure** — interior skin as needed; expose floor/walls/roof leaks.  
4. **Chassis & running gear** — frame repair, axle/brake/tire package, A-frame.  
5. **Envelope repair** — sister studs, subfloor, roof deck, new membrane or panel skin.  
6. **Insulation & seal** — closed-cell / polyiso; window bucks; underbelly.  
7. **Rough-in** — 48V spine, AC subpanel, PEX, drains, data (Cat6), low-voltage.  
8. **Set major systems** — battery bay, inverter, HVAC, water heater strategy.  
9. **Cabinetry & finishes** — lightweight modules, floor, solid surface.  
10. **Smart stack** — HA, Thread/Matter, lighting, cams, locks.  
11. **Commissioning** — Victron config, torque checklist, GFCI/AFCI tests, brake controller gain, water pressure test, 48h energy trial.  
12. **Validation weigh** — CAT scale empty + loaded; adjust ballast/battery position.

### 5.3 Ballpark BOM (USD, 2025–2026 street)

| Subsystem | DIY range | Pro-installed range |
|---|---:|---:|
| Structural / exterior skin / roof / windows | $8k–$25k | $18k–$45k |
| 48V power / solar / inverter / battery | $10k–$22k | $16k–$30k |
| HVAC / plumbing / tanks / filtration | $4k–$10k | $8k–$16k |
| Running gear / brakes / hitch / tires | $3k–$9k | $5k–$12k |
| Smart tech / networking / cams / HA | $2k–$6k | $3k–$8k |
| Interior finishes / cabinetry / furniture | $6k–$18k | $12k–$35k |
| **Total** | **~$33k–$90k** | **~$62k–$146k** |

Excludes donor trailer cost, shop rent, and “surprise rot” contingency (**add 15–30%**).

---

## Do-not-do list

1. Do not keep polybutylene supply.  
2. Do not hang 20 kWh on the A-frame.  
3. Do not run induction + resistive water heater + old roof AC on a 3kVA inverter.  
4. Do not skip frame inspection before torsion axle drill pattern.  
5. Do not cloud-lock locks/HVAC with no local fallback.  
6. Do not claim 2013 construction methods because of title year.  
7. Do not spray foam over active leaks.  
8. Do not use residential non-mobile LiFePO4 without vibration/vent/fastening plan.

---

## Sources & analogs (non-exhaustive)

- VIN structure decoded from `1EA1F272941595598` (WMI/year/series tokens).  
- Victron MultiPlus-II datasheet (48V high-power hybrid inverter class).  
- joshgubler/trailer-build — 48V bank placement vs tongue weight; mini-split ~400–1000 W.  
- PaulGilchrist/off-grid — Victron travel-trailer integration patterns (24V analog).  
- divergent-futures/hw-slipstream — 48V Victron spine / aero all-electric trailer design values (greenfield analog).  
- Home Assistant Thread/Matter/Starlink docs — local-first stack.  
- HA core#95695 — Starlink Mini/dish behind Peplink routing pattern.

---

## Mandatory next field actions

1. Photograph certification label + axle plates; fill unknowns in §1.  
2. Empty CAT scale ticket.  
3. Moisture map + endoscope into wall cavities at windows.  
4. Decide axle rating reality (3,500 vs 4,400) before locking battery kWh.  
5. Freeze power architecture (Victron 48/5000 2x120V + 16–20 kWh) unless scales forbid.

*End of bible v1 — update tables in-place when sticker evidence arrives.*
