# Scholarship Pathways — static website bundle

Plain HTML, **no JavaScript** — any AI or browser can read it with a simple fetch.

## Deploy free (pick one, ~2 minutes)
- **GitHub Pages:** create a public repo, upload these files, Settings → Pages → deploy from main branch. Site goes live at https://<username>.github.io/<repo>/
- **Netlify Drop:** go to app.netlify.com/drop and drag this folder in. Instant public URL, no account needed to try.
- **Cloudflare Pages:** dash.cloudflare.com → Pages → upload assets, add this folder.

## Files
- `index.html` — the website (all 36 pathways, deadline calendar, open gates, verification log)
- `SCHOLARSHIP_PATHWAYS_MASTER.md` — canonical data any AI can edit
- `SCHOLARSHIP_PATHWAYS_INDEX.json` — machine-readable index

## Update workflow
Any AI verifies an entry on its official source → returns updated Markdown/JSON with source URL + date → owner applies the change to the master file → redeploy (or ask Muse to regenerate index.html from the master file).
