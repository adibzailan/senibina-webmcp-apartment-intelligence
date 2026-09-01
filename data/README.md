# Dawson fixture

`fixtures/dawson-v1.json` is the frozen application input. Rebuild it only when
deliberately refreshing public source data:

```shell
python data/scripts/build_dawson_fixture.py
```

The script uses only the Python standard library, polls the official
data.gov.sg download endpoints, converts WGS84 once into a local east/north
metre frame centred on Block 87, records source hashes, and labels the
`max_floor_level × 3.0 m` height as inferred. A refresh changes evidence and
must be reviewed before release.

## Weather fixture

`weather/singapore-changi-2011-2025.epw` is the frozen Singapore Changi
International Airport 486980 TMYx file for 2011–2025. It was retrieved on
1 September 2026 from Climate.OneBuilding.Org and has SHA-256
`9293635032609058428c34809b0c2fa90178cb73d2aaf857f0918b46893bf60c`.

The upstream authors describe TMYx as a typical year assembled from NOAA ISD
hourly observations using TMY/ISO 15927-4:2005 methods, with ERA5 solar data
for the 2026 release. The source asks users to cite Lawrie and Crawley (2026),
“Development of Global Typical Meteorological Years (TMYx),”
https://climate.onebuilding.org. The site does not publish a standalone licence
for this file; it is redistributed here only as the frozen input needed to
reproduce the submitted study. No ownership or endorsement is implied.
