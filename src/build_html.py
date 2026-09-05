#!/usr/bin/env python3
"""Build a static timeline site into docs/ from data/events.csv."""

from __future__ import annotations

import csv
import html
import json
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
BANNER_SRC = ASSETS / "2025-banner-west-face.jpg"
BANNER_DEST_NAME = "2025-banner-west-face.jpg"
BRUSHY_HERO_NAME = "1948-king-pp215.png"
BRUSHY_FORMATION = "brushy_canyon"
# Full-bleed slide backgrounds (cover-style). Keyed by event id.
SLIDE_BACKGROUNDS = {
    "king-1948-pp215": "1948-king-pp215.png",
    "beaubouef-1999-aapg-cn40": "1999-beaubouef-aapg-cn40-cover.png",
    "atlas-deep-water-outcrops-2007-aapg-sg56": "2007-atlas-deep-water-outcrops.jpeg",
}
# When True, CSV image is only used as background (not TimelineJS side media).
COVER_STYLE_ONLY = {
    "king-1948-pp215",
    "atlas-deep-water-outcrops-2007-aapg-sg56",
}

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


def parse_year(value: str | None) -> int | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Ma"):
        return None
    try:
        return int(text)
    except ValueError:
        return None


def image_web_path(filename: str | None) -> str | None:
    if not filename or not str(filename).strip():
        return None
    name = Path(str(filename).strip()).name
    if not (ASSETS / name).exists():
        return None
    return f"images/{name}"


def split_images(value: str | None) -> list[str]:
    """CSV image field may list multiple files separated by ';'."""
    return split_tags(value)


def collect_image_files(events: list[dict]) -> set[str]:
    names = {BANNER_DEST_NAME, BRUSHY_HERO_NAME}
    for ev in events:
        for img in split_images(ev.get("image")):
            names.add(Path(img).name)
    names.update(SLIDE_BACKGROUNDS.values())
    return names


def copy_images(names: set[str]) -> None:
    images_out = OUT / "images"
    images_out.mkdir(parents=True, exist_ok=True)
    for name in sorted(names):
        src = ASSETS / name
        if src.exists():
            shutil.copy2(src, images_out / name)


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
    credit = ev.get("image_credit") or ""
    figures = []
    image_names = split_images(ev.get("image"))
    for i, img_name in enumerate(image_names):
        img_path = image_web_path(img_name)
        if not img_path:
            continue
        # Credit once, under the last figure in a multi-image set.
        cap = credit if credit and i == len(image_names) - 1 else ""
        figures.append(
            f'<figure class="event-figure">'
            f'<img src="{esc(img_path)}" alt="" loading="lazy">'
            f'{f"<figcaption>{esc(cap)}</figcaption>" if cap else ""}'
            f"</figure>"
        )
    img_html = "".join(figures)

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
        {img_html}
        {f'<p class="event-people">{esc(people)}</p>' if people else ''}
        <p class="event-cite">{esc(ev.get('citations'))}</p>
      </div>
    </article>
    """


def slide_text_html(ev: dict) -> str:
    parts = [esc(ev.get("summary"))]
    people = ", ".join(ev["people_list"])
    if people:
        parts.append(f"<p><strong>People:</strong> {esc(people)}</p>")
    if ev.get("citations"):
        parts.append(f"<p><em>{esc(ev.get('citations'))}</em></p>")
    return "\n".join(parts)


def event_to_slide(ev: dict, era_labels: dict) -> dict:
    year = parse_year(ev.get("date_start"))
    if year is None:
        raise ValueError(f"Brushy timeline needs a numeric year for {ev.get('id')}")

    slide: dict = {
        "unique_id": ev["id"],
        "start_date": {"year": year, "display_date": str(ev.get("date_start") or year)},
        "text": {
            "headline": ev.get("title") or ev["id"],
            "text": slide_text_html(ev),
        },
        "group": era_labels.get(ev.get("era") or "", ev.get("era") or "Research"),
    }

    end_year = parse_year(ev.get("date_end"))
    if end_year is not None:
        slide["end_date"] = {"year": end_year}

    bg_name = SLIDE_BACKGROUNDS.get(ev["id"])
    bg_url = image_web_path(bg_name) if bg_name else None
    if bg_url:
        slide["background"] = {"url": bg_url, "color": "#1c2420"}

    # TimelineJS media: first CSV image (skip if cover-style-only).
    media_names = split_images(ev.get("image"))
    media_url = image_web_path(media_names[0]) if media_names else None
    if media_url and ev["id"] not in COVER_STYLE_ONLY:
        slide["media"] = {
            "url": media_url,
            "credit": ev.get("image_credit") or "",
            "alt": ev.get("title") or "",
        }

    return slide


def build_brushy_timeline_json(events: list[dict], era_labels: dict) -> dict:
    brushy = [e for e in events if BRUSHY_FORMATION in e["formation_list"]]
    title = {
        "text": {
            "headline": "Brushy Canyon research",
            "text": (
                "A TimelineJS view of events tagged <em>Brushy Canyon Formation</em> "
                "in The West Face dataset — names, maps, process models, and Mines theses."
            ),
        },
        "background": {
            "url": f"images/{BRUSHY_HERO_NAME}",
            "color": "#efe6d6",
            "alt": "King 1948 USGS Professional Paper 215 plate — El Capitan to Shumard Peak",
        },
    }
    return {
        "title": title,
        "events": [event_to_slide(e, era_labels) for e in brushy],
        "scale": "human",
    }


def build_brushy_page(n_events: int) -> str:
    # Cache-bust stylesheet: browsers otherwise keep an old styles.css after deploys.
    # TimelineJS treats initial_zoom: 0 as falsy and skips it; zoom_sequence[0]=0.5
    # also crushes the nav. Use index 1 (= 1× screen width) so 1942–2021 fits.
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Brushy Canyon — The West Face</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
  <link title="timeline-styles" rel="stylesheet" href="https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css">
  <link rel="stylesheet" href="styles.css?v=3">
</head>
<body class="page-brushy">
  <header class="subnav">
    <a class="subnav-brand" href="index.html">The West Face</a>
    <p class="subnav-title">Brushy Canyon · TimelineJS · {n_events} events</p>
    <a class="subnav-back" href="index.html">← Full Guads timeline</a>
  </header>
  <div id="timeline-embed" class="brushy-embed"></div>
  <script src="https://cdn.knightlab.com/libs/timeline3/latest/js/timeline.js"></script>
  <script>
    window.addEventListener("load", function () {{
      window.timeline = new TL.Timeline("timeline-embed", "brushy-timeline.json?v=4", {{
        hash_bookmark: true,
        initial_zoom: 1,
        scale_factor: 1,
        start_at_slide: 0,
        timenav_height_percentage: 34
      }});
    }});
  </script>
</body>
</html>
"""


def build() -> Path:
    eras_doc = load_yaml("eras.yaml")
    branches_doc = load_yaml("branches.yaml")
    formations_doc = load_yaml("formations.yaml")
    events = load_events()

    era_meta = {e["id"]: e for e in eras_doc["eras"]}
    era_order = [e["id"] for e in eras_doc["eras"]]
    era_labels = {e["id"]: e["label"] for e in eras_doc["eras"]}
    branch_labels = {b["id"]: b["label"] for b in branches_doc["branches"]}
    formation_labels = {f["id"]: f["label"] for f in formations_doc["formations"]}

    by_era: dict[str, list[dict]] = defaultdict(list)
    for ev in events:
        by_era[ev.get("era") or "unknown"].append(ev)

    used_branches = sorted({b for ev in events for b in ev["branch_list"]})
    used_formations = sorted({f for ev in events for f in ev["formation_list"]})
    brushy_events = [e for e in events if BRUSHY_FORMATION in e["formation_list"]]

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
  <link rel="stylesheet" href="styles.css?v=3">
</head>
<body>
  <header class="hero">
    <div class="hero-photo" role="img" aria-label="Western escarpment of the Guadalupe Mountains"></div>
    <div class="hero-veil"></div>
    <div class="hero-inner">
      <p class="hero-brand">The West Face</p>
      <p class="hero-sub">A research history of the Guadalupe Mountains — from deep time to today.</p>
      <p class="hero-note">{len(events)} events · <a class="hero-repo" href="brushy.html">Brushy Canyon TimelineJS</a> · <a class="hero-repo" href="https://github.com/zanejobe/the-west-face">GitHub repo</a></p>
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
    <p class="filter-status"><span id="visible-count">{len(events)}</span> events shown · <a href="brushy.html">Brushy Canyon TimelineJS view</a></p>
  </aside>

  <main class="timeline">
    {''.join(sections)}
  </main>

  <footer class="site-foot">
    <p><a href="brushy.html">Brushy Canyon TimelineJS</a> · <a href="https://github.com/zanejobe/the-west-face">GitHub repo</a> · edit <code>data/events.csv</code> then run <code>python src/build_html.py</code></p>
  </footer>

  <script src="timeline.js"></script>
</body>
</html>
"""

    OUT.mkdir(parents=True, exist_ok=True)
    copy_images(collect_image_files(events))

    brushy_json = build_brushy_timeline_json(events, era_labels)
    (OUT / "brushy-timeline.json").write_text(
        json.dumps(brushy_json, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "brushy.html").write_text(build_brushy_page(len(brushy_events)), encoding="utf-8")
    (OUT / "index.html").write_text(page, encoding="utf-8")
    return OUT / "index.html"


if __name__ == "__main__":
    path = build()
    brushy_n = len(json.loads((OUT / "brushy-timeline.json").read_text(encoding="utf-8"))["events"])
    print(f"Wrote {path}")
    print(f"Wrote {OUT / 'brushy.html'} ({brushy_n} Brushy events)")
    print(f"Wrote {OUT / 'brushy-timeline.json'}")
