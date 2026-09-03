# The West Face

## [View the live timeline →](https://zanejobe.github.io/the-west-face/)

**A research history of the Guadalupe Mountains — from deep time to today.**

The western escarpment of the Guadalupes (El Capitan, Capitan reef margin, Delaware Basin fill including Brushy Canyon) is the classic wall for reading Permian geology. This project traces how that wall has been mapped, named, argued over, and re-measured — geologic time first, then human research time.

## Status

Seed Brushy / Guads research events are in `data/events.csv`. Static HTML mock builds to `docs/`.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python src/build_html.py
python -m http.server 8765 --directory docs   # then open http://127.0.0.1:8765
```

## Edit the timeline

1. Add or revise rows in [`data/events.csv`](data/events.csv).
2. Keep **theme** tags in `branches` consistent with [`data/branches.yaml`](data/branches.yaml).
3. Keep **formation** tags in `formations` consistent with [`data/formations.yaml`](data/formations.yaml) (optional; blank = Guads-wide).
4. Drop images in `assets/images/` and credit them in [`assets/images/CREDITS.md`](assets/images/CREDITS.md).
5. See [`src/schema.md`](src/schema.md) for column definitions.

## Outputs (planned)

| Output | Path | Notes |
|---|---|---|
| Website | `docs/` → GitHub Pages | Sectioned timeline + branch / formation filters |
| PDF | browser print / `exports/` | Print CSS first |
| PowerPoint | `exports/timeline.pptx` | Key events (`importance` filter) |

## Later option: interactive TimelineJS

The current mock is a vertical scroll. For a clickable axis + pop-up slides (Knight Lab style), a later renderer can export `events.csv` to [TimelineJS](https://timeline.knightlab.com) JSON and embed it on GitHub Pages. That keeps CSV as source of truth while matching tools like TimelineJS (or visual references such as [Time.graphics](https://time.graphics/line/487)). Not built yet — dual filter (branch + formation) and PPT/PDF still favor owning our own data + multiple renderers.

## License

- **Code:** MIT ([`LICENSE`](LICENSE))
- **Timeline content:** CC BY 4.0 (see README note in releases; attribute *The West Face* / Zane Jobe)
- **Images:** per-file rights in `assets/images/CREDITS.md` — do not assume public domain
