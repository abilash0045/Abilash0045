#!/usr/bin/env python3
"""Generate Tokyo Night themed GitHub profile cards as SVG (stdlib only)."""
import datetime
import json
import math
import os
import pathlib
import re
import urllib.parse
import urllib.request

USER = "abilash0045"
NAME = "Abilash S L"
TOKEN = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"

BG1, BG2 = "#1a1b27", "#16161e"
BORDER = "#2e344f"
TITLE = "#7aa2f7"
ACCENT = "#bb9af7"
TEXT = "#c0caf5"
MUTED = "#565f89"
RING_BG = "#2d3149"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

LANG_COLORS = {
    "Java": "#b07219", "HTML": "#e34c26", "CSS": "#563d7c", "JavaScript": "#f1e05a",
    "Python": "#3572A5", "TypeScript": "#3178c6", "C": "#555555", "C++": "#f34b7d",
    "C#": "#178600", "Shell": "#89e051", "Dockerfile": "#384d54",
    "Jupyter Notebook": "#DA5B0B", "Kotlin": "#A97BFF", "Go": "#00ADD8",
    "PHP": "#4F5D95", "Ruby": "#701516", "Swift": "#F05138", "SCSS": "#c6538c",
    "Vue": "#41b883", "Dart": "#00B4AB",
}


def fetch(url, raw=False):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "profile-cards")
    if not raw:
        req.add_header("Accept", "application/vnd.github+json")
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8", "replace")
    return data if raw else json.loads(data)


def search_count(endpoint, query):
    try:
        q = urllib.parse.quote(query, safe="")
        return int(fetch(API + "/search/" + endpoint + "?per_page=1&q=" + q).get("total_count", 0))
    except Exception:
        return 0


def fmt(d):
    return MONTHS[d.month - 1] + " " + str(d.day)


def card(w, h, inner):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="' + str(w) + '" height="' + str(h)
        + '" viewBox="0 0 ' + str(w) + " " + str(h) + '">'
        '<defs>'
        '<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0%" stop-color="' + BG1 + '"/><stop offset="100%" stop-color="' + BG2 + '"/></linearGradient>'
        '<linearGradient id="grad" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0%" stop-color="' + TITLE + '"/><stop offset="100%" stop-color="' + ACCENT + '"/></linearGradient>'
        '</defs>'
        '<rect x="0.5" y="0.5" width="' + str(w - 1) + '" height="' + str(h - 1)
        + '" rx="12" fill="url(#bg)" stroke="' + BORDER + '"/>'
        + inner + "</svg>"
    )


def title_block(text_, x=25):
    return (
        '<text x="' + str(x) + '" y="34" fill="' + TITLE + '" font-size="16" font-weight="700" font-family="' + FONT + '">' + text_ + "</text>"
        '<rect x="' + str(x) + '" y="42" width="56" height="3" rx="1.5" fill="url(#grad)"/>'
    )


# ----- data: stats -----
user = fetch(API + "/users/" + USER)
repos = fetch(API + "/users/" + USER + "/repos?per_page=100&type=owner")
stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
year = datetime.date.today().year
commits = search_count("commits", "author:" + USER + " committer-date:>=" + str(year) + "-01-01")
prs = search_count("issues", "author:" + USER + " type:pr")
issues = search_count("issues", "author:" + USER + " type:issue")
followers = int(user.get("followers", 0))

score = stars * 4 + prs * 3 + issues * 2 + followers * 2 + commits * 0.3
grades = [(150, "S"), (75, "A+"), (35, "A"), (15, "B+"), (5, "B"), (0, "C+")]
grade = next(g for s, g in grades if score >= s)
pct = max(0.1, min(score / 150.0, 1.0))
circ = 2 * math.pi * 38

rows = [
    ("Total Stars Earned", stars),
    ("Commits (" + str(year) + ")", commits),
    ("Total PRs", prs),
    ("Total Issues", issues),
    ("Followers", followers),
]
inner = title_block(NAME + "&#39;s GitHub Stats")
y = 74
for label, val in rows:
    inner += (
        '<circle cx="30" cy="' + str(y - 5) + '" r="3" fill="url(#grad)"/>'
        '<text x="44" y="' + str(y) + '" fill="' + TEXT + '" font-size="14" font-weight="600" font-family="' + FONT + '">' + label + "</text>"
        '<text x="252" y="' + str(y) + '" fill="' + ACCENT + '" font-size="14" font-weight="700" text-anchor="end" font-family="' + FONT + '">' + str(val) + "</text>"
    )
    y += 24
inner += (
    '<circle cx="345" cy="112" r="38" stroke="' + RING_BG + '" stroke-width="9" fill="none"/>'
    '<circle cx="345" cy="112" r="38" stroke="url(#grad)" stroke-width="9" fill="none" stroke-linecap="round" stroke-dasharray="'
    + format(pct * circ, ".1f") + " " + format(circ, ".1f") + '" transform="rotate(-90 345 112)"/>'
    '<text x="345" y="121" fill="' + TEXT + '" font-size="24" font-weight="800" text-anchor="middle" font-family="' + FONT + '">' + grade + "</text>"
)
stats_svg = card(420, 195, inner)

# ----- data: streak (public contributions calendar) -----
total_year = 0
cur = longest = 0
cur_range = long_range = "-"
window = "-"
try:
    html = fetch("https://github.com/users/" + USER + "/contributions", raw=True)
    days = []
    for m in re.finditer(r'<td[^>]*data-date="([0-9]{4}-[0-9]{2}-[0-9]{2})"[^>]*>', html):
        lm = re.search(r'data-level="([0-9])"', m.group(0))
        days.append((m.group(1), int(lm.group(1)) if lm else 0))
    tm = re.search(r'([0-9][0-9,]*)\s+contribution', html)
    if tm:
        total_year = int(tm.group(1).replace(",", ""))
    if days:
        dser = sorted(((datetime.date.fromisoformat(d), l) for d, l in days), key=lambda t: t[0])
        window = fmt(dser[0][0]) + ", " + str(dser[0][0].year) + " - Present"
        best = run = 0
        best_end = None
        for d, l in dser:
            if l > 0:
                run += 1
                if run > best:
                    best, best_end = run, d
            else:
                run = 0
        longest = best
        if best_end and best:
            long_range = fmt(best_end - datetime.timedelta(days=best - 1)) + " - " + fmt(best_end)
        idx = len(dser) - 1
        if idx >= 0 and dser[idx][1] == 0:
            idx -= 1
        end_d = None
        while idx >= 0 and dser[idx][1] > 0:
            if end_d is None:
                end_d = dser[idx][0]
            cur += 1
            idx -= 1
        if cur and end_d:
            cur_range = fmt(end_d - datetime.timedelta(days=cur - 1)) + " - " + fmt(end_d)
        if not total_year:
            total_year = sum(1 for _, l in dser if l > 0)
except Exception:
    pass

circ2 = 2 * math.pi * 34
frac = max(0.08, min(cur / 30.0, 1.0))
inner = title_block("Contribution Streak")
inner += '<line x1="150" y1="62" x2="150" y2="168" stroke="' + BORDER + '"/>'
inner += '<line x1="270" y1="62" x2="270" y2="168" stroke="' + BORDER + '"/>'
inner += (
    '<text x="87" y="108" fill="' + TITLE + '" font-size="26" font-weight="800" text-anchor="middle" font-family="' + FONT + '">' + format(total_year, ",") + "</text>"
    '<text x="87" y="132" fill="' + TEXT + '" font-size="12" font-weight="600" text-anchor="middle" font-family="' + FONT + '">Contributions</text>'
    '<text x="87" y="150" fill="' + MUTED + '" font-size="10" text-anchor="middle" font-family="' + FONT + '">' + window + "</text>"
)
inner += (
    '<circle cx="210" cy="104" r="34" stroke="' + RING_BG + '" stroke-width="7" fill="none"/>'
    '<circle cx="210" cy="104" r="34" stroke="url(#grad)" stroke-width="7" fill="none" stroke-linecap="round" stroke-dasharray="'
    + format(frac * circ2, ".1f") + " " + format(circ2, ".1f") + '" transform="rotate(-90 210 104)"/>'
    '<text x="210" y="113" fill="' + ACCENT + '" font-size="24" font-weight="800" text-anchor="middle" font-family="' + FONT + '">' + str(cur) + "</text>"
    '<text x="210" y="157" fill="' + TEXT + '" font-size="12" font-weight="600" text-anchor="middle" font-family="' + FONT + '">Current Streak</text>'
    '<text x="210" y="173" fill="' + MUTED + '" font-size="10" text-anchor="middle" font-family="' + FONT + '">' + cur_range + "</text>"
)
inner += (
    '<text x="333" y="108" fill="' + TITLE + '" font-size="26" font-weight="800" text-anchor="middle" font-family="' + FONT + '">' + str(longest) + "</text>"
    '<text x="333" y="132" fill="' + TEXT + '" font-size="12" font-weight="600" text-anchor="middle" font-family="' + FONT + '">Longest Streak</text>'
    '<text x="333" y="150" fill="' + MUTED + '" font-size="10" text-anchor="middle" font-family="' + FONT + '">' + long_range + "</text>"
)
streak_svg = card(420, 195, inner)

# ----- data: languages -----
lang_bytes = {}
for r in repos:
    if r.get("fork"):
        continue
    try:
        for k, v in fetch(API + "/repos/" + USER + "/" + r["name"] + "/languages").items():
            lang_bytes[k] = lang_bytes.get(k, 0) + int(v)
    except Exception:
        continue
top = sorted(lang_bytes.items(), key=lambda kv: -kv[1])[:6]
tot = sum(v for _, v in top) or 1
segs = [(k, v / tot) for k, v in top]

inner = title_block("Most Used Languages")
inner += '<clipPath id="bar"><rect x="25" y="62" width="810" height="12" rx="6"/></clipPath>'
inner += '<rect x="25" y="62" width="810" height="12" rx="6" fill="' + RING_BG + '"/>'
inner += '<g clip-path="url(#bar)">'
x = 25.0
for k, f in segs:
    w = 810 * f
    inner += '<rect x="' + format(x, ".1f") + '" y="62" width="' + format(w, ".1f") + '" height="12" fill="' + LANG_COLORS.get(k, "#8a92b2") + '"/>'
    x += w
inner += "</g>"
for i, (k, f) in enumerate(segs):
    cx = 25 + (i % 3) * 270
    cy = 103 + (i // 3) * 26
    inner += (
        '<circle cx="' + str(cx + 5) + '" cy="' + str(cy - 4) + '" r="5" fill="' + LANG_COLORS.get(k, "#8a92b2") + '"/>'
        '<text x="' + str(cx + 18) + '" y="' + str(cy) + '" fill="' + TEXT + '" font-size="13" font-weight="600" font-family="' + FONT + '">' + k + " " + format(f * 100, ".1f") + "%</text>"
    )
langs_svg = card(860, 150, inner)

# ----- write -----
out = pathlib.Path("dist")
out.mkdir(parents=True, exist_ok=True)
(out / "github-stats.svg").write_text(stats_svg, encoding="utf-8")
(out / "github-streak.svg").write_text(streak_svg, encoding="utf-8")
(out / "github-langs.svg").write_text(langs_svg, encoding="utf-8")
print("stats", stars, commits, prs, issues, followers, grade,
      "| streak", cur, longest, total_year,
      "| langs", [k for k, _ in segs])
