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
APPLY = json.loads((ROOT / "data/apply.json").read_text())["routes"]
STORIES = json.loads((ROOT / "data/stories.json").read_text())["stories"]
ODDS = json.loads((ROOT / "data/odds.json").read_text())["routes"]


def odds_label(n):
    return ["No funded route", "Very long shot", "Long shot", "Outside chance", "Realistic", "Realistic", "Good chance", "Good chance", "Strong", "Strong", "Very strong"][n]


FACTOR_NAME = {"eligibility": "Eligibility", "competition": "Room in the field", "profile": "Profile match", "timing": "Timing fit"}
FACTOR_HINT = {"eligibility": "Do you clearly qualify?", "competition": "How crowded the field is (more = less crowded)", "profile": "How close you are to who they pick", "timing": "Does the start date fit your internship?"}


def dial(n, cls="dial"):
    return (f'<span class="{cls}" style="--s:{n}" aria-hidden="true"><svg viewBox="0 0 44 44" focusable="false">'
            f'<circle class="d-bg" cx="22" cy="22" r="18" pathLength="100"/><circle class="d-fg" cx="22" cy="22" r="18" pathLength="100"/></svg>'
            f'<span class="d-n">{n}</span></span>')


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


def rich(text):
    """Escape, then turn **bold** into <strong>."""
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(text))


FEE_CLS = {"free": "fee-free", "paid": "fee-paid", "unk": "fee-unk"}
FEE_ICON = {"free": "✓", "paid": "¤", "unk": "?"}


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
    ap = APPLY.get(p["id"])
    has_story = p["id"] in STORIES
    apply_html = ""
    if ap:
        apply_html = (
            f'<div class="apply"><p class="fee {FEE_CLS[ap["kind"]]}"><span class="fee-k">Application fee</span>'
            f'<strong><span class="fee-i" aria-hidden="true">{FEE_ICON[ap["kind"]]}</span> {e(ap["fee"])}</strong></p>'
            + (f'<p class="fee card-odds"><span class="fee-k">Your odds</span><strong>{ODDS[p["id"]]["score"]}/10 · {odds_label(ODDS[p["id"]]["score"])}</strong></p>' if p["id"] in ODDS else "")
            + f'<a class="portal" href="{e(ap["portal_url"])}" target="_blank" rel="noopener">Open portal<span class="sr"> for {e(p["name"])} (opens in a new tab)</span> <span aria-hidden="true">↗</span></a></div>'
        )
    story_html = (
        f'<a class="story-link" href="#story-{e(p["id"])}"><span>Read the story</span><span class="sr"> about {e(p["name"])}</span> <span aria-hidden="true">→</span></a>'
        if has_story else ""
    )
    feekind = ap["kind"] if ap else ""
    return f'''<li class="card" id="p-{e(p["id"])}" data-fee="{feekind}" data-cat="{p["cat"]}" data-elig="{p["elig"]}" data-country="{e(p["country"])}" data-rank="{p["rank"]}" data-d="{p.get("d") or ""}" data-name="{e(p["name"].lower())}" data-q="{e(search)}">
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
    {apply_html}
    {story_html}
    <details>
      <summary>Full notes &amp; source</summary>
      <div class="more">{change}{note}<p class="foot">{src}<span class="ver">Verified {e(fmt(p["v"]))}</span></p></div>
    </details>
  </article>
</li>'''


cards_html = "\n".join(card(p) for p in paths)
PBYID = {p["id"]: p for p in paths}

FIT_LABEL = {"good": "Good fit", "mixed": "Mixed", "poor": "Poor fit"}
FIT_NAME = {"us": "US Match, 2029 plan", "eu": "Practising in Europe", "interest": "Your interests"}


DEST = {
    "imperial-pres": ("LHR", "London"), "oist-phd": ("OKA", "Okinawa"), "sanger-phd": ("STN", "Cambridge"),
    "eth-esop": ("ZRH", "Zurich"), "yenching": ("PEK", "Beijing"), "clarendon": ("LHR", "Oxford"),
    "emjm-neurasmus": ("BOD", "Bordeaux"), "hkpfs": ("HKG", "Hong Kong"), "jhu-phd": ("BWI", "Baltimore"),
    "emory-phd": ("ATL", "Atlanta"), "singa": ("SIN", "Singapore"), "mps": ("FRA", "Germany"),
    "euhem": ("OSL", "Oslo"), "gates": ("STN", "Cambridge"), "cw-shared": ("LHR", "United Kingdom"),
    "emjm-noha": ("BRU", "Europe"), "unc-phd": ("RDU", "Chapel Hill"), "mbzuai": ("AUH", "Abu Dhabi"),
}
STAMP = {"ok": "Strong fit", "warn": "Proceed with care", "bad": "Not funded"}
FIT_VAL = {"good": 100, "mixed": 62, "poor": 26}


def split_fix(t):
    label, body = "", t
    m = re.match(r"^([A-Z][^:]{1,38}):\s+(.*)$", t)
    if m:
        label, body = m.group(1), m.group(2)
    was, now = [], []
    for x in re.split(r"(?<=[.])\s+(?=[A-Z])", body):
        if x.startswith("Gemini"):
            a, _, b = x.partition("; ")
            was.append(a if not b else a + ".")
            if b:
                now.append(b[0].upper() + b[1:])
        else:
            now.append(x)
    return label, " ".join(was), " ".join(now)


def gauge(k, v):
    val = FIT_VAL[v[0]]
    return (
        f'<li class="g g-{v[0]}"><svg viewBox="0 0 120 68" aria-hidden="true" focusable="false">'
        f'<path class="g-bg" d="M10 62 A50 50 0 0 1 110 62" pathLength="100"/>'
        f'<path class="g-fg" d="M10 62 A50 50 0 0 1 110 62" pathLength="100" style="--v:{val}"/></svg>'
        f'<span class="g-l">{FIT_LABEL[v[0]]}</span><span class="g-n">{FIT_NAME[k]}</span><span class="g-t">{e(v[1])}</span></li>'
    )


def story_html(pid, st):
    p = PBYID[pid]
    ap = APPLY.get(pid)
    code, city = DEST.get(pid, ("—", p["country"]))
    sid = f"story-{e(pid)}"
    chapters, toc = [], []
    for i, sec in enumerate(st["sections"]):
        cid = f"c-{e(pid)}-{i}"
        catches = sec["h"].lower().startswith("the catches")
        body = "".join(f"<p>{rich(x)}</p>" for x in sec.get("p", []))
        if sec.get("ul"):
            if catches:
                items = []
                for j, x in enumerate(sec["ul"]):
                    m = re.match(r"^\*\*(Catch \d+: [^*]+?)\.?\*\*\s*(.*)$", x)
                    head, rest = (m.group(1), m.group(2)) if m else (f"Catch {j+1}", x)
                    head = re.sub(r"^Catch \d+:\s*", "", head)
                    items.append(f'<li><span class="c-n" aria-hidden="true">{j+1:02d}</span><div><h4><span class="sr">Catch {j+1}: </span>{e(head.rstrip("."))}</h4><p>{rich(rest)}</p></div></li>')
                body += '<ol class="catch-grid">' + "".join(items) + "</ol>"
            else:
                body += "<ul>" + "".join(f"<li>{rich(x)}</li>" for x in sec["ul"]) + "</ul>"
        chapters.append(f'<section class="ch{" ch-catch" if catches else ""}" id="{cid}" aria-labelledby="{cid}-h"><p class="ch-n" aria-hidden="true">{i+1:02d}</p><h3 id="{cid}-h">{e(sec["h"])}</h3>{body}</section>')
        toc.append(f'<li><a href="#{sid}" data-jump="{cid}"><span aria-hidden="true">{i+1:02d}</span>{e(sec["h"])}</a></li>')
    fixes = []
    for x in st["fixed"]:
        label, was, now = split_fix(x)
        lab = f'<p class="fx-l">{e(label)}</p>' if label else ""
        if was:
            w2 = re.sub(r"^Gemini (?:said|quoted) ", "", was)
            w2 = w2[:1].upper() + w2[1:]
            fixes.append(f'<li>{lab}<div class="fx-row"><p class="fx-was"><span class="fx-k">Gemini&#8217;s draft</span><s>{rich(w2)}</s></p><p class="fx-now"><span class="fx-k">Official page</span>{rich(now) if now else "Corrected"}</p></div></li>')
        else:
            fixes.append(f'<li>{lab}<div class="fx-row fx-solo"><p class="fx-now"><span class="fx-k">Fact-check note</span>{rich(now)}</p></div></li>')
    fee = e(ap["fee"]) if ap else "—"
    closes = e(fmt(p["d"])) if p.get("d") else "Rolling"
    portal_btn = (
        f'<a class="board-btn" href="{e(ap["portal_url"])}" target="_blank" rel="noopener">Board now<span class="sr">: open the application portal for {e(p["name"])} (opens in a new tab)</span> <span aria-hidden="true">↗</span></a>'
        if ap else ""
    )
    od = ODDS.get(pid)
    odds_html = ""
    if od:
        facs = "".join(
            f'<li><span class="of-n">{FACTOR_NAME[k]}<span class="of-h">{FACTOR_HINT[k]}</span></span>'
            f'<span class="of-bar" aria-hidden="true">{"".join(f"<i class={chr(34)}on{chr(34)}></i>" if j < v else "<i></i>" for j in range(3))}</span>'
            f'<span class="of-v">{v} of 3</span></li>'
            for k, v in od["factors"].items()
        )
        raise_ = "".join(f"<li>{e(x)}</li>" for x in od["raise"])
        odds_html = (
            f'<section class="odds-box o-{od["score"]}" aria-labelledby="od-{e(pid)}"><div class="odds-dial">{dial(od["score"], "dial dial-xl")}<p class="odds-big"><span class="sr">Score: </span>{od["score"]}<small>/10</small></p></div>'
            f'<div class="odds-txt"><p class="fx-k">Your odds this cycle</p><h3 id="od-{e(pid)}">{odds_label(od["score"])}</h3><p>{e(od["why"])}</p>'
            f'<ul class="ofac">{facs}</ul><p class="fx-k" style="margin-top:16px">What would raise it</p><ul class="oraise">{raise_}</ul>'
            f'<p class="onote">An estimate of the chance of a <em>funded</em> place, from what the board knows (marks and class rank unknown). Not a statistic.</p></div></section>'
        )
    box = ""
    if ap:
        box = (
            f'<div class="howto"><h3>Before you board</h3><p class="howto-portal"><span class="fx-k">Portal</span>'
            f'<a href="{e(ap["portal_url"])}" target="_blank" rel="noopener">{e(ap["portal_label"])} <span aria-hidden="true">↗</span><span class="sr"> (opens in a new tab)</span></a></p>'
            f'<p>{e(ap["fee_note"])}</p><p class="howto-check"><strong>How this was checked:</strong> {e(ap["check"])}</p></div>'
        )
    return f'''<article class="story" id="{sid}" role="dialog" aria-modal="true" aria-labelledby="st-{e(pid)}" tabindex="-1" data-tone="{st["tone"]}">
  <div class="story-sheet">
    <div class="story-bar"><span class="story-prog" aria-hidden="true"></span><p class="eyebrow">Route story · {e(p["country"])}</p><a class="story-close" href="#p-{e(pid)}">Close <span aria-hidden="true">✕</span><span class="sr"> story</span></a></div>
    <header class="pass-stage">
      <div class="pass" aria-label="Boarding pass summary">
        <div class="pass-main">
          <p class="pass-air"><span class="pass-logo" aria-hidden="true"></span>PATHWAYS · BOARDING PASS</p>
          <div class="pass-route">
            <p class="pass-port"><span class="pc">CGP</span><span class="pn">Chattogram</span></p>
            <svg class="pass-arc" viewBox="0 0 200 60" aria-hidden="true" focusable="false"><path d="M6 50 Q100 -14 194 50" pathLength="100"/><g class="pass-plane"><path d="M0 -5 L4 0 L0 5 L1 0 Z M-6 -1 L4 -1 L4 1 L-6 1 Z"/></g></svg>
            <p class="pass-port pass-to"><span class="pc">{e(code)}</span><span class="pn">{e(city)}</span></p>
          </div>
          <h2 id="st-{e(pid)}">{e(p["name"])}</h2>
          <dl class="pass-f">
            <div><dt>Passenger</dt><dd>Dr A. U. Chowdhury</dd></div>
            <div><dt>Gate closes</dt><dd>{closes}</dd></div>
            <div><dt>Fare to apply</dt><dd>{fee}</dd></div>
            <div><dt>Odds</dt><dd>{(str(ODDS[pid]["score"]) + "/10 · " + odds_label(ODDS[pid]["score"])) if pid in ODDS else "—"}</dd></div>
          </dl>
        </div>
        <div class="pass-stub">
          <p class="stub-k">Seat</p><p class="stub-code">{e(code)}</p>
          {portal_btn}
          <span class="barcode" aria-hidden="true"></span>
        </div>
        <p class="stamp" role="note"><span class="sr">Verdict: </span>{e(STAMP[st["tone"]])}</p>
      </div>
    </header>
    <div class="story-body">
      <nav class="toc" aria-label="Chapters"><p class="toc-h">Chapters</p><ol>{"".join(toc)}<li><a href="#{sid}" data-jump="od-{e(pid)}"><span aria-hidden="true">%</span>Your odds</a></li><li><a href="#{sid}" data-jump="fx-{e(pid)}"><span aria-hidden="true">✓</span>Fact-check</a></li></ol></nav>
      <div class="story-main">
        <p class="verdict v-{st["tone"]}"><span class="v-i" aria-hidden="true"></span>{e(st["tag"])}</p>
        <p class="story-lede">{rich(st["lede"])}</p>
        <p class="ai-note"><span aria-hidden="true">✦</span> Drafted by Gemini (an AI), then rewritten and fact-checked against official pages on 2 Nov 2026. Where they disagreed, the official page won.</p>
        <ul class="gauges" aria-label="How it fits your goals">{"".join(gauge(k, v) for k, v in st["fit"].items())}</ul>
        {odds_html}
        {box}
        {"".join(chapters)}
        <section class="factcheck" id="fx-{e(pid)}" aria-labelledby="fx-{e(pid)}-h"><p class="ch-n" aria-hidden="true">✓</p><h3 id="fx-{e(pid)}-h">Fact-check: Gemini vs the official pages</h3><ul class="fx">{"".join(fixes)}</ul></section>
        <div class="story-end">{portal_btn}<a class="btn btn-ghost" href="#p-{e(pid)}">Back to the route</a></div>
      </div>
    </div>
  </div>
</article>'''


stories_html = "\n".join(story_html(k, v) for k, v in STORIES.items() if k in PBYID)

desk_ids = sorted(
    [k for k in APPLY if k in PBYID],
    key=lambda k: ((PBYID[k].get("d") or "9999"), PBYID[k]["rank"]),
)
desk_rows = []
for k in desk_ids:
    p, ap = PBYID[k], APPLY[k]
    d = p.get("d")
    date_cell = e(fmt(d)) if d else "—"
    bundle = f' data-bundle="{ap["bundle"]}"' if ap.get("bundle") else ""
    desk_rows.append(f'''<tr data-id="{e(k)}" data-d="{d or ""}" data-cur="{ap["cur"]}" data-amt="{ap["amt"]}"{bundle}>
  <td data-label="Closes" class="dk-date">{date_cell}<span class="dk-rel" data-left="{d or ""}">{e(rel(days_left(d))) if d else ""}</span></td>
  <td data-label="Route" class="dk-name"><a href="#p-{e(k)}">{e(p["name"])}</a><span class="dk-c">{e(p["country"])}</span></td>
  <td data-label="Portal"><a class="portal" href="{e(ap["portal_url"])}" target="_blank" rel="noopener">{e(ap["portal_label"])} <span aria-hidden="true">↗</span><span class="sr"> (opens in a new tab)</span></a></td>
  <td data-label="Fee"><span class="fee {FEE_CLS[ap["kind"]]}"><strong><span class="fee-i" aria-hidden="true">{FEE_ICON[ap["kind"]]}</span> {e(ap["fee"])}</strong></span></td>
  <td data-label="Odds" class="dk-odds">{(dial(ODDS[k]["score"], "dial dial-sm") + f'<span class="dk-ov">{ODDS[k]["score"]}/10</span>') if k in ODDS else ""}</td>
  <td data-label="Story">{f'<a class="story-link" href="#story-{e(k)}">Read <span class="sr">the story about {e(p["name"])} </span>→</a>' if k in STORIES else ""}</td>
  <td data-label="Cost" class="dk-tick"><label><input type="checkbox" class="calc" data-id="{e(k)}"><span class="sr">Add {e(p["name"])} to the fee estimate</span></label></td>
</tr>''')
desk_html = "\n".join(desk_rows)
odds_ids = sorted([k for k in ODDS if k in PBYID], key=lambda k: (-ODDS[k]["score"], PBYID[k].get("d") or "9999"))
odds_rows = "".join(
    f'<li class="ob o-{ODDS[k]["score"]}"><a href="#story-{e(k)}"><span class="ob-name">{e(PBYID[k]["name"])}<span class="ob-c">{e(PBYID[k]["country"])} · closes {e(fmt(PBYID[k]["d"])) if PBYID[k].get("d") else "rolling"}</span></span>'
    f'<span class="ob-track" aria-hidden="true"><span class="ob-fill" style="--s:{ODDS[k]["score"]}"></span></span>'
    f'<span class="ob-v"><strong>{ODDS[k]["score"]}</strong>/10<span class="ob-l">{odds_label(ODDS[k]["score"])}</span></span></a></li>'
    for k in odds_ids
)
free_n = sum(1 for k in desk_ids if APPLY[k]["kind"] == "free")
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
    .replace("{{STORIES}}", stories_html)
    .replace("{{DESK_ROWS}}", desk_html)
    .replace("{{ODDS_ROWS}}", odds_rows)
    .replace("{{DESK_N}}", str(len(desk_ids)))
    .replace("{{DESK_FREE}}", str(free_n))
    .replace("{{STORY_N}}", str(len([k for k in STORIES if k in PBYID])))
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
