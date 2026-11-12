# Science evidence and geographic candidates

Research checked 2026-11-12. The local projected origin is not yet defined, so `data/region/science-stops.json` intentionally contains no routable `scienceStops` or `positionXY` values.

## Verified sources

- NASA’s [Perseverance Rover Location Map](https://science.nasa.gov/mission/mars-2020-perseverance/location-map/) says its high-resolution color base map uses MRO/HiRISE imagery and its broader regional base map uses ESA Mars Express HRSC imagery. It describes each map dot as a drive endpoint labeled by Mars sol. The page does not expose machine-readable traverse coordinates in its text.
- NASA’s [Mars Rock Samples inventory](https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/) lists Ha’ahóni, sealed on Sol 371 (2022-03-07), and Atsá, sealed on Sol 377 (2022-03-13), as rock cores from “Octavia E. Butler Landing / Ch’ał outcrop.” The page gives no coordinates for those individual sampling locations.
- The [PDS Geosciences Mars 2020 archive index](https://pds-geosciences.wustl.edu/missions/mars2020/) links instrument archives, the sample dossier and rover PLACES bundle. Its Release 16 notice is dated 2026-08-11 and covers sols 1740–1859 (2026-01-10 to 2026-05-13). This index does not itself provide a traverse GeoJSON.
- The dedicated [PDS Rover PLACES bundle page](https://pds-geosciences.wustl.edu/missions/mars2020/places.htm) verifies an official coordinate-data lead: Release 16 covers rover localizations and mechanism positions from 2021-02-18 through 2026-06-21 (sols 0–1897). The landing page does not identify a ready-made GeoJSON; inspect its collections, SIS and release notes to determine coordinate frames and whether localization points can be responsibly used as traverse endpoints.

## Candidate and coordinate limits

“Octavia E. Butler Landing / Ch’ał outcrop” is retained as a named science-region candidate because NASA associates two real sample records with it. It is not converted into two waypoints: the inventory lacks site coordinates, and no source-backed point coordinate or uncertainty radius was verified. Do not use the sample names to label hypothetical destinations.

The crop center (18.4446, 77.4509) was supplied by the project request. It is only a crop reference, not verified here as the exact landing coordinate. No claim is made that the candidate falls inside the final crop until A1 establishes crop bounds and a geographic source is available. A hypothetical waypoint may be added only as a clearly labeled, non-sample target after those bounds and the coordinate transform are agreed.

## Challenge-page access

The official 2026 Space Apps challenge URL attempted was `https://www.spaceappschallenge.org/2026/challenges/the-martian-map/`. The fetch failed with an issuer-certificate error; strict `curl` verification also failed, so TLS verification was not bypassed. The challenge page/resources and any linked datasets therefore remain unverified. The old `mars.nasa.gov` rover-location URL did redirect successfully (with verified TLS) to the NASA Science location-map URL above.

## Traverse-data follow-up

No ready-to-use traverse GeoJSON was verified during this pass. PDS Rover PLACES is an official coordinate/localization-data lead; inspect its product collections and SIS before treating it as a geographic traverse. Keep science stops unregistered until coordinate provenance, crop inclusion, uncertainty, and local XY conversion are documented.
