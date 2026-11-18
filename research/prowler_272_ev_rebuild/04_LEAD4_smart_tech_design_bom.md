# Lead 4 — Smart Stack · Industrial Design · Weight/Cost/Build Order

Source: parallel research lead (agent `bc-aa2947a9-bc33-56e3-830e-32f7a6d46fd1`).  
Synthesized into `FLEETWOOD_PROWLER_272_EV_REBUILD_BIBLE.md` Parts 3–5.

**Confidence:** H = primary/open source · M = multi-source pattern · L = ballpark verify-before-buy.

## Connectivity (local-first)

| Item | Guidance | Conf |
|---|---|---|
| Starlink Mini | ~2.43 lb; 11.75×10.2×1.45″; **12–48 VDC**; ≤60 W (typ. 15–40 W); Ethernet → router WAN; **Bypass Mode**; route to `192.168.100.1` | H |
| In-motion | Roam / Mobile Priority plans for sustained motion | M |
| Budget router | GL.iNet Spitz AX **GL-X3000** (failover/load-balance; OpenWrt) ~$350–450 | H |
| True bond | Self-host OpenMPTCP / tailbond / SmoothWAN to own VPS | H |
| Prosumer | Peplink MAX BR1 / Transit Duo + optional self-hosted FusionHub | M |
| Avoid for no-lock-in | Cradlepoint NetCloud-centric path unless fleet already committed | M |

**Recommended:** `Starlink Mini (bypass) + GL-X3000 → optional self-host bond → HA LAN`. Escalate Peplink only for SLA/true multi-WAN bonding need.

## Edge / Matter / Thread

| Hub | Role | Cost | Conf |
|---|---|---|---|
| HA Green + Connect ZBT-2 | Light control plane | Green ~$159 + stick | H |
| Mini-PC HAOS + ZBT-2 + Coral | Preferred for Frigate + cams + WLED + MQTT | $250–600 + Coral ~$60 | H |
| HA Yellow | Built-in Thread/Zigbee; still prefer split NVR | Variable | H |

Hard rule: Mosquitto + Matter Server + Frigate on-LAN; Tailscale/WireGuard optional remote; cloud never control plane.

## UX subsystems

| Subsystem | Pick | Cost | Conf |
|---|---|---|---|
| Touch panels | ESP32-S3 LVGL / Android Fully Kiosk | $40–200 | H |
| Cove LEDs | SK6812 RGBW + WLED + HA circadian | $80–400 / coach | H |
| PDLC | <5 W/m²; fails opaque; wet bath / projector | Film $15–120/ft² | M |
| Motorized shades | Zigbee/ESPHome tubular; bedrooms (thermal) | $150–400 / opening | M |
| Desk PD | USB-C PD 3.1 **140 W = 28 V × 5 A**; e-marked 240 W cables; dedicated brick/dock often more practical than rare in-wall 140 W receptacles | Brick $60–120 | H |
| Lock | Nuki + ESPHome BLE/MQTT local; mechanical override | $200–350 + bridge | H |
| Cams | Reolink-class RTSP → Frigate + go2rtc | $80–200 ea | H |
| Level | Lippert Ground Control TT ~$2.5–4.5k installed; SteadyFast manual $400–1.2k | M/L |

## Weight / BOM deltas (smart + design slice)

- Networking + HA + cams ≈ 20–50 lb  
- GC TT auto-level ≈ 150–300+ lb kit-dependent  
- Wrap path $2–6k vs panels/windows $5–18k installed  
- Smart stack DIY often $2–6k; full rebuild envelope still dominated by structure + 48V bank  

## Local-first topology

```text
Starlink Mini ──► GL-X3000 / Peplink ◄── 5G dual-SIM
                      │
                 Trailer LAN
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
      HAOS mini-PC   Frigate+Coral  Victron Cerbo (MQTT)
         │
    WLED / Nuki / ESPHome panels / level sensors
```
