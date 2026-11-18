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

> **Deep dive (Lead Researcher 2):** tagged claims, NHTSA IDs, strip inventory →  
> [`LR2_OEM_ELECTRICAL_PLUMBING_LP_HVAC.md`](./LR2_OEM_ELECTRICAL_PLUMBING_LP_HVAC.md)

#### Electrical (factory)
| Item | Best current evidence | Confidence |
|---|---|---|
| Shore power | **30A / 120V** TT-30 most common for this size/era; 50A rare unless heavily optioned. **VIN inlet = verify.** | `era_typical` / `unknown_verify` |
| Converter/charger | Integrated power center; **2003 Prowler OEM documented at 45 A** (NHTSA complaint 10051783). Brand Magnetek / PD / WFCO = **nameplate**. Siemens Q breakers recall **04V145000** on 2004 Fleetwood TT incl. Prowler. | `direct` amps (sister year) + `era_typical` brand window |
| House battery | Single Group 24/27 flooded lead-acid in tongue box or under dinette | `era_typical` |
| 12V distribution | Automotive-style fuse block; wiring in walls/floor voids, often stapled. **Pinched frame/floor wiring** documented on 2006 Prowler (complaint 10173668). | `era_typical` + `direct` failure mode |
| 120V distribution | Breaker panel in power center; Romex-like NM in coach (mobile practice of era) | `era_typical` |
| Chassis bonding | Frame bond + 7-pin trailer connector (lights, electric brakes, charge line ~16–18AWG weak) | `era_typical` |

#### Plumbing
| Item | Best current evidence | Confidence |
|---|---|---|
| Fresh / gray / black gallons | **No brochure recovered in research env.** Planning band ~30–50 / ~25–45 / ~25–45 gal — **not OEM fact for this VIN** | `unknown_verify` (+ `era_typical` band only) |
| Tank locations | Fresh often forward/mid; gray/black mid-aft under bath/galley | `era_typical` / `unknown_verify` |
| Supply | Transition era: **polybutylene or early PEX** — cut-test required; replace all with PEX in rebuild | `era_typical` / `unknown_verify` |
| Drain | ABS DWV with P-traps; dump valves mid-curbside | `era_typical` |
| Pump | 12V demand pump + accumulator sometimes | `era_typical` |
| Water heater | **6-gal** LP/electric (Atwood/Suburban) common; some 10-gal — **dataplate** | `era_typical` / `unknown_verify` |

#### LP / HVAC / appliances
| Item | Best current evidence | Confidence | Strip for EV? |
|---|---|---|---|
| LP bottles | Dual **20-lb** or **30-lb** on A-frame — measure tray | `era_typical` / `unknown_verify` | Yes — remove |
| Regulator / lines | Two-stage regulator → furnace, WH, range, fridge. Slide LP pinch recall **05V433000** (2004–05 **5th-wheel** Prowler) | `era_typical` + `direct` (5W subset) | Yes — purge & remove |
| Furnace | Forced-air LP **16–30k BTU** (Suburban/Atwood) — **dataplate** | `era_typical` / `unknown_verify` | Yes |
| Roof AC | **13.5k BTU** Coleman-Mach / Duo-Therm class common — **dataplate** | `era_typical` / `unknown_verify` | Yes |
| Cooktop/oven | LP range | `era_typical` | Yes |
| Refrigerator | Absorption **Dometic** two-door (**RM2652 / RM2852** documented on 2003–04 Prowlers); Norcold also used in Fleetwood fleet. Recalls **07V120000**, **08V320000**, equip. **06E076** | `direct` | Yes |
| Microwave | Samsung membrane-panel units on Fleetwood TT incl. Prowler — recall **03V452000** | `direct` | Strip / replace |
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

**Primary local-first path:** `Starlink Mini (bypass) + GL.iNet GL-X3000 (5G failover) → optional self-host bond → HA LAN`. Escalate to Peplink only if true multi-WAN bonding + support SLA is required. Avoid Cradlepoint/NetCloud unless a fleet already depends on it.

| Layer | Choice | Notes |
|---|---|---|
| LEO sat | **Starlink Mini** (~2.43 lb; **12–48 VDC**; typ. 15–40 W, ≤60 W) | Vibration-isolated roof mount; Ethernet → router WAN; **Bypass Mode**; in-motion needs Roam/Mobile Priority plan |
| Cellular | **GL-X3000** dual-SIM 5G (budget) or **Peplink MAX BR1 / Transit Duo** (prosumer) + MIMO antennas | Failover/load-balance first; true aggregation via self-hosted OpenMPTCP/tailbond/FusionHub |
| Edge | **Mini-PC HAOS** preferred (Frigate headroom); HA Yellow/Green OK for control-only | PoE switch; Mosquitto on-LAN; Tailscale/WireGuard optional remote |
| Matter / Thread | HA Matter Server + OTBR (**Connect ZBT-2** or Yellow radio) | Local commission; some vendors still require cloud *first* pairing — pick devices that don’t |
| NVR | **Frigate** + Coral TPU + go2rtc on mini-PC | RTSP cams only; vendor cloud disabled |
| Victron bridge | Cerbo → MQTT → HA | Battery/solar as first-class entities |
| Dish admin path | Static/management route to `192.168.100.1` when dish is bypassed behind router | Required for HA Starlink integration |

```text
Starlink Mini ──► GL-X3000 / Peplink ◄── 5G dual-SIM
                      │
                 Trailer LAN
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   HAOS mini-PC   Frigate+Coral   Cerbo (MQTT)
         │
   WLED / locks / ESPHome panels / level sensors
```

### 3.2 Interior tech & UX

- **Lighting:** SK6812 **RGBW** cove via **WLED**/ESP32 + HA circadian Kelvin schedule (not rainbow party mode as default).  
- **Privacy:** **Hybrid** — motorized cellular/blackout shades in sleep zones (thermal); **PDLC** (about 5 W/m² or less) for wet bath / projector wall (fails opaque = good privacy).  
- **Work/gaming:** Fold-down or rail desk; ultrawide on **gas-spring arm** with transit lock; concealed raceways; **USB-C PD 3.1 140 W (28 V × 5 A)** via e-marked cables — practical path is dedicated 140 W brick/dock on a known circuit until true in-wall 140 W receptacles are common.  
- **Touch UX:** Wall tablet (Fully Kiosk) and/or ESP32-S3 LVGL panels = coach OS; phone is remote.  
- **AV:** Soundbar + short-throw projector; local media (Jellyfin/Plex on mini-PC); HA `media_player` preferred over Alexa-primary bars.  
- **Access:** **Nuki** (or RV-rated equivalent) + ESPHome BLE/MQTT local path + NFC/keypad; mechanical key override mandatory.  
- **Security:** Hitch/rear/curbside/roadside RTSP cams → Frigate; tow-away geofence; local SSD retention.  
- **Leveling:** **Lippert Ground Control TT** (~$2.5–4.5k installed, heavier) or SteadyFast-class manual ($400–1.2k); HA status only — physical panel remains primary; never remote-actuate slides/awning.

**UX principle:** Cloud is optional sync only. Lights, HVAC setpoints, locks, and dumps must work with WAN unplugged.

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
| Disc brake conversion | +20 to +80 (often near-neutral vs drums) |
| Auto-level (GC TT class) | +150 to +300 |
| Manual stabilizers (SteadyFast class) | +40 to +120 |
| Smart tech + HA/NVR + panels + cams | +20 to +50 |
| Insulation foam (net) | +40 to +120 |
| **Subtotal additions** | **≈ +810 to +1,450** |

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

#### Smart-stack detail (within the smart-tech line)

| Slice | DIY parts | Notes |
|---|---:|---|
| Starlink Mini + GL-X3000 | ~$900–1,200 | Peplink path adds ~$1–2k hardware |
| HA mini-PC + ZBT-2 + Coral + panels + WLED | ~$400–1,200 | Green-only control plane cheaper, less NVR headroom |
| Cams + Frigate host extras | ~$300–800 | RTSP only |
| Nuki + biometric/NFC path | ~$250–450 | Keep local BLE/MQTT |
| Leveling SteadyFast → GC TT | ~$400–1,200 → $2,500–4,500 | Weight rises sharply with auto kits |

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
- **LR2 systems topology:** [`LR2_OEM_ELECTRICAL_PLUMBING_LP_HVAC.md`](./LR2_OEM_ELECTRICAL_PLUMBING_LP_HVAC.md) — NHTSA recalls/complaints for Fleetwood Prowler MY≈2000–2006 (converter 45 A sister-year; Dometic RM2652/RM2852; Samsung MW; Siemens Q breakers; pinched chassis wiring; shore-fire complaint). Flat files: `flotwig/nhtsa-data`.  
- Victron MultiPlus-II datasheet (48V high-power hybrid inverter class).  
- joshgubler/trailer-build — 48V bank placement vs tongue weight; mini-split ~400–1000 W.  
- PaulGilchrist/off-grid — Victron travel-trailer integration patterns (24V analog).  
- divergent-futures/hw-slipstream — 48V Victron spine / aero all-electric trailer design values (greenfield analog).  
- Home Assistant Thread/Matter/Starlink docs — local-first stack.  
- HA core#95695 — Starlink Mini/dish behind Peplink routing pattern.  
- Lead research artifact `04_LEAD4_smart_tech_design_bom.md` — router tiers, Mini power/weight, Frigate/HA split, PDLC vs shades, BOM slices.  
- Lead research artifact `03_LEAD3_all_electric_offgrid_conversion.md` — 48V conversion detail.

---

## Mandatory next field actions

1. Photograph certification label + axle plates; fill unknowns in §1.  
2. Empty CAT scale ticket.  
3. Moisture map + endoscope into wall cavities at windows.  
4. Decide axle rating reality (3,500 vs 4,400) before locking battery kWh.  
5. Freeze power architecture (Victron 48/5000 2x120V + 16–20 kWh) unless scales forbid.

*End of bible v1 — update tables in-place when sticker evidence arrives.*
