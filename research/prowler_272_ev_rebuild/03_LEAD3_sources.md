# Lead 3 — Source index (all-electric off-grid)

Evidence collected 2026-11-18 for `03_LEAD3_all_electric_offgrid_conversion.md`.

## Datasheets / primary technical PDFs
- Victron MultiPlus-II inverter/charger datasheet (EU 4 kW / 6 kW models): charge voltages 57.6 / 55.2 V, zero-load 20–28 W, mobile/marine suitability, PowerAssist — `Datasheet-MultiPlus-II-inverter-charger-4k5-6k5-EN-2.pdf` (indexed blob).
- EG4 12000XP spec: 12 kW batt-only / 15 kW w/ PV, 104.7 lb, idle <70 W, 250 A charge/discharge — `eg4-12000xp-spec.pdf`.
- EG4 FlexBOSS21: hybrid AIO PV/batt ratings, idle <60–80 W — `flexboss21.pdf`.
- Sol-Ark Limitless 15K-LV (15K-2P): 12/15 kW, 135 lb, 90 W idle, UL1741 — `15k-2p-n.pdf`.
- Trina Vertex S+ NEG18RC.27 (N-type i-TOPCon bifacial): 495–520 W, ~51.8 lb, 1961×1134 mm — 2025 datasheet.
- Trina / Canadian Solar-class large TOPCon bifacial (610–650 W): roof-impractical dims/weights — 2025 datasheets.
- MUST LP1600 LiFePO4: 48V 100 Ah ~45 kg; 48V 200 Ah ~80 kg — LP1600 series datasheet.
- Hessaire / Grainger mini-split specs (R32 & high-SEER R454B, 2026): 12k / 18k rated input watts & SEER2.
- Wolf / Café induction install sheets: 30" residential induction ~39–49 lb, 40 A dedicated — **anti-pattern for TT**.
- EcoFlow DELTA Pro Ultra battery manual (related LFP mass anchor ~111 lb / 6.1 kWh class) — not Power Kit primary, used only as mass context.
- RICS Spray foam insulation consumer guide (Mar 2023): irreversible mod, moisture/fire caveats.

## GitHub / integration evidence
- `askpatrickw/awesome-fordtransit`: Cruise N Comfort USA listed as 12/24/48 V split AC.
- `foxthefox/ioBroker.ecoflow-mqtt` `doc/devices/powerkit.md`: Power Kit totalOutWatts up to 7200 W.
- `tolwi/hassio-ecoflow-cloud#131`: Power Kit / Gen2 API limitations.
- Victron Orion XS issues (`victronenergy/node-red-contrib-victron`): Orion XS as alternator charger on Cerbo.
- `mrmees/esphome-houghton-ac` / IRremoteESP8266#2247: RecPro/Houghton = 120V CARRIER_AC128 class (not 48V proof).
- `CaptainASIC/offgridpower`: EG4 WallMount 280 Ah = 14.3 kWh each.
- MidNite Rosie / MN15: community CAN/MQTT and HA Modbus FR threads (existence, not full datasheet).

## Limits
- Manufacturer sites (Nomadic Cooling, Hensley, ProPride, EcoFlow retail, NHTSA vPIC) blocked by agent egress allowlist — weights for hitches and Nomadic/CNC run-watts marked `[I]`/`[U]`.
- Exact Fleetwood Prowler 272 GVWR for VIN requires physical door/axle stickers.
