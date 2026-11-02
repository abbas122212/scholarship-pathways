# Scholarship Pathways

Every route abroad for a Bangladeshi MBBS graduate: funded degrees, salaried PhDs, paid research jobs and licensing paths, with live deadlines.

Live site: https://abbas122212.github.io/scholarship-pathways/

## How it's built
`index.html` is generated, so don't edit it by hand. Edit the data, then rebuild:

```
python3 build.py
```

- `data/board.json`: the Pathway Board export (121 routes, checklist, weekly log, watchlist)
- `data/extra.json`: routes from the master file that aren't on the board (Maastricht, Commonwealth Shared, US PhDs/MPHs, Italy, DAAD, Australia/NZ PhDs and others)
- `data/guide.json`: plan, journey, 30-day to-do, documents, open questions
- `site/template.html`: page design (CSS + a small script)
- `classic.html`: the previous version of the site

All content is rendered as plain HTML at build time, so the page reads fully without JavaScript, for screen readers and AIs fetching it. JavaScript only adds live countdowns, filters, the shortlist and saved checklist ticks.

## Other files
- `SCHOLARSHIP_PATHWAYS_MASTER.md`: canonical research notes
- `SCHOLARSHIP_PATHWAYS_INDEX.json`: machine-readable index
- `CLAUDE_CHECK_VERDICTS.md`: independent verification notes
