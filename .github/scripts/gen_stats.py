#!/usr/bin/env python3
"""Generate a Tokyo Night themed GitHub stats card as SVG (stdlib only)."""
import datetime
import json
import math
import os
import pathlib
import urllib.parse
import urllib.request

USER = "abilash0045"
NAME = "Abilash S L"
TOKEN = os.environ.get("GH_TOKEN", "")
API = "https://api.github.com"

BG = "#1a1b27"
TITLE = "#7aa2f7"
ICON = "#bb9af7"
TEXT = "#c0caf5"
RING_BG = "#2d3149"
FONT = "Segoe UI, Ubuntu, Helvetica, Arial, sans-serif"


def fetch(url):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "stats-card")
    if TOKEN:
        req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def search_count(endpoint, query):
    try:
        q = urllib.parse.quote(query, safe="")
        url = API + "/search/" + endpoint + "?per_page=1&q=" + q
        return int(fetch(url).get("total_count", 0))
    except Exception:
        return 0


user = fetch(API + "/users/" + USER)
repos = fetch(API + "/users/" + USER + "/repos?per_page=100&type=owner")
stars = sum(int(r.get("stargazers_count", 0)) for r in repos)
year = datetime.date.today().year
commits = search_count("commits", "author:" + USER + " committer-date:>=" + str(year) + "-01-01")
prs = search_count("issues", "author:" + USER + " type:pr")
issues = search_count("issues", "author:" + USER + " type:issue")
followers = int(user.get("followers", 0))

score = stars * 4 + prs * 3 + issues * 2 + followers * 2 + commits * 0.3
grades = [(120, "A+"), (80, "A"), (50, "B+"), (25, "B"), (10, "C+"), (0, "C")]
grade = next(g for s, g in grades if score >= s)
pct = max(0.08, min(score / 200.0, 1.0))
circumference = 2 * math.pi * 40
dash = pct * circumference

rows = [
    ("\u2605", "Total Stars Earned", stars),
    ("\u29d7", "Commits (" + str(year) + ")", commits),
    ("\u2442", "Total PRs", prs),
    ("\u25ce", "Total Issues", issues),
    ("\u2726", "Followers", followers),
]
row_svg = ""
y = 68
for icon, label, val in rows:
    row_svg += (
        '<text x="25" y="' + str(y) + '" fill="' + ICON + '" font-size="15" font-family="' + FONT + '">' + icon + "</text>"
        '<text x="52" y="' + str(y) + '" fill="' + TEXT + '" font-size="14" font-weight="600" font-family="' + FONT + '">' + label + ":</text>"
        '<text x="240" y="' + str(y) + '" fill="' + TEXT + '" font-size="14" font-weight="700" font-family="' + FONT + '">' + str(val) + "</text>"
    )
    y += 25

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="480" height="195" viewBox="0 0 480 195">'
    '<rect width="480" height="195" rx="10" fill="' + BG + '"/>'
    '<text x="25" y="38" fill="' + TITLE + '" font-size="18" font-weight="600" font-family="' + FONT + '">' + NAME + "&#39;s GitHub Stats</text>"
    + row_svg
    + '<circle cx="390" cy="115" r="40" stroke="' + RING_BG + '" stroke-width="8" fill="none"/>'
    '<circle cx="390" cy="115" r="40" stroke="' + TITLE + '" stroke-width="8" fill="none" stroke-linecap="round" stroke-dasharray="'
    + format(dash, ".1f") + " " + format(circumference, ".1f")
    + '" transform="rotate(-90 390 115)"/>'
    '<text x="390" y="124" fill="' + ICON + '" font-size="26" font-weight="800" text-anchor="middle" font-family="' + FONT + '">' + grade + "</text>"
    "</svg>"
)

out = pathlib.Path("dist")
out.mkdir(parents=True, exist_ok=True)
(out / "github-stats.svg").write_text(svg, encoding="utf-8")
print("stars", stars, "commits", commits, "prs", prs, "issues", issues, "followers", followers, "grade", grade)

