#!/usr/bin/env python3
"""Build index.html from data/*.json.

All content is rendered into plain HTML at build time, so the page reads fully
without JavaScript (screen readers, simple fetchers, other AIs). JavaScript only
adds live countdowns, filtering, a shortlist and saved checklist ticks.

Run:  python3 build.py
"""
import json
import math
import re
from collections import Counter, defaultdict
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).parent
BUILD_DATE = date(2026, 11, 2)  # fallback "today" for the no-JS render

board = json.loads((ROOT / "data/board.json").read_text())
extra = json.loads((ROOT / "data/extra.json").read_text())
guide = json.loads((ROOT / "data/guide.json").read_text())

paths = board["paths"] + extra["paths"]
paths.sort(key=lambda p: p["rank"])

CATS = [
    ("fund", "Funded study", "Scholarships that cover the full cost of a degree."),
    ("phd", "Funded PhDs", "Free or salaried doctorates. Long, so graduation ages for a Match."),
    ("job", "Paid research jobs", "Paid posts abroad — the strongest bridge to a US Match."),
    ("clin", "Clinical licensing", "Exams and registration that lead to practising medicine."),
    ("self", "Self-funded & partial", "Measured against the USD 30k budget."),
    ("off", "Off-road routes", "Lesser-known options, including dead ends and why."),
    ("bd", "At home in Bangladesh", "Fallbacks and experience at home."),
]
CAT_NAME = {k: n for k, n, _ in CATS}
ELIG = {
    "now": ("Open to him now", "Open now", "now"),
    "post": ("Opens after internship", "After internship", "post"),
    "unc": ("Eligibility to confirm", "Check first", "unc"),
    "exp": ("Needs work experience", "Needs experience", "exp"),
    "closed": ("Closed or dead end", "Closed", "closed"),
}
ELIG_ORDER = ["now", "post", "unc", "exp", "closed"]
USM = {
    "helps": ("Helps the US goal", "up"),
    "neutral": ("Neutral for the US goal", "flat"),
    "hurts": ("Works against the US goal", "down"),
}
GETS = {
    "Visa only": "A way abroad (no licence)",
    "Both": "A way abroad + a licence",
    "Path to practice": "Leads to practising medicine",
    "Neither": "Neither visa nor licence",
    "Government job at home": "Government job at home",
    "Specialist training at home": "Specialist training at home",
    "—": "—",
}

e = lambda s: escape(str(s if s is not None else ""), quote=True)


def pdate(s):
    y, m, d = map(int, s.split("-"))
    return date(y, m, d)


def fmt(s, year=True):
    d = pdate(s)
    return d.strftime("%-d %b %Y" if year else "%-d %b")


def days_left(s):
    return (pdate(s) - BUILD_DATE).days


def rel(n):
    if n == 0:
        return "today"
    if n == 1:
        return "tomorrow"
    if n > 0:
        return f"in {n} days"
    if n == -1:
        return "yesterday"
    return f"{-n} days ago"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- stats
total = len(paths)
open_now = sum(p["elig"] == "now" for p in paths)
countries = sorted({p["country"] for p in paths})
upcoming = sorted(
    [p for p in paths if p.get("d") and days_left(p["d"]) >= 0 and p["elig"] != "closed"],
    key=lambda p: (p["d"], p["rank"]),
)
in60 = [p for p in upcoming if days_left(p["d"]) <= 60]
by_day = Counter(p["d"] for p in in60)
big_day = max(by_day.items(), key=lambda kv: (kv[1], -days_left(kv[0])))[0] if by_day else None
big_count = by_day.get(big_day, 0)
big_names = [p["name"] for p in upcoming if p["d"] == big_day]

# ---------------------------------------------------------------- hero map
# Equirectangular projection, cropped. Purely decorative (aria-hidden).
W, H = 1200, 600
def proj(lon, lat):
    return ((lon + 180) / 360 * W, (90 - lat) / 180 * H)

ORIGIN = ("Chattogram", 91.8, 22.3)
CITIES = [
    ("Boston", -71.1, 42.4), ("Baltimore", -76.6, 39.3), ("London", -0.1, 51.5),
    ("Paris", 2.35, 48.9), ("Berlin", 13.4, 52.5), ("Budapest", 19.0, 47.5),
    ("Istanbul", 29.0, 41.0), ("Riyadh", 46.7, 24.7), ("Doha", 51.5, 25.3),
    ("Beijing", 116.4, 39.9), ("Seoul", 127.0, 37.6), ("Tokyo", 139.7, 35.7),
    ("Hong Kong", 114.2, 22.3), ("Singapore", 103.8, 1.35), ("Sydney", 151.2, -33.9),
    ("Auckland", 174.8, -36.8), ("Stockholm", 18.1, 59.3), ("Lisbon", -9.1, 38.7),
]
LABELLED = {"Boston", "London", "Berlin", "Riyadh", "Tokyo", "Hong Kong", "Singapore", "Sydney", "Seoul"}
ox, oy = proj(ORIGIN[1], ORIGIN[2])
arcs, dots = [], []
for i, (name, lon, lat) in enumerate(CITIES):
    x, y = proj(lon, lat)
    mx, my = (ox + x) / 2, (oy + y) / 2
    dx, dy = x - ox, y - oy
    dist = math.hypot(dx, dy)
    nx, ny = -dy / dist, dx / dist
    if ny > 0:
        nx, ny = -nx, -ny  # always bow upward
    k = dist * 0.28
    cx, cy = mx + nx * k, my + ny * k
    arcs.append(
        f'<path class="arc" style="--i:{i};--len:{dist*1.25:.0f}" '
        f'd="M{ox:.1f} {oy:.1f} Q{cx:.1f} {cy:.1f} {x:.1f} {y:.1f}"/>'
    )
    dots.append(f'<circle class="city" style="--i:{i}" cx="{x:.1f}" cy="{y:.1f}" r="4"/>')
    if name in LABELLED:
        anchor = "end" if x < ox - 40 else "start"
        tx = x - 8 if anchor == "end" else x + 8
        ty = y + 5
        if name in ("Berlin", "Seoul", "Boston"):
            anchor, tx, ty = "middle", x, y - 12
        elif name == "London":
            anchor, tx = "end", x - 9
        elif name in ("Auckland",):
            anchor, tx, ty = "end", x, y + 20
        dots.append(f'<text class="city-l" style="--i:{i}" x="{tx:.1f}" y="{ty:.1f}" text-anchor="{anchor}">{e(name.upper())}</text>')

hero_svg = f'''<svg class="routes-svg" viewBox="330 80 880 360" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
  <defs>
    <pattern id="dotgrid" width="14" height="14" patternUnits="userSpaceOnUse"><circle cx="1.5" cy="1.5" r="1.1" class="grid-dot"/></pattern>
    <radialGradient id="fade" cx="70%" cy="50%" r="65%"><stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
    <mask id="m"><rect x="330" y="80" width="880" height="360" fill="url(#fade)"/></mask>
  </defs>
  <rect x="330" y="80" width="880" height="360" fill="url(#dotgrid)" mask="url(#m)"/>
  <g class="arcs">{"".join(arcs)}</g>
  <g>{"".join(dots)}</g>
  <circle class="origin-pulse" cx="{ox:.1f}" cy="{oy:.1f}" r="8"/>
  <circle class="origin" cx="{ox:.1f}" cy="{oy:.1f}" r="8"/>
  <text class="origin-l" x="{ox-10:.1f}" y="{oy+30:.1f}" text-anchor="end">CHATTOGRAM</text>
</svg>'''

# ---------------------------------------------------------------- departures
def flap(text):
    return "".join(
        f'<span class="flap" style="--c:{i}">{e(ch) if ch != " " else "&nbsp;"}</span>' for i, ch in enumerate(text)
    )


def dep_status(n):
    if n < 0:
        return ("Departed", "gone")
    if n <= 7:
        return ("Final call", "final")
    if n <= 30:
        return ("Boarding", "boarding")
    return ("Scheduled", "sched")


dep_rows = []
for i, p in enumerate(upcoming[:14]):
    n = days_left(p["d"])
    st, sc = dep_status(n)
    d_up = pdate(p["d"]).strftime("%d %b").upper()
    approx = p.get("a") == 1
    dep_rows.append(f'''<tr style="--r:{i}" data-d="{p["d"]}">
  <td class="dep-date"><span class="sr">{e(fmt(p["d"]))}{" (estimated)" if approx else ""}</span><span aria-hidden="true">{flap(("≈" if approx else "") + d_up)}</span></td>
  <td class="dep-dest">{e(p["country"].upper())}</td>
  <td class="dep-route"><a href="#p-{e(p["id"])}">{e(p["name"])}</a><span class="dep-sub">{e(p["country"])} · <span data-left="{p["d"]}">{e(rel(n))}</span> · <span class="st st-{sc}" data-st="{p["d"]}">{st}</span></span></td>
  <td class="dep-left" data-left="{p["d"]}">{e(rel(n))}</td>
  <td class="dep-st"><span class="st st-{sc}" data-st="{p["d"]}">{st}</span></td>
</tr>''')

# ---------------------------------------------------------------- cards
def card(p):
    el_long, el_short, el_cls = ELIG[p["elig"]]
    us_label, us_cls = USM.get(p.get("usmle", "neutral"), USM["neutral"])
    gets = GETS.get(p.get("gets", "—"), p.get("gets", ""))
    approx = p.get("a") == 1
    dl_html = ""
    if p.get("d"):
        n = days_left(p["d"])
        dl_html = (
            f'<p class="dl" data-dl="{p["d"]}"><span class="dl-date">{"≈ " if approx else ""}{e(fmt(p["d"]))}</span>'
            f'<span class="dl-rel" data-left="{p["d"]}">{e(rel(n))}</span></p>'
        )
    src = (
        f'<a class="src" href="{e(p["src"])}" rel="noopener" target="_blank">Official source<span class="sr"> for {e(p["name"])} (opens in a new tab)</span> ↗</a>'
        if p.get("src") else '<span class="src muted">No single official source — verify before acting</span>'
    )
    change = f'<p class="change"><strong>What changed:</strong> {e(p["change"])}</p>' if p.get("change") else ""
    note = f'<p>{e(p["note"])}</p>' if p.get("note") else ""
    search = " ".join([p["name"], p["country"], p.get("note", ""), p.get("gets", ""), p.get("cost", ""), CAT_NAME[p["cat"]]]).lower()
    new = '<span class="badge-new">Updated this week</span>' if p.get("isNew") else ""
    return f'''<li class="card" id="p-{e(p["id"])}" data-cat="{p["cat"]}" data-elig="{p["elig"]}" data-country="{e(p["country"])}" data-rank="{p["rank"]}" data-d="{p.get("d") or ""}" data-name="{e(p["name"].lower())}" data-q="{e(search)}">
  <article aria-labelledby="t-{e(p["id"])}">
    <div class="card-top">
      <p class="card-meta"><span>{e(p["country"])}</span><span aria-hidden="true"> · </span><span>{e(CAT_NAME[p["cat"]])}</span></p>
      <button type="button" class="star" data-star="{e(p["id"])}" aria-pressed="false"><span aria-hidden="true">★</span><span class="sr">Shortlist {e(p["name"])}</span></button>
    </div>
    <h3 id="t-{e(p["id"])}">{e(p["name"])}</h3>
    <p class="tags"><span class="elig elig-{el_cls}"><span class="ico" aria-hidden="true"></span>{e(el_long)}</span>{new}</p>
    <p class="when">{e(p.get("dt", ""))}</p>
    {dl_html}
    <dl class="facts">
      <div><dt>Money</dt><dd>{e(p.get("cost") or "—")}</dd></div>
      <div><dt>Timing</dt><dd>{e(p.get("time") or "—")}</dd></div>
      <div><dt>Gets him</dt><dd>{e(gets)}</dd></div>
      <div><dt>US goal</dt><dd class="us us-{us_cls}"><span class="ico" aria-hidden="true"></span>{e(us_label)}</dd></div>
    </dl>
    <details>
      <summary>Full notes &amp; source</summary>
      <div class="more">{change}{note}<p class="foot">{src}<span class="ver">Verified {e(fmt(p["v"]))}</span></p></div>
    </details>
  </article>
</li>'''


cards_html = "\n".join(card(p) for p in paths)
cat_counts = Counter(p["cat"] for p in paths)
elig_counts = Counter(p["elig"] for p in paths)

cat_chips = '<button type="button" class="seg" data-cat="all" aria-pressed="true">All <span class="n">%d</span></button>' % total
cat_chips += "".join(
    f'<button type="button" class="seg" data-cat="{k}" aria-pressed="false">{e(n)} <span class="n">{cat_counts[k]}</span></button>'
    for k, n, _ in CATS
)
elig_chips = "".join(
    f'<button type="button" class="chip chip-{k}" data-elig="{k}" aria-pressed="false"><span class="ico" aria-hidden="true"></span>{ELIG[k][1]} <span class="n">{elig_counts[k]}</span></button>'
    for k in ELIG_ORDER
)
country_opts = '<option value="">All countries &amp; regions</option>' + "".join(
    f'<option value="{e(c)}">{e(c)}</option>' for c in countries
)

# ---------------------------------------------------------------- calendar
months = defaultdict(list)
for p in paths:
    if p.get("d") and pdate(p["d"]) >= date(2026, 10, 1):
        months[p["d"][:7]].append(p)
cal_html = []
for ym in sorted(months):
    items = sorted(months[ym], key=lambda p: (p["d"], p["rank"]))
    y, m = map(int, ym.split("-"))
    label = date(y, m, 1).strftime("%B %Y")
    lis = "".join(
        f'<li data-d="{p["d"]}" class="cal-{p["elig"]}"><span class="cal-day">{"≈" if p.get("a") == 1 else ""}{pdate(p["d"]).day}</span>'
        f'<a href="#p-{e(p["id"])}">{e(p["name"])}</a><span class="cal-tag">{e(ELIG[p["elig"]][1])}</span></li>'
        for p in items
    )
    cal_html.append(
        f'<section class="month" data-ym="{ym}" aria-labelledby="m-{ym}"><h3 id="m-{ym}">{e(label)} <span class="n">{len(items)}</span></h3><ol>{lis}</ol></section>'
    )

# ---------------------------------------------------------------- prep, gates, log, watch
checklist = "".join(
    f'<li><label><input type="checkbox" data-tick="{i}"><span>{e(t)}</span></label></li>'
    for i, t in enumerate(guide["checklist"])
)
docs = "".join(
    f'<li><span class="doc-n" aria-hidden="true">{i+1:02d}</span><div><strong>{e(a)}</strong><span>{e(b)}</span></div></li>'
    for i, (a, b) in enumerate(guide["documents"])
)
gates = "".join(
    f'<li><h3>{e(a)}</h3><p>{e(b)}</p></li>' for a, b in guide["gates"]
)
log_items = sorted(board["log"] + guide["extraLog"], key=lambda x: x["date"], reverse=True)
log_html = "".join(
    f'<li><time datetime="{x["date"]}">{e(fmt(x["date"]))}</time><p>{e(x["text"])}</p></li>' for x in log_items
)
watch_html = "".join(f"<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>" for a, b in board["watch"])
truths = "".join(
    f'<li><span class="truth-n" aria-hidden="true">{i+1}</span><h3>{e(t["title"])}</h3><p>{e(t["body"])}</p></li>'
    for i, t in enumerate(guide["truths"])
)
journey = "".join(
    f'<li class="{"j-tag" if s.get("tag") else ""}"><span class="j-dot" aria-hidden="true"></span><p class="j-when">{e(s["when"])}{f" <span class=j-badge>{e(s["tag"])}</span>" if s.get("tag") else ""}</p><h3>{e(s["title"])}</h3><p>{e(s["body"])}</p></li>'
    for s in guide["journey"]
)

big_list = "".join(f"<li>{e(n)}</li>" for n in big_names[:8])
more_big = f"<li>+ {len(big_names) - 8} more</li>" if len(big_names) > 8 else ""

client_data = json.dumps(
    {"bigDay": big_day, "build": BUILD_DATE.isoformat()}, separators=(",", ":")
)

# ---------------------------------------------------------------- page
template = (ROOT / "site/template.html").read_text()
page = (
    template.replace("{{HERO_SVG}}", hero_svg)
    .replace("{{TOTAL}}", str(total))
    .replace("{{OPEN_NOW}}", str(open_now))
    .replace("{{IN60}}", str(len(in60)))
    .replace("{{COUNTRIES}}", str(len(countries)))
    .replace("{{BIG_DAY_LABEL}}", e(pdate(big_day).strftime("%-d %B")) if big_day else "—")
    .replace("{{BIG_DAY}}", big_day or "")
    .replace("{{BIG_DAYS_LEFT}}", str(days_left(big_day)) if big_day else "—")
    .replace("{{BIG_COUNT}}", str(big_count))
    .replace("{{BIG_LIST}}", big_list + more_big)
    .replace("{{DEP_ROWS}}", "\n".join(dep_rows))
    .replace("{{TRUTHS}}", truths)
    .replace("{{JOURNEY}}", journey)
    .replace("{{CAT_CHIPS}}", cat_chips)
    .replace("{{ELIG_CHIPS}}", elig_chips)
    .replace("{{COUNTRY_OPTS}}", country_opts)
    .replace("{{CARDS}}", cards_html)
    .replace("{{CALENDAR}}", "\n".join(cal_html))
    .replace("{{CHECKLIST}}", checklist)
    .replace("{{DOCS}}", docs)
    .replace("{{GATES}}", gates)
    .replace("{{LOG}}", log_html)
    .replace("{{WATCH}}", watch_html)
    .replace("{{PROFILE}}", e(guide["profile"]))
    .replace("{{PERSON}}", e(guide["person"]))
    .replace("{{LAST_SWEEP}}", e(fmt(board["meta"]["lastSweep"])))
    .replace("{{CLIENT_DATA}}", client_data)
)
left = re.findall(r"\{\{[A-Z_0-9]+\}\}", page)
assert not left, left
(ROOT / "index.html").write_text(page)
print(f"index.html written: {total} routes, {open_now} open now, {len(countries)} countries, next big day {big_day} ({big_count})")
