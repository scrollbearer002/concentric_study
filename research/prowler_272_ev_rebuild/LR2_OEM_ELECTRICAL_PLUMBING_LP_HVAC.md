# Lead Researcher 2 of 4 — OEM Electrical / Plumbing / LP / HVAC Topology

**Target coach:** ~2004 Fleetwood Prowler 27' tandem-axle travel trailer (272 / 27H / 270 class)  
**VIN:** `1EA1F272941595598`  
**Territory:** Factory 12V/120V, fresh/gray/black plumbing, LP gas, HVAC & OEM appliances (strip inventory)  
**Research date:** 2026-11-18  
**Document role:** Evidence layer for `FLEETWOOD_PROWLER_272_EV_REBUILD_BIBLE.md` §1.3 / §5.1  

### Environment basis
- **System of interest:** OEM coach systems on Fleetwood Enterprises Prowler stick-built travel trailers MY ~2003–2006, focused on the VIN’s `…F272…` + year-code `4` identity.  
- **Runtime environment:** Cursor Cloud Agent with **restricted egress**. Direct fetches to `vpic.nhtsa.dot.gov`, `nhtsa.gov`, RVTrader, iRV2, ManualsLib, and most OEM sites **failed**.  
- **What worked:** GitHub-hosted NHTSA flat files (`flotwig/nhtsa-data` recalls + complaints CSVs, years 2000–2008) + Cursor WebSearch (heavily polluted by SEO spam manuals — those spam hits are **not** treated as sources).  
- **Implication:** Claims below are tagged honestly. Exact brochure gallonages / converter brand for *this VIN* remain **`unknown`** until sticker / placard / physical open-up.

### Claim tags (per charter)
| Tag | Use |
|---|---|
| `direct_in_domain_support` | Fleetwood Prowler MY≈2003–2006 evidence (NHTSA recall/complaint naming Prowler) |
| `analogical_support` | Same OEM family / same RV industry generation, not this floorplan |
| `inferred` | Engineering inference from class norms + VIN structure |
| `unknown` | Not established by reachable primary sources — **do not invent** |

---

## 0. VIN / platform anchors

| Claim | Tag | Source |
|---|---|---|
| Position 10 = `4` → model year **2004** | `direct_in_domain_support` | VIN `1EA1F272941595598` |
| VDS contains `F272` → 272-series / ~27' family | `inferred` | VIN structure; twin VINs in NHTSA complaints use `…F272…` on 2004 Prowlers (e.g. `1EC1F272944`, `1EC1F272242`) |
| WMI `1EA` is Fleetwood Enterprises trailer family | `inferred` | Consistent with project bible + Fleetwood WMI practice; **NHTSA vPIC decode blocked** in this environment — re-verify on nhtsa.gov |
| Exact floorplan letter (27H vs Regal 270 vs other) **not** encoded beyond series token | `unknown` | VIN alone insufficient |
| “Prowler Regal **270**” existed as a 2004 Fleetwood floorplan name | `direct_in_domain_support` | NHTSA complaint **10158411** (“2004 PROWLER REGAL 270”) |
| One 2004 Prowler TT owner reported **GVWR 6600 lb** and B-rated tires insufficient vs that GVWR | `direct_in_domain_support` | NHTSA complaint **10146248** — *that coach’s sticker*, not proven for this VIN |

**Physical gate before locking strip weights:** photograph federal cert label, axle tags, LP tray stamps, power-center nameplate, water-heater rating plate, roof-AC dataplate, fridge dataplate.

---

## 1. Factory 12V DC / 120V AC

### 1.1 Shore power — 30A vs 50A

| Claim | Tag | Notes / source |
|---|---|---|
| Mid-2000s ~27' single-roof-AC travel trailers were **almost always TT-30 (30A / 120V)** from the factory | `analogical_support` | Industry class pattern; no brochure for this VIN recovered |
| 50A / 240V split shore was uncommon on this size/era unless dual AC or heavy residential options | `analogical_support` | Same class pattern |
| **This VIN’s inlet rating** | `unknown` | Read inlet / breaker main: 30A main ⇒ 30A shore; dual-pole 50A ⇒ 50A |
| Shore/inlet wiring can fail catastrophically | `direct_in_domain_support` | NHTSA complaint **10232011** (2006 Fleetwood Prowler): electrical fire attributed to “main wire” plugged into the shore box |

**Rebuild implication:** Plan rewire as if replacing a **30A power center** unless inspection proves 50A. Upgrading inlet to 14-50 is a conversion choice, not an OEM fact.

### 1.2 Converter / power center

| Claim | Tag | Notes / source |
|---|---|---|
| OEM converter on a **2003 Fleetwood Prowler** was **45 A** | `direct_in_domain_support` | NHTSA complaint **10051783**: “ORIGINAL UNIT WAS A 45 AMP”; dealer tried 35 A replacement, then suggested 55 A |
| Converter reliability was a known pain point on early-2000s Prowler | `direct_in_domain_support` | Complaints **10050654**, **10051783** (repeated converter failures) |
| Brand for that 45 A unit (Magnetek vs Progressive Dynamics vs WFCO) | `unknown` | Complaint does not name brand |
| Magnetek-era converters common late-1990s / early-2000s; Progressive Dynamics / WFCO dominate mid-2000s replacements | `analogical_support` | Industry succession pattern; **not** VIN-proven |
| Typical integrated power center = 120V breakers + 12V fuse block + converter in one cabinet | `analogical_support` | Universal TT topology of era |
| 2004 Fleetwood conventional & fifth-wheel trailers (incl. **Prowler**) used **Siemens Q** circuit breakers that were **mis-marked** | `direct_in_domain_support` | NHTSA recall **04V145000** |

**Brand ranking for *this* coach (pending nameplate):**  
1. Read converter/power-center label.  
2. If missing: treat as **45 A class** (`direct` sister-year) inside a Magnetek→PD/WFCO transition window (`analogical`).

### 1.3 Battery location

| Claim | Tag | Notes |
|---|---|---|
| Single flooded Group 24/27 house battery typical | `analogical_support` | Era/class |
| Common locations: **A-frame / tongue box** or **under dinette / front bunk** with vented box | `analogical_support` | Stick-built Fleetwood practice |
| Exact location on VIN `…595598` | `unknown` | Inspect |
| Dead house battery reported on 2004 Prowler Regal 270 (symptom, not topology proof) | `direct_in_domain_support` | Complaint **10158411** |

### 1.4 Fuse / breaker panel & wire routing

| Claim | Tag | Notes / source |
|---|---|---|
| 120V branch breakers live in the **power center** cabinet (often hallway / bed base / cabinet end) | `analogical_support` | Era TT layout |
| 12V ATC/ATO fuse strip in same cabinet or adjacent | `analogical_support` | Era TT layout |
| Chassis wiring can be **pinched between frame and floor** | `direct_in_domain_support` | Complaint **10173668** (2006 Prowler): wiring caught frame/floor; burned cable, converter, fuses, brakes |
| 12V runs typically follow floor voids / wall cavities, often stapled to studs/joists with minimal grommets | `analogical_support` | Stick-built Fleetwood “stick-and-tin” practice |
| Exact loom map for this VIN | `unknown` | Photograph before cut |

**Strip note:** Assume **no salvage value** on OEM converter/wiring; plan full 48V spine + cleaned 12V bus (see bible §2.1).

---

## 2. Fresh / gray / black plumbing

### 2.1 Capacities & locations (2003–2006 ~27' Prowler)

| Tank | Brochure value for this VIN | Working band for planning | Tag |
|---|---|---|---|
| Fresh | **`unknown`** | Often ~30–50 gal on similar 26–28' Fleetwood stick-builts | `unknown` + `analogical_support` |
| Gray | **`unknown`** | Often ~25–45 gal | `unknown` + `analogical_support` |
| Black | **`unknown`** | Often ~25–45 gal | `unknown` + `analogical_support` |
| Locations | Fresh often forward/mid underbelly; gray/black mid-aft under bath/galley | `analogical_support` | Confirm underbelly |
| Dump valves | Curbside mid-coach cluster typical | `analogical_support` | Confirm |

**No reachable brochure PDF** listed gallonages for 2003–2006 Prowler 272/27H/270 in this environment. Do **not** treat the planning band as OEM fact.

Related Fleetwood fresh-tank structural issue (folding line, not Prowler TT): recall **01V367000** — missing freshwater tank support braces on Fleetwood Folding C25 — `analogical_support` only (shows Fleetwood tank mounting can be under-specified).

### 2.2 Supply piping — polybutylene vs PEX

| Claim | Tag | Notes |
|---|---|---|
| Early-2000s RVs sit in the **PB → PEX transition** | `analogical_support` | Industry chronology (Qest/Quest PB → PEX) |
| **Whether this VIN has PB, early PEX, or mixed** | `unknown` | Cut one accessible cold line; look for PB stamp / Qest fittings vs PEX |
| Rebuild rule: **replace entire potable supply with PEX** regardless | `inferred` | Non-regression for EV rebuild bible |

### 2.3 Drain / city water / pump

| Claim | Tag | Notes |
|---|---|---|
| Drain/waste: **ABS DWV** with P-traps; 3" black, 1.5–2" gray typical | `analogical_support` | Era TT |
| City-water inlet → pressure regulator → manifold; pump on tank mode with check valve | `analogical_support` | Era TT |
| 12V demand pump (Shurflo / similar class) near fresh tank | `analogical_support` | Brand on *this* coach = `unknown` |
| Accumulator tank | sometimes present | `unknown` for VIN |
| Skylight / shower leak path documented on 2004 Regal 270 | `direct_in_domain_support` | Complaint **10158411** (skylight over shower leaked; slide leak) |

---

## 3. LP gas / HVAC / absorption cooling

### 3.1 LP bottles & regulator

| Claim | Tag | Notes / source |
|---|---|---|
| Dual bottles on A-frame tray | `analogical_support` | Universal for this class |
| **20-lb vs 30-lb** for this VIN | `unknown` | Measure tray / bottle collars |
| Two-stage regulator → steel/copper distribution to furnace, WH, range, fridge | `analogical_support` | Era TT |
| Fleetwood **fifth-wheel** Prowlers MY 2004–2005: LP lines through slide floor could **pinch** | `direct_in_domain_support` (5th-wheel subset) | Recall **05V433000** — *fifth wheel only*; conventional bumper-pull VIN may not apply, but slide LP routing remains an inspection item if a slide exists |
| Purge & remove entire LP plant for all-electric rebuild | `inferred` | Bible objective |

### 3.2 Furnace

| Claim | Tag | Notes |
|---|---|---|
| Forced-air LP furnace, Suburban or Atwood OEM common industry-wide | `analogical_support` | Recalls naming Suburban/Atwood furnaces across OEMs (e.g. **06V208000** Thor — exhaust vent) |
| Typical input band for ~27' TT: **~16k–30k BTU** | `analogical_support` | Class sizing |
| Exact BTU / brand on this VIN | `unknown` | Read exterior vent / dataplate |
| Strip weight planning band | ~50–80 lb | `analogical_support` (bible §5.1) |

### 3.3 Water heater

| Claim | Tag | Notes |
|---|---|---|
| OEM class: **Atwood or Suburban** gas/electric storage | `analogical_support` | Dominant mid-2000s TT suppliers |
| **6-gal** more common than 10-gal on mid-size TT | `analogical_support` | Class pattern |
| Exact capacity on this VIN | `unknown` | Read door / rating plate |
| Strip weight planning band | ~60–90 lb (empty + remnants) | `analogical_support` |

### 3.4 Roof air conditioner

| Claim | Tag | Notes |
|---|---|---|
| Single roof AC typical for this size/era | `analogical_support` | Ties to 30A shore assumption |
| Coleman-Mach / Duo-Therm **~13.5k BTU** class widely used | `analogical_support` | Industry OEM share; **not VIN-proven** |
| Exact brand/tonnage | `unknown` | Read shroud / dataplate |
| Strip weight planning band | ~80–110 lb | `analogical_support` |

### 3.5 Refrigerator (absorption)

| Claim | Tag | Notes / source |
|---|---|---|
| Fleetwood Prowler travel trailers MY 2000–2004 included in **Dometic two-door boiler-tube** recalls | `direct_in_domain_support` | NHTSA **07V120000**, **08V320000** (Prowler explicitly listed among conventional/5th-wheel lines) |
| Documented installed models on Prowlers: **Dometic RM2652**, **RM2852** | `direct_in_domain_support` | Complaints **10236824**, **10260931**, **10288565**, **10176967**, **10334956**, etc. |
| Equipment campaign umbrella | `direct_in_domain_support` | Dometic **06E076000** / related **08E032000** referenced in owner complaints |
| Norcold also used across Fleetwood TT/MH fleet | `analogical_support` | Fleetwood recall **08V240000** (Norcold) — confirms dual-supplier reality; Prowler-specific Norcold installs still `unknown` per VIN |
| Fire / ammonia leak failure mode is real on this generation | `direct_in_domain_support` | Complaints above + recall text (coolant release near ignition source) |
| Strip weight planning band | ~100–150 lb | `analogical_support` |

### 3.6 Other LP / 120V appliances

| Item | OEM expectation | Tag |
|---|---|---|
| Cooktop / oven | LP range (3–4 burner + oven common) | `analogical_support` |
| Microwave | Samsung microwave used on Fleetwood travel trailers incl. **Prowler** MY 2000–2004 | `direct_in_domain_support` — recall **03V452000** (defective membrane panel → self-activation / fire risk) |
| Furnace thermostat / WH switch | 12V control | `analogical_support` |

---

## 4. OEM appliance list & approximate strip weights

Use for **removal planning / tongue rebalance**, not shipping quotes. Weigh on removal when possible.

| # | System / appliance | OEM likelihood on ~2004 Prowler 272-class | Approx. removal mass (lb) | Mass tag | EV disposition |
|---|---|---|---:|---|---|
| 1 | Dual LP bottles (empty) + brackets | High | 25–50 | `analogical_support` | Strip |
| 2 | LP regulator + pigtails + lines | High | 15–30 | `analogical_support` | Strip / purge |
| 3 | LP forced-air furnace | High | 50–80 | `analogical_support` | Strip |
| 4 | Water heater 6–10 gal gas/electric | High | 60–90 | `analogical_support` | Strip |
| 5 | Absorption fridge (Dometic RM26xx/RM28xx class) | **High (NHTSA-backed)** | 100–150 | `direct` model family + `analogical` mass | Strip |
| 6 | Roof AC ~13.5k class | High | 80–110 | `analogical_support` | Strip |
| 7 | LP range / oven | High | 40–70 | `analogical_support` | Strip |
| 8 | Microwave (Samsung era) | Medium–high | 30–50 | `direct` OEM presence + `analogical` mass | Strip or replace 120V |
| 9 | Converter / power center | High (~45 A class) | 15–30 | `direct` amperage sister-year + `analogical` mass | Strip |
| 10 | House flooded battery | High | 40–65 | `analogical_support` | Strip |
| 11 | 12V demand pump + plumbing fittings | High | 5–15 | `analogical_support` | Replace |
| 12 | Fresh / gray / black tanks (empty plastic) | High | 40–90 combined | `analogical_support` | Keep or replace |
| **A** | **LP + HVAC + absorption + WH + range subtotal** | — | **≈ 400–630** | mixed | — |
| **B** | **Electrical power-center + battery** | — | **≈ 55–95** | mixed | — |

Bible §5.1 removal band (−640 to −1,250 including cabinetry) remains consistent with row **A+B** plus cabinetry/generator deltas.

---

## 5. Known plumbing / electrical failure modes (this generation)

### 5.1 Confirmed on Fleetwood Prowler (NHTSA)

| Failure mode | Evidence | Tag |
|---|---|---|
| **Converter repeated failure** (45 A OEM; under/oversized replacements) | Complaints **10050654**, **10051783** | `direct_in_domain_support` |
| **Dometic absorption boiler-tube leak / fire / ammonia** | Recalls **07V120000**, **08V320000**; complaints with RM2652/RM2852 | `direct_in_domain_support` |
| **Samsung microwave self-start / fire risk** | Recall **03V452000** | `direct_in_domain_support` |
| **Siemens Q breaker mis-marking** (overload protection error) | Recall **04V145000** | `direct_in_domain_support` |
| **Frame/floor-pinched chassis wiring** → burned cables, converter, brakes | Complaint **10173668** | `direct_in_domain_support` |
| **Shore-power inlet / feed fire** | Complaint **10232011** | `direct_in_domain_support` |
| **Slide / skylight water intrusion** (bath/galley zone) | Complaint **10158411** | `direct_in_domain_support` |
| **LP line pinch in slide floor** | Recall **05V433000** | `direct_in_domain_support` for 2004–2005 **fifth-wheel** Prowler; `analogical_support` caution for any slide LP pass-through |

### 5.2 Era / class hazards (not VIN-proven)

| Failure mode | Tag | Notes |
|---|---|---|
| Polybutylene fitting brittle failure / leaks → subfloor rot | `analogical_support` | Inspect; replace all supply |
| ABS dump-valve / tank seam leaks | `analogical_support` | Common aging failure |
| Roof AC gasket / duct boot leaks into ceiling | `analogical_support` | Common |
| Furnace exhaust / intake blockage or bad install → CO | `analogical_support` | Industry furnace recalls on other OEMs |
| Corroded battery cables / poor ground → chronic 12V brownouts | `analogical_support` | Common |
| Aluminum wheel lug torque / paint on hub face | `direct_in_domain_support` on Fleetwood TT family | Recalls **03V437000**, **04V310000** (wheels — adjacent, not plumbing/electrical) |

---

## 6. Systems-to-strip inventory (EV rebuild)

Ordered for **safe decommission** (gas → electrical → wet → structural penetrations):

### Phase A — Make safe
1. Close LP bottle valves; burn residual at appliances outdoors if needed; **purge lines**; remove bottles.  
2. Unplug shore; disconnect house battery negative first.  
3. Cap / lock out city water; drain all tanks & WH.

### Phase B — Combustion & heavy appliances
4. LP range/oven  
5. Absorption refrigerator (Dometic/Norcold) + roof/side vents  
6. LP furnace + thermostat + duct boots  
7. Gas/electric water heater  
8. LP regulator, pigtails, all copper/steel LP distribution  

### Phase C — Electrical OEM core
9. Converter / power center (keep temporary lights only if needed)  
10. Shore cord / inlet (replace later with new inlet strategy)  
11. House battery & tray cables  
12. Microwave (Samsung-era unit — do not reuse without verifying recall remedy)  

### Phase D — Climate envelope penetrations
13. Roof AC shroud + air box (patch/reinforce roof opening for mini-split or close)  
14. Fridge roof vent / side vent covers  

### Phase E — Plumbing (selective)
15. Demand pump, city inlet regulator, PB/PEX supply (full redo)  
16. Keep or replace tanks/valves based on leak test; ABS drains as needed  

### Phase F — Do **not** strip until structure plan set
- Fresh/gray/black tanks if still sound and locations suit new layout  
- Dump valves if sealing OK  
- 7-pin / electric brake wiring until running-gear phase  

---

## 7. Capacity / topology tables (summary)

### Electrical topology (OEM expected)

```
TT-30 shore inlet ──► Power center (Siemens Q breakers) ──► 120V branches
                         │
                         ├── Converter/charger (~45 A class) ──► 12V fuse block ──► loads
                         │
                         └── Battery (Group 24/27) ◄── charge line / converter
```

Tags: shore amperage `analogical`/`unknown`; converter amps `direct` (2003 sister); brand `unknown`.

### Plumbing topology (OEM expected)

```
City inlet ──► regulator ──► [PB or PEX] manifold ──► fixtures + WH
Fresh tank ──► 12V pump ──► same manifold
Fixtures ──► ABS gray / black ──► dump valves
```

Tags: materials & gallons `unknown` until open-up.

### LP / HVAC topology (OEM expected)

```
Dual bottles ──► 2-stage regulator ──► furnace / WH / range / absorption fridge
Roof AC ──► dedicated 120V breaker (often 20A)
```

Tags: bottle size / furnace BTU / WH gallons / AC tonnage = `unknown`; fridge family = `direct` (Dometic two-door / RM2652–2852 class).

---

## 8. Research gaps / next evidence actions

| Gap | Why it matters | How to close |
|---|---|---|
| Exact fresh/gray/black gallons | Weight & layout | Brochure / door placard / measure tanks |
| Converter brand + model | Spare parts / strip | Photograph power-center label |
| 30A vs 50A inlet | Shore strategy | Photograph inlet & main breaker |
| PB vs PEX | Leak risk | Cut test coupon |
| Furnace / WH / AC dataplates | Strip mass & vent reuse | Photograph exteriors |
| NHTSA vPIC full decode for `1EA…` | Confirm make/model string | Decode on nhtsa.gov when egress allows |
| OEM brochure 2004 Prowler 272/27H/270 | Capacities / standard equipment | Internet Archive / dealer scan |

---

## 9. Sources (primary & working)

1. **NHTSA recall flat files** via `https://github.com/flotwig/nhtsa-data` (`recalls_2000.csv` … `recalls_2008.csv`) — campaigns **03V452000**, **04V145000**, **05V433000**, **07V120000**, **08V240000**, **08V320000**, others cited above.  
2. **NHTSA complaint flat files** via same repo (`complaints_2003.csv` …) — IDs **10050654**, **10051783**, **10146248**, **10158411**, **10173668**, **10232011**, **10236824**, **10260931**, **10288565**, **10334956**, etc.  
3. Project VIN `1EA1F272941595598` structural parse (year/series tokens).  
4. Parent bible: `FLEETWOOD_PROWLER_272_EV_REBUILD_BIBLE.md` (era-typical construction context).  

**Explicitly excluded as sources:** SEO spam “owners manual PDF download” GitHub pages returned by WebSearch (no usable OEM content).

---

## 10. Recursive critique (saturation pass)

| Critique | Result |
|---|---|
| Weak brochure gallonages? | Confirmed still **`unknown`** — not filled with invented numbers |
| Converter brand claimed? | No — only **45 A** from sister-year complaint |
| 30A asserted as fact for VIN? | No — class pattern only |
| Fridge overstated? | Strengthened with RM2652/RM2852 complaint IDs + Prowler-named recalls |
| 5th-wheel LP recall applied to bumper-pull? | Demoted to subset + inspection caution |
| Weights? | Kept as planning bands; tagged |

**Stop condition:** Further WebSearch in this environment yields spam, not stronger primary sources. Next material improvement requires **physical placards** or unblocked brochure/NHTSA vPIC access.
