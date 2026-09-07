#!/usr/bin/env python3
"""Populate pdfs/ from Zotero + Mines CoRE + public USGS URLs; set has_pdf on events.csv."""

from __future__ import annotations

import csv
import json
import re
import shutil
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDFS = ROOT / "pdfs"
CSV_PATH = ROOT / "data" / "events.csv"
ZOTERO_STORAGE = Path.home() / "Zotero" / "storage"
UA = {"User-Agent": "the-west-face-pdf-sync/1.0 (research; local archive)"}

# event_id -> (filename, source)
# source: zotero:<KEY> | mines:<handle> | url:<https...> | path:</abs/or/~/file.pdf>
EVENT_PDFS: dict[str, tuple[str, str]] = {
    "bartlett-1854-personal-narrative": (
        "1854-bartlett-personal-narrative.pdf",
        "url:https://archive.org/download/personalnarrativ01bart/personalnarrativ01bart.pdf",
    ),
    "shumard-1858-permian-fossils": (
        "1858-shumard-permian-fossils.pdf",
        "path:~/Downloads/mobot31753002105986.pdf",
    ),
    "richardson-1904-delaware-mountain": (
        "1904-richardson-delaware-mountain.pdf",
        "url:https://repositories.lib.utexas.edu/bitstream/handle/2152/24408/2013-X-0008-RascoeElder.pdf?sequence=1&isAllowed=y",
    ),
    "girty-1908-pp58": (
        "1908-girty-guadalupian-fauna.pdf",
        "path:~/Downloads/report.pdf",
    ),
    "king-1942-dmg-names": (
        "1942-king-dmg-names.pdf",
        "path:~/Downloads/aapg_1942_0026_0004_0535.pdf",
    ),
    "king-1948-pp215": (
        "1948-king-geology-southern-guadalupe-mountains.pdf",
        "url:https://pubs.usgs.gov/pp/0215/report.pdf",
    ),
    "hayes-1964-pp446": (
        "1964-hayes-geology-guadalupe-mountains-nm.pdf",
        "url:https://pubs.usgs.gov/pp/0446/report.pdf",
    ),
    "harms-1974-brushy-density": (
        "1974-harms-brushy-canyon-density-current.pdf",
        "zotero:SFD5AE23",
    ),
    "rossen-sarg-1987-aapg-abstract": (
        "1987-rossen-sarg-brushy-siliciclastic-wedge.pdf",
        "zotero:8G3AVUEE",
    ),
    "harms-williamson-1988-dmg": (
        "1988-harms-williamson-delaware-mountain-density.pdf",
        "zotero:XSGLAPXH",
    ),
    "gardner-1992-wtgs-dmg-turbidites": (
        "1992-gardner-eolian-derived-dmg-turbidites.pdf",
        "zotero:GKRHQYZY",
    ),
    "doe-nash-draw-1995-brushy-class-iii": (
        "1995-martin-nash-draw-brushy-class-iii.pdf",
        "zotero:GW6L8DP3",
    ),
    "zelt-rossen-1995-atlas": (
        "1995-zelt-rossen-brushy-deep-water-atlas.pdf",
        "zotero:VEHSJI7I",
    ),
    "gardner-sonnenfeld-1996-pbs-sepm": (
        "1996-gardner-sonnenfeld-brushy-play-guidebook.pdf",
        "zotero:7BR34ENP",
    ),
    # DOE Class III Geraldine Ford topical (1997) — open OSTI substitute for paywalled BEG RI 255
    "dutton-etal-1999-geraldine-ford-beg-ri255": (
        "1997-dutton-geraldine-ford-doe-topical.pdf",
        "url:https://www.osti.gov/servlets/purl/595625.pdf",
    ),
    "sageman-etal-1998-geology-brushy-org": (
        "1998-sageman-brushy-organic-siltstone-hierarchy.pdf",
        "zotero:C8IXX4JT",
    ),
    "mines-johnson-1998-ms": (
        "1998-johnson-brushy-outcrop-cabin-lake.pdf",
        "mines:11124/15090",
    ),
    "beaubouef-1999-aapg-cn40": (
        "1999-beaubouef-brushy-deep-water-sandstones.pdf",
        "zotero:2GLI2272",
    ),
    "mines-kullman-1999-ms": (
        "1999-kullman-brushy-fracture-networks.pdf",
        "mines:11124/15198",
    ),
    "batzle-gardner-2000-memoir72-seismic": (
        "2000-batzle-gardner-brushy-seismic-lithology.pdf",
        "zotero:Z8IWRYDB",
    ),
    "carr-gardner-2000-memoir72": (
        "2000-carr-gardner-lower-brushy-basin-floor-fan.pdf",
        "zotero:RXNJUUNX",
    ),
    "gardner-borer-2000-memoir72": (
        "2000-gardner-borer-brushy-slope-basin-channels.pdf",
        "zotero:ITLYWKYY",
    ),
    "mines-wagerle-2001-ms": (
        "2001-wagerle-middle-brushy-architecture.pdf",
        "mines:11124/15294",
    ),
    "mines-melick-2002-ms": (
        "2002-melick-upper-brushy-facies-architecture.pdf",
        "mines:11124/15316",
    ),
    "gardner-etal-2003-mpg": (
        "2003-gardner-process-response-submarine-channels.pdf",
        "zotero:J35TWT52",
    ),
    "mines-romans-2003-ms": (
        "2003-romans-cutoff-brushy-cherry-basinal-cycle.pdf",
        "mines:11124/15694",
    ),
    "mines-baptista-2004-ms": (
        "2004-baptista-brushy-basin-wide-framework.pdf",
        "mines:11124/16747",
    ),
    "bohacs-etal-2005-source-rock-paths": (
        "2005-bohacs-source-rock-paths.pdf",
        "zotero:ZH36FTQS",
    ),
    "mines-borer-2005-phd": (
        "2005-borer-middle-brushy-channel-modeling.pdf",
        "mines:11124/177744",
    ),
    "mines-kling-2006-phd": (
        "2006-kling-brushy-starved-margin.pdf",
        "mines:11124/177784",
    ),
    "mines-hanggoro-2007-ms": (
        "2007-hanggoro-lower-brushy-slope-channels.pdf",
        "mines:11124/15998",
    ),
    "mines-atan-2007-phd": (
        "2007-atan-multiscale-flow-heterogeneous-reservoirs.pdf",
        "mines:11124/79180",
    ),
    "gardner-etal-2008-gcssepm-strat-models": (
        "2008-gardner-gcssepm-strat-models.pdf",
        "zotero:LUXSVAZS",
    ),
    "mines-amerman-2009-phd": (
        "2009-amerman-deepwater-mass-transport-deposits.pdf",
        "mines:11124/79179",
    ),
    "pyles-etal-2010-beacon-channel-jsr": (
        "2010-pyles-beacon-channel-sinuous-slope.pdf",
        "zotero:3WYU2EBX",
    ),
    "amerman-etal-2011-sepm-cutoff-mtd": (
        "2011-amerman-sepm-cutoff-mtd.pdf",
        "zotero:F7J65DML",
    ),
    "no-2021-brushy-pay-zone-ksmer": (
        "2021-no-brushy-pay-zone.pdf",
        "zotero:T4AZHY8S",
    ),
}


def http_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={**UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as resp, tmp.open("wb") as out:
        shutil.copyfileobj(resp, out)
    tmp.replace(dest)


def zotero_pdf_path(key: str) -> Path:
    folder = ZOTERO_STORAGE / key
    if not folder.is_dir():
        raise FileNotFoundError(f"Zotero storage missing: {folder}")
    pdfs = sorted(folder.glob("*.pdf")) + sorted(folder.glob("*.PDF"))
    if not pdfs:
        raise FileNotFoundError(f"No PDF in {folder}")
    return pdfs[0]


def mines_pdf_url(handle: str) -> str:
    pid = http_json(
        "https://repository.mines.edu/server/api/pid/find?id="
        + urllib.parse.quote(f"http://hdl.handle.net/{handle}")
    )
    uuid = pid["uuid"]
    bundles = http_json(
        f"https://repository.mines.edu/server/api/core/items/{uuid}/bundles"
    )
    for bundle in bundles.get("_embedded", {}).get("bundles", []):
        if bundle.get("name") != "ORIGINAL":
            continue
        bid = bundle["uuid"]
        bits = http_json(
            f"https://repository.mines.edu/server/api/core/bundles/{bid}/bitstreams"
        )
        for bs in bits.get("_embedded", {}).get("bitstreams", []):
            name = (bs.get("name") or "").lower()
            mime = (bs.get("format") or "")
            if name.endswith(".pdf") or "pdf" in str(mime).lower():
                return f"https://repository.mines.edu/bitstreams/{bs['uuid']}/download"
    raise FileNotFoundError(f"No PDF bitstream for mines:{handle}")


def ensure_pdf(event_id: str, filename: str, source: str) -> bool:
    dest = PDFS / filename
    if dest.is_file() and dest.stat().st_size > 1000:
        print(f"  exists {filename}")
        return True
    try:
        if source.startswith("zotero:"):
            src = zotero_pdf_path(source.split(":", 1)[1])
            print(f"  copy {src.name} -> {filename}")
            shutil.copy2(src, dest)
        elif source.startswith("path:"):
            src = Path(source[5:]).expanduser()
            if not src.is_file():
                raise FileNotFoundError(f"Local path missing: {src}")
            print(f"  path {src} -> {filename}")
            shutil.copy2(src, dest)
        elif source.startswith("mines:"):
            handle = source.split(":", 1)[1]
            url = mines_pdf_url(handle)
            print(f"  mines {handle} -> {filename}")
            download(url, dest)
        elif source.startswith("url:"):
            url = source[4:]
            print(f"  url -> {filename}")
            download(url, dest)
        else:
            raise ValueError(f"Unknown source {source}")
        return dest.is_file() and dest.stat().st_size > 1000
    except Exception as exc:  # noqa: BLE001 — report per-event failures
        print(f"  FAIL {event_id}: {exc}")
        if dest.exists():
            dest.unlink()
        return False


def update_csv(present: dict[str, bool]) -> tuple[int, int]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)

    if "has_pdf" not in fieldnames:
        # Place after image_credit if present, else append.
        if "image_credit" in fieldnames:
            i = fieldnames.index("image_credit") + 1
            fieldnames.insert(i, "has_pdf")
        else:
            fieldnames.append("has_pdf")

    yes = no = 0
    for row in rows:
        eid = row["id"]
        filename = EVENT_PDFS.get(eid, (None, None))[0]
        ok = bool(filename and (PDFS / filename).is_file())
        # Also accept any already-present file if mapped and present dict says so
        if eid in present:
            ok = present[eid]
        row["has_pdf"] = "yes" if ok else "no"
        if ok:
            yes += 1
        else:
            no += 1

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return yes, no


def main() -> None:
    PDFS.mkdir(parents=True, exist_ok=True)
    present: dict[str, bool] = {}
    print(f"Syncing {len(EVENT_PDFS)} mapped events into {PDFS}")
    for event_id, (filename, source) in EVENT_PDFS.items():
        print(event_id)
        present[event_id] = ensure_pdf(event_id, filename, source)

    yes, no = update_csv(present)
    print(f"has_pdf: {yes} yes / {no} no")


if __name__ == "__main__":
    main()
