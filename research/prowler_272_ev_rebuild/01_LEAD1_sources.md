# Lead 1 — Source index (OEM chassis / construction)

Evidence collected 2026-11-18 for `01_LEAD1_oem_chassis_running_gear_construction.md`.

## Primary / direct
- NHTSA manufacture WMI dump mirror: https://github.com/iotlabsltd/pyvin/blob/master/data/WMI_565.csv  
  - `1EA` → Fleetwood Enterprises / Fleetwood Travel Trailers (Riverside / San Bernardino CA)  
  - Folding Trailers → `1EB`, `1CL`, `4CA`, `4CF`, `4CT`, `4CG` (Somerset PA)  
  - Project README cites upstream `ftp://ftp.nhtsa.dot.gov/manufacture`
- VIN structural parse of `1EA1F272941595598` (WMI, `272` token, year code `4`, check digit match)

## Secondary / incomplete
- https://github.com/Wal33D/nhtsa-vin-decoder — offline WMI CSVs list `1EC`=Fleetwood; omit `1EA`
- https://github.com/idlesign/vininfo — WMI dict incomplete for trailer OEMs

## Blocked this environment (needed for next pass)
- Live NHTSA vPIC: `https://vpic.nhtsa.dot.gov/api/vehicles/DecodeVinValues/1EA1F272941595598?format=json`
- RVUSA / RV Trade Digest / archive.org 2003–2005 Prowler brochures
- Dexter OEM axle ID documentation hosts
- rv.net / IRV2 photo teardown threads

## Explicit non-sources
- SEO spam GitHub “manual download” pages (no real OEM content)
