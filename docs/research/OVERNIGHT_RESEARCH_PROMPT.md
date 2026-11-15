# Overnight research prompt (paste into ChatGPT deep research)

You are doing source-checked research for a NASA Space Apps Challenge 2026 project called Moon Analog Finder. The project ranks Earth locations as terrain analogs for the lunar south pole using NASA and ESA elevation data. I need facts I can cite, not opinions or summaries from memory.

## Rules for every answer

1. Every fact must have a source URL and an exact quote from that source of 25 words or fewer that supports it.
2. Prefer primary sources: NASA, ESA, CSA, USGS, LPI, national geological surveys, UNESCO, government travel advisories, and peer-reviewed papers. Use Wikipedia only to find primary sources, and say so if it is the only source.
3. If you cannot find something, write NOT FOUND. Never estimate, infer or fill a gap from general knowledge.
4. If two sources disagree, give both and say they disagree.
5. Give coordinates in decimal degrees exactly as the source states them (convert degrees and minutes if needed and show the original).
6. Record the date you accessed each source.
7. Deliver one Markdown document with the sections and tables below, and nothing else.

## Task A: Artemis III candidate landing regions

NASA named nine regions on 28 October 2024: Peak near Cabeus B, Haworth, Malapert Massif, Mons Mouton Plateau, Mons Mouton, Nobile Rim 1, Nobile Rim 2, de Gerlache Rim 2, Slater Plain.
For each, find the centre latitude and longitude (or corner coordinates) from NASA, LPI, USGS or a peer-reviewed paper.
Table columns: region | latitude | longitude | what the coordinate refers to (centre, corner, named feature) | source URL | quote | access date.

## Task B: three candidate Earth sites

Site 1: 73.95 N, 25.18 W (East Greenland, possibly Andree Land, inside Northeast Greenland National Park)
Site 2: 37.32 N, 73.11 E (south-east Pamir, Tajikistan, about 55 km west of Lake Zorkul)
Site 3: 21.05 N, 16.45 E (Tarso Tousside volcano, Tibesti massif, Chad)

For each site answer, one row per fact:
- B1. The official name of the land area, valley or massif that contains the point.
- B2. Rock types at or within about 20 km of the point, from a geological survey map or paper.
- B3. Ground elevation at the point.
- B4. Any published use or proposal of this place, or its surrounding region, as an analog for the Moon or Mars, or any published comparison with lunar or Martian terrain. Search the scientific literature, not only the web.
- B5. Nearest airstrip, road and settlement, with distances.
- B6. Protected-area status and what permits research access requires.
- B7. Current government travel advice for the area (US State Department and UK FCDO), with the date of the advice.
- B8. Presence of glaciers or permanent snow within 10 km (for example from the Randolph Glacier Inventory or national maps).
Table columns: site | question | answer | source URL | quote | access date.

## Task C: has anyone already used these regions as lunar or Mars analogs?

For each region, report any published analog use or proposal, or NOT FOUND:
Peary Land (north Greenland); northern Ellesmere Island (Lake Hazen, Tanquary Fiord); Baffin Island interior (around 68 N, 68 W and 71.6 N, 75.8 W); the south-west Bolivian Altiplano (around 21.5 S, 67.8 W); the Pamir plateau; East Greenland fjord zone (72 to 75 N); the Taymyr Peninsula (around 75.8 N, 107 E); the Tibesti massif.
Table columns: region | Moon, Mars or none | what it was used for | source URL | quote | year.

## Task D: more established lunar analog sites

I already have: Antarctic Dry Valleys, Axel Heiberg Island, Black Point Lava Flow, Cinder Lake, Haughton crater, Kilauea, Lonar crater, Meteor Crater, Mistastin crater, Mount Etna, Ries crater, Sudbury, Sunset Crater, Tenerife, Atacama, Mauna Kea, Craters of the Moon, Askja, CHILL-ICE lava tube, Kilbourne Hole, Piton de la Fournaise.
Find at least 20 more outdoor field sites that a space agency or a peer-reviewed paper names as a lunar analog, astronaut geology training site or lunar hardware test site. Exclude indoor facilities and habitats.
Table columns: site | country | latitude | longitude | what it is an analog for (crater, anorthosite, regolith, lava terrain, operations) | who uses it | source URL | quote.

## Task E: is this finding already published?

Our measurement: using the same method on both bodies, the lunar south pole has a median Hurst exponent of about 0.93 for surface roughness over 80 m to 1.3 km, while Earth's bare land at the same slope has about 0.71, and the gap grows at longer distances.
- E1. Has any paper compared Hurst exponents or multi-scale roughness between the Moon and Earth? Give values.
- E2. What published Hurst exponent values exist for terrestrial landscapes at 100 m to 3 km scales?
- E3. What is published about bias in roughness or slope when comparing radar-derived elevation (TanDEM-X or Copernicus DEM) with laser altimetry (LOLA, ICESat-2)?
Table columns: question | finding | paper (authors, year, journal) | URL or DOI | quote.

## Task F: data inventory for Mars and for the whole Moon

I may extend the method from the lunar south pole to Mars and to the rest of the Moon. I need to know exactly which open datasets exist. Do not download anything; list what exists.
For each dataset give: name | body | what it measures | coverage | resolution (metres per pixel) | file format | direct download URL of the file or directory | approximate size | licence or usage terms | source page URL | quote confirming the resolution.

- F1. Mars global elevation: MOLA MEGDR, the MOLA and HRSC blended DEM (about 200 m), and any other global or near-global DEM. State true resolution and coverage of each.
- F2. Mars higher-resolution elevation with wide coverage: HRSC DTMs, CTX DTM mosaics. State how much of Mars each covers.
- F3. Mars surface temperature and thermal inertia global maps (TES, THEMIS, MCS): gridded products with download links.
- F4. Mars dust, albedo and rock abundance global maps.
- F5. Mars global slope or roughness products, and published Hurst exponent or multi-scale roughness values for Mars (for example Kreslavsky and Head; Aharonson et al.).
- F6. Coordinates of Mars landing sites to use as targets: all successful landers and rovers, and NASA's candidate human exploration zones if a list with coordinates is published.
- F7. Whole-Moon elevation: SLDEM2015 and the LOLA global gridded products, with exact file names, resolution and latitude coverage.
- F8. Whole-Moon temperature (Diviner global products), rock abundance, and any global slope or Hurst exponent maps (for example NASA PGDA products 67 and 70), with file names.
- F9. Apollo, Chang'e and other lunar landing site coordinates from a NASA or peer-reviewed source.
- F10. Established Mars analog field sites with coordinates from primary sources, beyond those in the ESA Catalogue of Planetary Analogues (2012).

## Final section: what you could not verify

List every item above that ended as NOT FOUND or with conflicting sources.
