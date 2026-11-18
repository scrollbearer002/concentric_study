# Lead Researcher 1 — OEM Chassis, Running Gear, Floor/Wall/Roof Construction

**Territory:** OEM chassis · running gear · floor / wall / roof anatomy · structural weak points  
**Target VIN:** `1EA1F272941595598`  
**Claimed platform:** ~2004 Fleetwood Prowler 27' bumper-pull tandem-axle (272-series / 27H–270 class; titled as 2013)  
**Research date:** 2026-11-18  
**Role:** Lead Researcher 1 of 4 (Fleetwood Prowler rebuild bible)

---

## Research frame

| Field | Value |
|---|---|
| system_of_interest | Fleetwood Prowler 272-series bumper-pull travel trailer shell + chassis |
| domain | OEM travel-trailer structural / running-gear anatomy |
| environment | US mid-2000s Fleetwood stick-built production; remote research with blocked OEM brochure / live NHTSA API egress |
| task | Exhaustive factual OEM anatomy for teardown planning |
| stakeholder | Owner planning inside-out all-electric rebuild |
| success_criteria | Confidence-tagged claims; no invented gauges; physical verification gates |
| excluded_adjacent | Motorhomes, fifth-wheels as primary, aluminum-cage coaches (Airstream/Nash), modern Lippert torsion-first lines as OEM truth |
| transfer_rules | Adjacent Fleetwood TT lines (Wilderness/Terry) may inform construction class only as `analogical_support` |

### Confidence tags (this report)
| Tag | Meaning |
|---|---|
| `direct_in_domain_support` | Primary document or VIN-structural fact for this manufacturer/unit |
| `analogical_support` | Strong pattern from same era / same OEM class, not this exact floorplan brochure |
| `inferred` | Reasonable engineering inference from VIN + class norms |
| `unknown` | Not established; must measure / photograph on unit |

### Environment / source limits (mandatory honesty)
Remote egress in this agent environment **blocks** live NHTSA vPIC (`vpic.nhtsa.dot.gov`), RVUSA, archive.org brochure hosts, rv.net, and most OEM PDF hosts. WebSearch returned almost no usable brochure content (SEO spam manuals).  

**What was obtainable:**
- NHTSA manufacturer WMI registration dump mirrored on GitHub (`iotlabsltd/pyvin` → `data/WMI_565.csv`) — **primary for WMI identity**
- ISO-3779 VIN structural parse + check-digit validation — **primary for year/series tokens**
- Incomplete public WMI dictionaries listing `1EC` = Fleetwood (secondary; incomplete; does not list `1EA`)

**Not obtained this pass:** 2003–2005 Prowler 27H/270/272 brochure weight tables, Dexter axle plate photo for this VIN, federal certification label photo, frame rail caliper measurements.

---

## 1. VIN / manufacturer identity

### 1.1 Structural decode of `1EA1F272941595598`

| Position | Char(s) | Interpretation | Confidence |
|---|---|---|---|
| 1–3 WMI | `1EA` | Fleetwood Enterprises / Fleetwood Travel Trailers (see §1.2) | `direct_in_domain_support` |
| 4–8 VDS body | `1F272` | Manufacturer-specific; embeds **`272`** series token | `direct_in_domain_support` (token present) / `inferred` (maps to 272/27H/270 family) |
| 9 check | `9` | ISO-3779 check digit **matches** computed value `9` | `direct_in_domain_support` |
| 10 year | `4` | Model year **2004** (SAE year code 1–9 → 2001–2009) | `direct_in_domain_support` |
| 11 plant | `1` | Plant code — **specific plant not resolved** from available dump | `unknown` |
| 12–17 serial | `595598` | Sequential production number | `direct_in_domain_support` |

**Title year 2013 vs VIN year 2004:** Registration/title year is **not** OEM model year. Do not use 2013 for construction assumptions. Treat as paperwork anomaly until federal label year is photographed. — `direct_in_domain_support` (VIN year) + `inferred` (title mismatch is administrative)

**Exact floorplan letter (27H vs 270 vs other 272-family):** Not recoverable from VIN alone. — `unknown`

### 1.2 WMI `1EA` — correction to Folding-Trailers hypothesis

**Claim:** WMI `1EA` identifies **Fleetwood Enterprises / Fleetwood Travel Trailers** (hard-side trailer family, Riverside / San Bernardino CA addresses in NHTSA letters), **not** Fleetwood Folding Trailers (Somerset PA).

| Evidence | What it shows | Confidence |
|---|---|---|
| NHTSA manufacture WMI dump rows for `1EA` | `FLEETWOOD ENTERPRISES INC.` / `FLEETWOOD ENTERPRISES, INC` / `FLEETWOOD TRAVEL TRAILERS` — product type TRAILER (and one TRAVEL TRAILERS row typed TRUCK) — Riverside / San Bernardino CA — letter dates 1991–1998 range in dump | `direct_in_domain_support` |
| Same dump, Folding Trailers rows | `FLEETWOOD FOLDING TRAILERS*` use WMIs **`1EB`, `1CL`, `4CA`, `4CF`, `4CT`, `4CG`** — Somerset PA | `direct_in_domain_support` |
| Incomplete wiki/offline WMI lists | Often list `1EC` = Fleetwood; omit `1EA` | `analogical_support` (incomplete secondary) |

**Source URL (mirrored NHTSA manufacture file):**  
https://github.com/iotlabsltd/pyvin/blob/master/data/WMI_565.csv  
(Upstream referenced by that project: `ftp://ftp.nhtsa.dot.gov/manufacture` — live FTP not reachable from this environment.)

**Representative dump lines (verbatim pattern):**
- `FLEETWOOD ENTERPRISES, INC,1EA,3030 MYERS ST,,RIVERSIDE,CA,92513,,TRAILER,,1998-02-18`
- `FLEETWOOD TRAVEL TRAILERS,1EA,255 S. PEPPER AVE.,,SAN BERNARDINO,CA,92412,,TRUCK,,1991-05-09`
- `FLEETWOOD FOLDING TRAILERS INC,1EB,,,SOMERSET,PA,15501,,TRAILER,,1991-05-06`

**Plant code caveat:** Dump associates `1EA` with Fleetwood travel-trailer corporate registrations in CA; position-11 plant `1` on this VIN is **not** mapped to a named assembly plant in sources retrieved this pass. — `unknown`

### 1.3 Model-family inference (272 / 27H / 270)

| Claim | Tag | Notes |
|---|---|---|
| VIN embeds `272` → unit is in Fleetwood **272-series** naming family used for ~27' Prowler floorplans | `inferred` | Strong token match; not a brochure confirmation of letter suffix |
| Common marketing names in this size band include **27H / 270 / 272** variants depending on year trim | `analogical_support` | Owner/dealer naming varies; brochure not retrieved |
| Nearest brochure year if label unavailable: search **2003–2005 Prowler / Prowler LS** 27' sheets | `inferred` | Planning guidance only |

---

## 2. Chassis & running gear

### 2.1 Frame

| Attribute | Finding | Confidence | Source / basis |
|---|---|---|---|
| Architecture | Steel **ladder frame** with main rails + crossmembers + **outriggers** supporting floor edge | `analogical_support` | Universal early-2000s Fleetwood conventional TT practice |
| Main rail section | **C-channel** predominant in this OEM class (not I-beam coach rail) | `analogical_support` | Era Fleetwood/Wilderness/Terry stick-built class |
| Rail height / flange / gauge | **Unknown — do not invent** | `unknown` | Requires caliper / tape on bare rails |
| Steel type (A36 vs HSLA, etc.) | **Unknown** | `unknown` | No mill cert / OEM print retrieved |
| Outrigger spacing | Often ~16–24" along floor edge in this class | `analogical_support` | Typical stick-built TT; measure on unit |
| A-frame | Formed steel A-frame welded to main rails; coupler + jack + LP tray mounts | `analogical_support` | Class-standard |
| Coupler size | 2-5/16" ball common for ~7k GVWR class | `analogical_support` | Verify stamped rating ≥ GVWR |

**I-beam vs C-channel:** Treat as **C-channel unless physical inspection shows otherwise**. I-beam main rails are atypical for this budget/mid Fleetwood bumper-pull class. — `analogical_support`

### 2.2 Axles, suspension, hubs, brakes

| Attribute | Finding | Confidence | Notes |
|---|---|---|---|
| OEM axle brand | **Dexter** (or Dexter-spec) extremely common on Fleetwood TT of era | `analogical_support` | Confirm via axle ID tag photo |
| Suspension | **Leaf spring** with equalizer (rocker) on tandem — **not** Torflex/torsion as typical OEM | `analogical_support` | Torsion existed industry-wide but was not the Fleetwood Prowler default |
| Capacity candidates | Dual **3,500 lb** most common package; dual **4,400 lb** on heavier/optioned units | `analogical_support` | **This VIN: unknown until tags read** |
| Brakes | Electric **drum** brakes; **10"** drums typical on 3,500-lb Dexter packages; **12"** more common on heavier axles | `analogical_support` | Measure drum OD / read tag |
| Hub / bolt pattern | 5-lug or 6-lug depending axle capacity package | `unknown` | Count lugs on unit |
| Spring centers / track | Printed on axle tag or measurable hanger-to-hanger | `unknown` | Critical before axle replacement |

**GAWR math (planning only):**  
If tags say 3,500 × 2 → axle-sum 7,000 lb; trailer **GVWR is often ≤ axle-sum** because tongue carries share. Never treat axle-sum as GVWR. — `inferred`

### 2.3 Weights (UVW / hitch / GVWR)

| Spec | Exact 2004 272 / 27H / 270 brochure value | Confidence |
|---|---|---|
| UVW (dry) | **Not retrieved** this pass | `unknown` |
| Hitch / tongue weight | **Not retrieved** | `unknown` |
| GVWR | **Not retrieved** | `unknown` |
| Cargo carrying capacity | **Not retrieved** | `unknown` |

**Planning band only (NOT for this VIN as fact):** similar ~27' early-2000s Fleetwood stick-built bumper-pulls often fall roughly UVW ~5,200–6,400 lb and GVWR ~7,000–7,600 lb with hitch ~10–14% of UVW. Use solely as order-of-magnitude until door sticker + CAT scale. — `analogical_support` / `inferred`

**Authoritative locations on the physical unit:**
1. Federal certification label (roadside forward half / entry door area): GVWR, GAWR each axle, tire size/PSI, sometimes UVW  
2. VIN plate  
3. Axle manufacturer tags on axle tubes  
4. CAT scale: empty UVW + separate tongue scale

---

## 3. Floor construction

| Layer | OEM expectation for this generation | Confidence |
|---|---|---|
| Structure | Wood floor joists spanning main rails / outriggers | `analogical_support` |
| Joist size | Often 2×3 or 2×4 dimensional lumber | `analogical_support` |
| Joist spacing | Commonly **~16" o.c.** | `analogical_support` |
| Subfloor deck | **5/8" or 3/4" plywood or OSB** | `analogical_support` — exact thickness/material `unknown` until core sample |
| Finish floor | Vinyl / linoleum / carpet over underlayment | `analogical_support` |
| Underbelly | Plastic corrugated enclosure (**Coroplast / Coro-plast / Darco-class**); coverage often incomplete at tanks/axles | `analogical_support` |
| Floor insulation | Fiberglass batts or thin foam board above belly | `analogical_support` |
| Effective R | Brochure R-claims optimistic; wet/compressed batts far lower | `inferred` |

**Tank interaction:** Fresh often forward/mid; gray/black clustered under bath/galley — condensation + plumbing leaks drive floor rot. Exact gallonages and drop locations: `unknown` until underbelly open.

---

## 4. Wall construction

| Attribute | OEM expectation | Confidence |
|---|---|---|
| Method | **Stick-and-tin**: wood stud framing — **not** welded aluminum cage | `analogical_support` |
| Studs | Vertical wood (often ~2×2 / 1.5" nominal), commonly ~16" o.c. | `analogical_support` |
| Exterior cladding | **Corrugated aluminum** common; some trims/years use thin **Filon / fiberglass** over lauan | `analogical_support` — which skin is on THIS unit: `unknown` (photo) |
| Interior paneling | Lauan / decorative panelboard stapled to studs | `analogical_support` |
| Insulation | Fiberglass batts in cavities | `analogical_support` |
| Marketed R-value | Often cited in brochures as modest wall R (commonly R-7 class marketing in era); **not verified for 272** | `unknown` for this floorplan; brochure R = marketing not lab |
| Windows | Radius-corner framed; butyl/putty tape + exterior clamp ring — high leak rate with age | `analogical_support` |

**Aluminum cage exclusion:** Do not design rebuild assuming extruded aluminum wall cage. Opening a wall panel should show wood studs. — `analogical_support`

---

## 5. Roof construction

| Attribute | OEM expectation | Confidence |
|---|---|---|
| Structure | **Wood rafters / trusses** | `analogical_support` |
| Decking | Thin plywood / OSB / lauan sheet | `analogical_support` — thickness `unknown` |
| Membrane | **EPDM** rubber dominant early–mid 2000s | `analogical_support` |
| TPO likelihood | Industry shift toward TPO largely **later** than 2004 for mainstream Fleetwood TT | `analogical_support` — confirm by membrane feel/markings |
| Edge detail | Aluminum drip edge / termination bar + lap sealant — primary water path | `analogical_support` |
| Penetrations | Roof AC, bath fan, fridge roof vent, antenna — flange failure common | `analogical_support` |

---

## 6. Known structural weak points (this generation Fleetwood / Prowler class)

These are **class failure modes** repeatedly reported across early-2000s Fleetwood stick-built travel trailers (Prowler / Wilderness / Terry family). Treat as inspection priorities, not a certified defect list for this VIN.

| Zone | Failure mode | Why it happens | Confidence |
|---|---|---|---|
| Roof edge / termination bar | EPDM lift → top-plate / upper stud rot | UV + flex + dried lap sealant | `analogical_support` |
| Window bucks / corner moldings | Water into wall cavity → soft studs, panel delam | Failed putty tape / clamp ring | `analogical_support` |
| Bath fan / skylight | Soft ceiling decking, drip into walls | Flange seal age | `analogical_support` |
| Front cap / rock guard | Cracks + spray intrusion at A-frame junction | Road flex + impact | `analogical_support` |
| Galley / bath subfloor | Soft OSB/ply, delaminated finish floor | Plumbing leaks + gray-tank condensation | `analogical_support` |
| Slide aperture (if equipped) | Floor/wall delam at opening | Seal wear + drainage | `analogical_support` / `unknown` if this unit has a slide |
| Outrigger tips / floor edge screws | Rusted fasteners, soft edge | Underbelly humidity | `analogical_support` |
| A-frame welds / coupler | Cracks, elongated holes | Fatigue + overload + hitching shock | `analogical_support` |
| Spring hangers / equalizer | Elongated bolts, cracked hangers, worn bushings | Mileage + overload | `analogical_support` |
| Frame near axles | Cracks / bent hangers if overloaded or impact | Beyond GAWR / pothole events | `analogical_support` |
| Sidewall delamination | Bubbles / soft spots (worse with fiberglass skins) | Water between skin and lauan | `analogical_support` |
| Underbelly | Open/chewed plastic → wiring/insulation damage | Rodents + abrasion | `analogical_support` |

**Slide note:** Whether THIS 272 has a slide-out is **unknown** without photos/floorplan confirmation.

---

## 7. Confidence summary

| Domain | Overall confidence | Why |
|---|---|---|
| WMI / manufacturer family | **High** | NHTSA manufacture dump maps `1EA` → Fleetwood Enterprises / Travel Trailers |
| Model year 2004 | **High** | VIN pos.10 = `4`; check digit validates |
| Series ≈ 272 / ~27' family | **Medium-high** | `272` token embedded; letter suffix unknown |
| Exact 27H vs 270 vs other | **Low** | No brochure / label photo |
| Frame is C-channel ladder | **Medium** | Strong class pattern; unmeasured on unit |
| Exact rail gauge / dimensions | **None** | Explicitly `unknown` |
| Dual Dexter leaf + 10" electric drums | **Medium** | Era OEM pattern; tags unread |
| Axle capacity 3500 vs 4400 | **None for this VIN** | Must read plates |
| Exact UVW / hitch / GVWR | **None** | Brochure hosts blocked; sticker unread |
| Stick-built wood walls + EPDM roof | **Medium-high** | Dominant Fleetwood conventional TT architecture of era |
| Exact R-values / deck thicknesses | **None** | Marketing numbers not retrieved; measure |
| Weak-point list | **Medium** | Class pattern; unit-specific moisture map required |

### What would raise confidence next (priority order)
1. Photos of federal certification label + both axle tags + coupler stamp  
2. Live NHTSA vPIC decode of full VIN (when egress allows)  
3. 2003–2005 Fleetwood Prowler / Prowler LS brochure PDF for matching length/floorplan  
4. Physical rail calipers, joist OC tape, membrane ID, wall peel sample  
5. Empty CAT scale + tongue scale ticket

---

## 8. Physical teardown / inspection checklist

Use this as the gate before structural redesign or battery mass planning.

### A. Identity & ratings (photograph + transcribe)
- [ ] Federal certification label: GVWR, GAWR-front axle, GAWR-rear axle, tire size, cold PSI, manufacture date if present  
- [ ] VIN plate matches `1EA1F272941595598`  
- [ ] Both axle tube tags: brand, capacity (lb), brake type/size, serial, spring center  
- [ ] Coupler stamp rating and ball size  
- [ ] Tire DOT date codes + load range  
- [ ] Confirm title-year discrepancy narrative vs label year  

### B. Chassis geometry (measure)
- [ ] Main rail: C vs I; height × flange × web thickness (calipers)  
- [ ] Outrigger spacing and condition at tips  
- [ ] A-frame weld inspection (dye penetrant if cracks suspected)  
- [ ] Spring hanger / equalizer / shackle wear; elongated holes  
- [ ] Axle alignment / spring center; hanger cracks near axles  
- [ ] Frame rust map: A-frame, mid, axle zone, rear bumper box  

### C. Floor
- [ ] Remove underbelly sections; photograph joist direction/OC  
- [ ] Probe subfloor at bath, galley, entry, slide (if any), over tanks  
- [ ] Identify plywood vs OSB and measure thickness at a cut edge  
- [ ] Map tank locations and hanger corrosion  
- [ ] Note insulation type and wet/compressed zones  

### D. Walls
- [ ] Confirm wood studs (peel one interior panel in a wet-suspect bay)  
- [ ] Measure stud OC  
- [ ] Identify exterior skin: corrugated Al vs Filon/fiberglass  
- [ ] Moisture meter / infrared scan at windows, corners, slide corners  
- [ ] Check for sidewall bubbles / delamination  

### E. Roof
- [ ] Identify membrane (EPDM vs TPO) by markings/feel/seam style  
- [ ] Inspect termination bar full perimeter  
- [ ] Probe decking at AC gasket, bath fan, fridge vent, antenna  
- [ ] Measure rafter OC and decking thickness at a controlled cut if replacing membrane  

### F. Water-intrusion paths (priority sequence)
1. Roof edges / termination bar  
2. Window flanges and vertical corner moldings  
3. Bath fan / skylight  
4. Front cap / rock guard  
5. Entry door threshold  
6. Slide seals / wipers (if equipped)  
7. Tail light / marker light housings  
8. Refrigerator roof vent and side access doors  
9. Underbelly seams at tank plumbing penetrations  

### G. Rebuild decision thresholds (suggested)
- Soft/rot affecting **>~30% of wall studs** or **>~40% of subfloor** → plan shell-off / reframe rather than patch-in-place (`inferred` planning rule)  
- Any A-frame or axle-hanger crack → stop load-path modifications until frame repair engineered  
- Axle tags unread → **do not** finalize battery kWh or axle upgrade purchase  

---

## 9. Source index

| ID | Source | Use |
|---|---|---|
| S1 | https://github.com/iotlabsltd/pyvin/blob/master/data/WMI_565.csv | NHTSA manufacture WMI dump mirror — `1EA` = Fleetwood Enterprises / Travel Trailers; Folding = `1EB`/etc. |
| S2 | VIN `1EA1F272941595598` ISO-3779 parse + check-digit verification (computed this research) | Year 2004, series token `272`, valid check digit |
| S3 | https://github.com/Wal33D/nhtsa-vin-decoder (offline WMI lists) | Secondary; lists `1EC`=Fleetwood; incomplete for `1EA` |
| S4 | https://github.com/iotlabsltd/pyvin (README cites `ftp://ftp.nhtsa.dot.gov/manufacture`) | Provenance of WMI dump |
| S5 | Class knowledge / prior rebuild bible draft in-repo | Era-typical stick-built Fleetwood construction — tagged `analogical_support` only |
| S6 | Triple-L / general trailer ID plate explanation (GVWR vs GAWR) — analogical plate literacy | https://ymmkluc2ciaax2ks.public.blob.vercel-storage.com/model-documents/triple-l-jlg-1014/triple-l-trailers-operation-safety-and-service-manual-ansi-DT0Ax8G8nirwu764ibSsWE5DbH8Pbt.pdf |

### Explicitly NOT used as OEM truth
- SEO spam “owners manual download” GitHub pages (no real brochure content)  
- Invented steel gauge numbers  
- Title year 2013 as manufacture year  

---

## 10. Lead 1 bottom line for the rebuild bible

1. **`1EA` is Fleetwood Enterprises / Travel Trailers — not Folding Trailers.** Correct any bible text that equates `1EA` with Somerset folding plant codes.  
2. **Factory year is 2004 from VIN**; title 2013 is non-OEM.  
3. **Construction class is stick-and-tin on steel C-channel ladder + leaf Dexter-class axles + EPDM roof** — all medium-confidence class patterns pending peel/measure.  
4. **Exact UVW, GVWR, hitch, axle lb rating, rail gauge, and R-values remain `unknown`** until stickers and calipers.  
5. **Strongest next action:** photograph certification label + both axle tags + moisture-map wet zones before any battery or axle spend.

*End of Lead 1 report.*
