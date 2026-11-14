# Scholarship Pathways

Every route abroad for a Bangladeshi MBBS graduate: funded degrees, salaried PhDs, paid research jobs and licensing paths, with live deadlines.

Live site: https://abbas122212.github.io/scholarship-pathways/

## Four sites
| Site | Folder | Theme | What's on it |
|---|---|---|---|
| Full board | `index.html` (root) | Green | All 180 routes, unchanged |
| USA | `usa/` | Navy & red | PhDs, MPHs, paid research jobs, internships, summer programmes, USMLE |
| Europe & Erasmus | `europe/` | EU blue & gold | UK + Europe, with **Erasmus Mundus as its own section** |
| Australia, NZ, Middle East & Asia | `world/` | Sand & terracotta | Australia, NZ, Gulf, Asia, plus global and at-home options |

Each regional site has a "By type" overview (master's, PhDs, jobs, internships & study tours, licensing, self-funded, off-road).
Mainland China is left off the regional sites (CSC, Yenching); Hong Kong's HKPFS is kept. Both mainland routes stay on the full board.
Routes that span regions (e.g. UN internships, World Bank scholarship) appear on every site they fit. The build fails if any
route on the full board is missing from all three regional sites.

The live site is published from the `gh-pages` branch, so after merging, deploy the built files there.

## How it's built
`index.html` is generated, so don't edit it by hand. Edit the data, then rebuild (this writes `index.html`, `usa/`, `europe/` and `world/`):

```
python3 build.py
```

- `data/board.json`: the Pathway Board export (121 routes, checklist, weekly log, watchlist)
- `data/extra.json`: routes from the master file that aren't on the board (Maastricht, Commonwealth Shared, US PhDs/MPHs, Italy, DAAD, Australia/NZ PhDs and others)
- `data/guide.json`: plan, journey, 30-day to-do, documents, open questions
- `data/packs.json`: application packs (USA 1 Dec, MRC North West, SOPHAS guide, MPH shortlist, guidance)
- `sources/`: the uploaded research notes, verbatim, plus `sources/verification/` (web checks against official pages, 9 Nov 2026)
- `data/regional.json`: routes shown only on the regional sites (study tours and short programmes added 14 Nov 2026)
- `regions.py`: which routes go on which regional site, themes, the Erasmus section and the China note
- `site/template.html`: page design (CSS + a small script)
- `classic.html`: the previous version of the site

All content is rendered as plain HTML at build time, so the page reads fully without JavaScript, for screen readers and AIs fetching it. JavaScript only adds live countdowns, filters, the shortlist and saved checklist ticks.

## Other files
- `SCHOLARSHIP_PATHWAYS_MASTER.md`: canonical research notes
- `SCHOLARSHIP_PATHWAYS_INDEX.json`: machine-readable index
- `CLAUDE_CHECK_VERDICTS.md`: independent verification notes
- `addenda/`: dated additions not yet merged into the master file or the site: the SOPHAS intake-term addendum, the Italy expanded target list, the "Eight New Routes" file, and a verification note for the new routes (10 Nov 2026)
