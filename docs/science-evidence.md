# Science evidence and geographic candidates

Research checked 2026-11-12. Real named sampling regions are recorded in `data/sources/science-candidates.json`; they are not registered sample-site waypoints. `data/region/science-stops.json` contains three explicitly hypothetical observation points on the prepared real CTX terrain, with source-backed regional context and no asserted sample identities.

## Verified sources

- NASA’s [Perseverance Rover Location Map](https://science.nasa.gov/mission/mars-2020-perseverance/location-map/) says its high-resolution color base map uses MRO/HiRISE imagery and its broader regional base map uses ESA Mars Express HRSC imagery. It describes each map dot as a drive endpoint labeled by Mars sol. The page does not expose machine-readable traverse coordinates in its text.
- NASA’s [Mars Rock Samples inventory](https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/) lists Ha’ahóni, sealed on Sol 371 (2022-03-07), and Atsá, sealed on Sol 377 (2022-03-13), as rock cores from “Octavia E. Butler Landing / Ch’ał outcrop.” The page gives no coordinates for those individual sampling locations.
- The [PDS Geosciences Mars 2020 archive index](https://pds-geosciences.wustl.edu/missions/mars2020/) links instrument archives, the sample dossier and rover PLACES bundle. Its Release 16 notice is dated 2026-08-11 and covers sols 1740–1859 (2026-01-10 to 2026-05-13). This index does not itself provide a traverse GeoJSON.
- The dedicated [PDS Rover PLACES bundle page](https://pds-geosciences.wustl.edu/missions/mars2020/places.htm) verifies an official coordinate-data lead: Release 16 covers rover localizations and mechanism positions from 2021-02-18 through 2026-06-21 (sols 0–1897). The landing page does not identify a ready-made GeoJSON; inspect its collections, SIS and release notes to determine coordinate frames and whether localization points can be responsibly used as traverse endpoints.

## Candidate and coordinate limits

“Octavia E. Butler Landing / Ch’ał outcrop” is retained as a named science-region candidate because NASA associates two real sample records with it. It is not converted into two waypoints: the inventory lacks site coordinates, and no source-backed point coordinate or uncertainty radius was verified. Do not use the sample names to label hypothetical destinations.

The planning crop reference (18.4446, 77.4509) is only a discovery reference, not independently verified here as an exact landing coordinate or supplied by the user. No claim is made that the named sampling region falls inside the final crop. The hypothetical targets are local grid-cell centers, not inferred positions of real sample sites. Null location uncertainty means no measured geodetic uncertainty was established; grid spacing is recorded separately.

## Challenge-page access

Direct Space Apps requests failed with an issuer-certificate error, so TLS verification was not bypassed. The correct official URL and its search-indexed challenge description are documented in [challenge alignment](challenge-alignment.md); direct Resources-tab verification remains outstanding. The old `mars.nasa.gov` rover-location URL redirected successfully (with verified TLS) to the NASA Science location-map URL above.

## Traverse-data follow-up

No ready-to-use traverse GeoJSON was verified during this pass. PDS Rover PLACES is an official coordinate/localization-data lead; inspect its product collections and SIS before treating it as a geographic traverse. Keep real named sample sites unregistered until coordinate provenance, crop inclusion, uncertainty, and local XY conversion are documented.
