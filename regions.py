"""Regional sites: usa/, europe/ and world/.

Each site is built by build.build() from the same data as the full board
(index.html), filtered to one region and given its own colour theme.
The full board at the root keeps every route; nothing is removed from it.

Run:  python3 build.py   (builds the full board and all three regional sites)
"""
import json
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
e = lambda s: escape(str(s if s is not None else ""), quote=True)

REGIONAL_EXTRA = json.loads((ROOT / "data/regional.json").read_text())["paths"]

# ------------------------------------------------------------------ membership
USA_COUNTRIES = {"USA", "USA / BD", "Switzerland / USA"}
EUROPE_COUNTRIES = {
    "Europe", "UK", "Germany", "Italy", "Ireland", "Sweden", "Switzerland", "Austria",
    "Belgium", "Netherlands", "Malta", "Hungary", "Türkiye", "France", "Czechia",
    "Geneva / SEARO", "Switzerland / USA",
}
WORLD_COUNTRIES = {
    "Australia", "New Zealand", "Japan", "Singapore", "Saudi Arabia", "Qatar", "UAE", "Gulf",
    "Thailand", "Canada", "South Korea", "Malaysia", "Hong Kong", "Brunei", "Japan / Korea",
    "Caribbean", "Bangladesh", "Remote", "Various", "—", "Geneva / SEARO", "Türkiye",
}
# Global routes that also belong on another regional site.
ALSO = {
    "usa": {"jjwbgsp", "akf-isp", "unicef-intern", "unfpa-intern"},  # US universities / New York HQs
    "europe": {"intlra", "otherschol", "jjwbgsp", "akf-isp"},        # UK posts, Holland/Italy/OeAD, UK universities
    "world": set(),
}
# China is left off the regional sites (see the note on the World site).
# Exception kept: Hong Kong's HKPFS, a salaried PhD (≈USD 44k/yr + travel) under Hong Kong's own system.
CHINA_EXCLUDED = {"csc", "yenching"}

COUNTRIES = {"usa": USA_COUNTRIES, "europe": EUROPE_COUNTRIES, "world": WORLD_COUNTRIES}

# Internships, study tours and short programmes get their own type on the regional sites.
SHORT_IDS = {"who", "unicef-intern", "unfpa-intern", "gavi-intern", "obs", "kcl-aero"}


def is_erasmus(p):
    return p["id"].startswith("emjm-") or p["id"] == "euhem"


def in_region(p, region):
    if p["id"] in CHINA_EXCLUDED:
        return False
    return p["country"] in COUNTRIES[region] or p["id"] in ALSO[region]


# ------------------------------------------------------------------ types
BASE_CATS = [
    ("fund", "Funded master's & scholarships", "Scholarships that cover the full cost of a degree."),
    ("phd", "Funded PhDs", "Free or salaried doctorates. Long, so graduation ages for a Match."),
    ("job", "Paid research jobs", "Paid posts — the strongest bridge to a US Match."),
    ("short", "Internships, study tours & short programmes", "UN internships, observerships, summer institutes and invited visits."),
    ("clin", "Clinical licensing", "Exams and registration that lead to practising medicine."),
    ("self", "Self-funded & partial", "Measured against the USD 30k budget."),
    ("off", "Off-road routes", "Lesser-known options, including dead ends and why."),
    ("bd", "At home in Bangladesh", "Fallbacks and experience at home."),
]
ERASMUS_CAT = ("erasmus", "Erasmus Mundus", "Joint master's across 2–3 European countries, most with a full scholarship.")


def region_paths(all_paths, region):
    out = []
    for p in list(all_paths) + REGIONAL_EXTRA:
        if not in_region(p, region):
            continue
        q = dict(p)
        if q["id"] in SHORT_IDS:
            q["cat"] = "short"
        if region == "europe" and is_erasmus(q):
            q["cat"] = "erasmus"
        out.append(q)
    return out


def cats_for(paths, region):
    used = {p["cat"] for p in paths}
    cats = list(BASE_CATS)
    if region == "europe":
        cats.insert(0, ERASMUS_CAT)
    return [c for c in cats if c[0] in used]


# ------------------------------------------------------------------ switcher
SITES = [("all", "Full board", ""), ("usa", "USA", "usa/"), ("europe", "Europe & Erasmus", "europe/"),
         ("world", "Australia, NZ, Middle East & Asia", "world/")]


def region_bar(current, base):
    links = "".join(
        f'<a href="{base}{path or "./"}"{" aria-current=" + chr(34) + "page" + chr(34) if key == current else ""}>{e(name)}</a>'
        for key, name, path in SITES
    )
    return f'<nav class="rbar" aria-label="Regional sites"><div class="wrap"><span class="rbar-k">Sites</span>{links}</div></nav>'


# ------------------------------------------------------------------ themes
def theme(light, dark):
    lv = ";".join(f"--{k}:{v}" for k, v in light.items())
    dv = ";".join(f"--{k}:{v}" for k, v in dark.items())
    return (f":root{{{lv}}}\n@media (prefers-color-scheme:dark){{:root:not([data-theme=\"light\"]){{{dv}}}}}\n"
            f":root[data-theme=\"dark\"]{{{dv}}}")


THEMES = {
    # Navy and red
    "usa": theme(
        {"bg": "#F5F6FA", "bg2": "#ECEEF5", "line": "#D9DCE6", "line2": "#C3C8D6", "accent": "#B31942", "accent-2": "#8E1434",
         "accent-soft": "#F8E1E7", "on-accent": "#FFFFFF", "map-arc": "#B31942", "map-dot": "#0A3161", "grid-dot": "#C9CEDB",
         "board": "#0A1A33", "board-2": "#10244A", "board-line": "#22365E", "amber": "#FF9EAE"},
        {"bg": "#0B1020", "bg2": "#10172B", "surface": "#141C33", "line": "#24304D", "line2": "#32405F", "accent": "#FF6B86",
         "accent-2": "#FF95A8", "accent-soft": "#3A1522", "on-accent": "#1A0510", "map-arc": "#FF6B86", "map-dot": "#E6EAF5",
         "grid-dot": "#26324E", "board": "#060B18", "board-2": "#0D1426", "board-line": "#22365E", "amber": "#FF9EAE"},
    ),
    # EU blue and gold
    "europe": theme(
        {"bg": "#F3F5FB", "bg2": "#E8ECF7", "line": "#D5DBEC", "line2": "#BFC7DE", "accent": "#0033A0", "accent-2": "#002877",
         "accent-soft": "#DFE6FA", "on-accent": "#FFFFFF", "map-arc": "#0033A0", "map-dot": "#15171C", "grid-dot": "#C5CDE3",
         "board": "#0B1640", "board-2": "#112056", "board-line": "#24346E", "amber": "#FFCC00"},
        {"bg": "#0A0F1F", "bg2": "#0F1630", "surface": "#131B38", "line": "#232E55", "line2": "#303D6B", "accent": "#8FB0FF",
         "accent-2": "#B3CAFF", "accent-soft": "#16224A", "on-accent": "#050A1A", "map-arc": "#FFD43B", "map-dot": "#E8ECF7",
         "grid-dot": "#25305A", "board": "#050A1A", "board-2": "#0B1230", "board-line": "#24346E", "amber": "#FFCC00"},
    ),
    # Desert sand and terracotta
    "world": theme(
        {"bg": "#F8F2E9", "bg2": "#F0E7D9", "line": "#E2D5C1", "line2": "#D0BFA6", "accent": "#B4461A", "accent-2": "#8F3613",
         "accent-soft": "#F8E2D6", "on-accent": "#FFFFFF", "map-arc": "#B4461A", "map-dot": "#2A1E14", "grid-dot": "#D9C9B0",
         "board": "#1C120C", "board-2": "#26190F", "board-line": "#3A2A1D", "amber": "#FFB35C"},
        {"bg": "#14100C", "bg2": "#1A1510", "surface": "#211A13", "line": "#33291F", "line2": "#43362A", "accent": "#FF9A5C",
         "accent-2": "#FFB685", "accent-soft": "#3D2213", "on-accent": "#1E0C03", "map-arc": "#FF9A5C", "map-dot": "#F3EADF",
         "grid-dot": "#3A2F24", "board": "#0E0906", "board-2": "#170F0A", "board-line": "#3A2A1D", "amber": "#FFB35C"},
    ),
}
FAVICON = {"usa": "%23B31942", "europe": "%230033A0", "world": "%23B4461A"}

# ------------------------------------------------------------------ hero map cities
CITIES = {
    "usa": [("Boston", -71.1, 42.4), ("New York", -74.0, 40.7), ("Baltimore", -76.6, 39.3)],
    "europe": [("London", -0.1, 51.5), ("Paris", 2.35, 48.9), ("Berlin", 13.4, 52.5), ("Budapest", 19.0, 47.5),
               ("Stockholm", 18.1, 59.3), ("Lisbon", -9.1, 38.7), ("Istanbul", 29.0, 41.0), ("Geneva", 6.1, 46.2),
               ("Maastricht", 5.7, 50.8)],
    "world": [("Riyadh", 46.7, 24.7), ("Doha", 51.5, 25.3), ("Abu Dhabi", 54.4, 24.5), ("Tokyo", 139.7, 35.7),
              ("Seoul", 127.0, 37.6), ("Hong Kong", 114.2, 22.3), ("Singapore", 103.8, 1.35), ("Bangkok", 100.5, 13.75),
              ("Sydney", 151.2, -33.9), ("Melbourne", 145.0, -37.8), ("Auckland", 174.8, -36.8)],
}
LABELLED = {
    "usa": {"Boston"},
    "europe": {"London", "Berlin", "Stockholm", "Lisbon", "Istanbul"},
    "world": {"Riyadh", "Tokyo", "Seoul", "Singapore", "Sydney", "Auckland"},
}

# ------------------------------------------------------------------ page text
TEXT = {
    "usa": {
        "title": "Scholarship Pathways · USA",
        "h1": "Every road to the USA, <em>mapped.</em>",
        "where": "in the United States",
        "desc": "Every route to the USA for a Bangladeshi MBBS graduate: PhDs, MPHs, paid research jobs, internships, summer programmes and USMLE, with live deadlines.",
    },
    "europe": {
        "title": "Scholarship Pathways · Europe & Erasmus",
        "h1": "Every road into Europe, <em>mapped.</em>",
        "where": "in Europe and the UK, with Erasmus Mundus on its own",
        "desc": "Every route to Europe and the UK for a Bangladeshi MBBS graduate: Erasmus Mundus, master's scholarships, salaried PhDs, internships and licensing, with live deadlines.",
    },
    "world": {
        "title": "Scholarship Pathways · Australia, NZ, Middle East & Asia",
        "h1": "Australia, the Gulf and Asia, <em>mapped.</em>",
        "where": "in Australia, New Zealand, the Middle East and Asia (plus global and at-home options)",
        "desc": "Every route to Australia, New Zealand, the Middle East and Asia for a Bangladeshi MBBS graduate: PhDs, scholarships, study tours, internships and licensing, with live deadlines.",
    },
}

PATTERN_OLD = ("<p><strong>The pattern.</strong> Nothing scores above 4 right now. The best odds are the government schemes where "
               "Bangladesh is a partner (Stipendium Hungaricum, CSC) and the health-focused Erasmus Mundus programmes.")
PATTERN_NEW = ("<p><strong>The pattern.</strong> Across the whole board nothing scores above 4 right now, and the best odds sit with "
               "government schemes where Bangladesh is a partner and the health-focused Erasmus Mundus programmes.")


def post_replacements(region):
    t = TEXT[region]
    reps = [
        ("<title>Scholarship Pathways</title>", f"<title>{e(t['title'])}</title>"),
        ("Every road out, <em>mapped.</em>", t["h1"]),
        ("routes to study, research and practise medicine abroad", f"routes to study, research and practise medicine {e(t['where'])}"),
        ("fill='%23006A4E'", f"fill='{FAVICON[region]}'"),
        ('<span class="brand-mark" aria-hidden="true"><i></i></span>Pathways</a>',
         f'<span class="brand-mark" aria-hidden="true"><i></i></span>Pathways · {e({"usa": "USA", "europe": "Europe", "world": "World"}[region])}</a>'),
        (PATTERN_OLD, PATTERN_NEW),
    ]
    for f in ("SCHOLARSHIP_PATHWAYS_MASTER.md", "CLAUDE_CHECK_VERDICTS.md", "data/board.json", "data/apply.json",
              "data/stories.json", "classic.html"):
        reps.append((f'href="{f}"', f'href="../{f}"'))
    return reps


# ------------------------------------------------------------------ extra sections
def types_section(L):
    """At-a-glance list of every route on this site, grouped by type."""
    by = {}
    for p in L["paths"]:
        by.setdefault(p["cat"], []).append(p)
    items = []
    for k, name, desc in L["CATS"]:
        ps = by.get(k, [])
        links = "".join(f'<li><a href="#p-{e(p["id"])}">{e(p["name"])}</a></li>' for p in ps)
        items.append(f'<li><h3>{e(name)} <span class="muted">· {len(ps)}</span></h3><p>{e(desc)}</p>'
                     f'<details><summary>Show all {len(ps)}</summary><ul class="x-links">{links}</ul></details></li>')
    return (f'<section class="sec" id="types" aria-labelledby="types-h"><div class="wrap"><div class="sec-head">'
            f'<div><p class="eyebrow">What is on this site</p><h2 id="types-h">By type</h2></div>'
            f'<p>Every route on this site, grouped: master&#8217;s, PhDs, jobs, internships and study tours, licensing and more. '
            f'Open a group to jump to a route.</p></div><ul class="xsec-intro">{"".join(items)}</ul></div></section>')


def _short(name):
    n = name.replace("Erasmus Mundus: ", "")
    return n[:1].upper() + n[1:]


def erasmus_section(L):
    ps = sorted([p for p in L["paths"] if p["cat"] == "erasmus"], key=lambda p: (p.get("d") or "9999", p["rank"]))
    rows = []
    for p in ps:
        d = p.get("d")
        od = L["ODDS"].get(p["id"])
        story = f'<a href="#story-{e(p["id"])}">Read →</a>' if p["id"] in L["STORIES"] else ""
        rows.append(
            f'<tr><td data-label="Programme"><a href="#p-{e(p["id"])}">{e(_short(p["name"]))}</a>'
            f'<span class="x-sub">{e(p.get("dt", ""))}</span></td>'
            f'<td data-label="Closes">{(("≈ " if p.get("a") == 1 else "") + e(L["fmt"](d))) if d else "—"}</td>'
            f'<td data-label="Status">{e(L["ELIG"][p["elig"]][1])}</td>'
            f'<td data-label="Money">{e(p.get("cost") or "—")}</td>'
            f'<td data-label="Odds">{(str(od["score"]) + "/10") if od else "—"}</td>'
            f'<td data-label="Story">{story}</td></tr>'
        )
    facts = [
        ("What it pays", "The standard Erasmus Mundus scholarship: €1,400 a month for up to 24 months, plus a waiver of the participation fee."),
        ("How you apply", "There is no central portal. Apply programme by programme, to up to three Erasmus Mundus programmes in one cycle."),
        ("When", "Windows run from October to January, each programme with its own dates. The table is sorted by closing date."),
        ("Watch out", "Not every joint master's carries the scholarship. Eu-HEM, for example, states the EMJM scholarship is not available."),
    ]
    intro = "".join(f"<li><h3>{e(a)}</h3><p>{e(b)}</p></li>" for a, b in facts)
    return (f'<section class="sec alt" id="erasmus" aria-labelledby="er-h"><div class="wrap"><div class="sec-head">'
            f'<div><p class="eyebrow">Its own section</p><h2 id="er-h">Erasmus Mundus · {len(ps)} programmes</h2></div>'
            f'<p>Two-year joint master&#8217;s taught across two or three European universities. For a fresh MBBS graduate these are the '
            f'best odds on the whole board. Every programme also has a full card under All routes (filter: Erasmus Mundus).</p></div>'
            f'<ul class="xsec-intro">{intro}</ul>'
            f'<div class="xtab-wrap"><table class="xtab"><caption class="sr">Erasmus Mundus programmes, soonest deadline first</caption>'
            f'<thead><tr><th scope="col">Programme</th><th scope="col">Closes</th><th scope="col">Status</th><th scope="col">Money</th>'
            f'<th scope="col">Odds</th><th scope="col">Story</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div></div></section>')


def china_section(L, all_by_id):
    rows = "".join(
        f'<li><h3>{e(all_by_id[k]["name"])}</h3><p>{e(all_by_id[k].get("cost", ""))}. {e(why)}</p></li>'
        for k, why in [
            ("csc", "A full degree in mainland China. Not a short or paid trip, and neutral for the US goal, so it is left off."),
            ("yenching", "Fully paid including airfare, but it is a China Studies master's, not health, and a hard selection. Left off."),
        ]
    )
    rows += ('<li><h3>Kept: Hong Kong PhD Fellowship (HKPFS)</h3><p>Hong Kong runs its own system and HKPFS pays a salary '
             '(≈USD 44k a year plus travel), so it stays on this site as the exception. It is a long shot (2/10).</p></li>')
    return (f'<section class="sec alt" id="china" aria-labelledby="cn-h"><div class="wrap"><div class="sec-head">'
            f'<div><p class="eyebrow">Left out on purpose</p><h2 id="cn-h">Why there is no China here</h2></div>'
            f'<p>Mainland China is excluded unless a route is a free or paid trip, or highly beneficial and easy to get. '
            f'Both mainland routes are still on the <a href="../#p-csc">full board</a>.</p></div>'
            f'<ul class="xsec-intro">{rows}</ul></div></section>')


EXTRA_CSS = ".x-links{margin:10px 0 0;padding-left:18px;font-size:.92rem}.x-links li{margin:4px 0}"


def config(all_paths, region, cats):
    all_by_id = {p["id"]: p for p in all_paths}

    def extra(L):
        html = types_section(L)
        if region == "europe":
            html = erasmus_section(L) + html
        if region == "world":
            html += china_section(L, all_by_id)
        return html

    nav = {"europe": '\n      <a href="#erasmus">Erasmus</a>', "world": '\n      <a href="#china">No China?</a>'}.get(region, "")
    return {
        "cats": cats,
        "cities": CITIES[region],
        "labelled": LABELLED[region],
        "region_bar": region_bar(region, "../"),
        "theme_css": THEMES[region] + "\n" + EXTRA_CSS,
        "extra_nav": '\n      <a href="#types">By type</a>' + nav,
        "extra_sections": extra,
        "desc": TEXT[region]["desc"],
        "post": post_replacements(region),
    }


def build_all(build, all_paths):
    seen = set()
    for region in ("usa", "europe", "world"):
        paths = region_paths(all_paths, region)
        seen |= {p["id"] for p in paths}
        page, info = build(paths, config(all_paths, region, cats_for(paths, region)))
        out = ROOT / region / "index.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page)
        print(f"{region}/index.html written: {info['total']} routes, {info['open_now']} open now, {len(info['countries'])} countries")
    # Guard: every route on the full board must appear on at least one regional site (except the China exclusions).
    missing = [p["id"] for p in all_paths if p["id"] not in seen and p["id"] not in CHINA_EXCLUDED]
    assert not missing, f"routes missing from every regional site: {missing}"
