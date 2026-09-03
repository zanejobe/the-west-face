#!/usr/bin/env python3
"""Build a static timeline site into docs/ from data/events.csv."""

from __future__ import annotations

import csv
import html
import shutil
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Install deps: pip install -r requirements.txt") from exc

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets" / "images"
OUT = ROOT / "docs"
BANNER_SRC = ASSETS / "banner-west-face.jpg"
BANNER_DEST_NAME = "banner-west-face.jpg"

BRANCH_COLORS = {
    "deep_time": "#6b5a3e",
    "mapping": "#3d5a4c",
    "stratigraphy": "#5c4a3a",
    "reef_and_shelf": "#8a6a4a",
    "basin_fill": "#4a5560",
    "sedimentology": "#2f4f4f",
    "petroleum": "#6b4423",
    "paleontology": "#4a5d4e",
    "park_science": "#3f5d4a",
    "digital_methods": "#3a4a5c",
    "education": "#5a4d3a",
}


def load_yaml(name: str) -> dict:
    with (DATA / name).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def split_tags(value: str | None) -> list[str]:
    if not value or not str(value).strip():
        return []
    return [p.strip() for p in str(value).split(";") if p.strip()]


def load_events() -> list[dict]:
    with (DATA / "events.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["branch_list"] = split_tags(row.get("branches"))
        row["formation_list"] = split_tags(row.get("formations"))
        row["people_list"] = split_tags(row.get("people"))
    rows.sort(key=lambda r: (r.get("date_start") or "", r.get("id") or ""))
    return rows


def esc(text: str | None) -> str:
    return html.escape(text or "", quote=True)


def chip(label: str, kind: str, color: str | None = None) -> str:
    style = f' style="--chip:{color}"' if color else ""
    return f'<span class="chip chip-{kind}"{style}>{esc(label)}</span>'


def render_event(ev: dict, branch_labels: dict, formation_labels: dict) -> str:
    primary = ev.get("branch_primary") or (ev["branch_list"][0] if ev["branch_list"] else "")
    color = BRANCH_COLORS.get(primary, "#5a5248")
    branches_html = "".join(
        chip(branch_labels.get(b, b), "branch", BRANCH_COLORS.get(b, "#5a5248"))
        for b in ev["branch_list"]
    )
    formations_html = "".join(
        chip(formation_labels.get(f, f), "formation") for f in ev["formation_list"]
    )
    people = ", ".join(ev["people_list"])
    data_branches = " ".join(ev["branch_list"])
    data_formations = " ".join(ev["formation_list"]) or "_none_"

    return f"""
    <article class="event" style="--accent:{color}"
      data-branches="{esc(data_branches)}"
      data-formations="{esc(data_formations)}"
      data-importance="{esc(ev.get('importance'))}">
      <div class="event-rail" aria-hidden="true"></div>
      <div class="event-body">
        <div class="event-meta">
          <time class="event-year">{esc(ev.get('date_start'))}</time>
          <div class="event-chips">{branches_html}{formations_html}</div>
        </div>
        <h3 class="event-title">{esc(ev.get('title'))}</h3>
        <p class="event-summary">{esc(ev.get('summary'))}</p>
        {f'<p class="event-people">{esc(people)}</p>' if people else ''}
        <p class="event-cite">{esc(ev.get('citations'))}</p>
      </div>
    </article>
    """


def build() -> Path:
    eras_doc = load_yaml("eras.yaml")
    branches_doc = load_yaml("branches.yaml")
    formations_doc = load_yaml("formations.yaml")
    events = load_events()

    era_meta = {e["id"]: e for e in eras_doc["eras"]}
    era_order = [e["id"] for e in eras_doc["eras"]]
    branch_labels = {b["id"]: b["label"] for b in branches_doc["branches"]}
    formation_labels = {f["id"]: f["label"] for f in formations_doc["formations"]}

    by_era: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        by_era[ev.get("era") or "unknown"].append(ev)

    used_branches = sorted({b for ev in events for b in ev["branch_list"]})
    used_formations = sorted({f for ev in events for f in ev["formation_list"]})

    branch_filters = "\n".join(
        f'<label class="filter"><input type="checkbox" name="branch" value="{esc(b)}" checked> '
        f'{esc(branch_labels.get(b, b))}</label>'
        for b in used_branches
    )
    formation_filters = "\n".join(
        [
            '<label class="filter"><input type="checkbox" name="formation" value="_none_" checked> '
            "No formation tag</label>"
        ]
        + [
            f'<label class="filter"><input type="checkbox" name="formation" value="{esc(f)}" checked> '
            f'{esc(formation_labels.get(f, f))}</label>'
            for f in used_formations
        ]
    )

    sections = []
    # Deep-time placeholder if no geologic events yet
    geo_events = [e for e in events if e.get("timescale") == "geologic"]
    if not geo_events:
        sections.append(
            """
            <section class="era era-geologic" id="permian_deposition">
              <header class="era-header">
                <p class="era-kicker">Act I · Geologic time</p>
                <h2>Permian deposition</h2>
                <p class="era-desc">Placeholder — add deep-time rows to events.csv for Brushy Canyon / Capitan depositional landmarks.</p>
              </header>
              <div class="hinge">
                <p>From rock time to research time</p>
              </div>
            </section>
            """
        )
    else:
        sections.append(
            '<div class="hinge hinge-standalone"><p>From rock time to research time</p></div>'
        )

    for era_id in era_order:
        era_events = by_era.get(era_id, [])
        if not era_events:
            continue
        meta = era_meta.get(era_id, {"label": era_id, "description": ""})
        timescale = meta.get("timescale", "human")
        kicker = "Act I · Geologic time" if timescale == "geologic" else "Act II · Research time"
        body = "\n".join(render_event(e, branch_labels, formation_labels) for e in era_events)
        sections.append(
            f"""
            <section class="era" id="{esc(era_id)}" data-timescale="{esc(timescale)}">
              <header class="era-header">
                <p class="era-kicker">{esc(kicker)}</p>
                <h2>{esc(meta.get('label', era_id))}</h2>
                <p class="era-desc">{esc(meta.get('description', ''))}</p>
              </header>
              <div class="era-events">{body}</div>
            </section>
            """
        )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>The West Face — Guadalupe Mountains research timeline</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="hero">
    <div class="hero-photo" role="img" aria-label="Western escarpment of the Guadalupe Mountains"></div>
    <div class="hero-veil"></div>
    <div class="hero-inner">
      <p class="hero-brand">The West Face</p>
      <p class="hero-sub">A research history of the Guadalupe Mountains — from deep time to today.</p>
      <p class="hero-note">{len(events)} events · <a class="hero-repo" href="https://github.com/zanejobe/the-west-face">GitHub repo</a></p>
    </div>
  </header>

  <aside class="filters" aria-label="Timeline filters">
    <details open>
      <summary>Filter by research branch</summary>
      <div class="filter-grid">{branch_filters}</div>
    </details>
    <details open>
      <summary>Filter by formation</summary>
      <div class="filter-grid">{formation_filters}</div>
    </details>
    <p class="filter-status"><span id="visible-count">{len(events)}</span> events shown</p>
  </aside>

  <main class="timeline">
    {''.join(sections)}
  </main>

  <footer class="site-foot">
    <p><a href="https://github.com/zanejobe/the-west-face">GitHub repo</a> · edit <code>data/events.csv</code> then run <code>python src/build_html.py</code></p>
  </footer>

  <script src="timeline.js"></script>
</body>
</html>
"""

    OUT.mkdir(parents=True, exist_ok=True)
    images_out = OUT / "images"
    images_out.mkdir(parents=True, exist_ok=True)
    if BANNER_SRC.exists():
        shutil.copy2(BANNER_SRC, images_out / BANNER_DEST_NAME)
    (OUT / "index.html").write_text(page, encoding="utf-8")
    return OUT / "index.html"


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path}")
