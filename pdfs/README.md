# PDFs (local only)

Personal copies of papers and theses for events in `data/events.csv`. **Not committed** — see root `.gitignore`.

## Naming

```text
{year}-{author}-{short-title}.pdf
```

- `year` — publication year (4 digits)
- `author` — first author surname, lowercase (use `etal` only in the short title if needed)
- `short-title` — kebab-case, ~3–6 words

Examples:

- `1948-king-geology-southern-guadalupe-mountains.pdf`
- `1998-johnson-brushy-outcrop-cabin-lake.pdf`
- `2003-gardner-process-response-submarine-channels.pdf`

## Sources

- Zotero: copy from `~/Zotero/storage/`
- Mines theses: [repository.mines.edu](https://repository.mines.edu) / handles in `citations`
- USGS reports: pubs.usgs.gov (public domain)

`has_pdf` in `data/events.csv` is `yes`/`no` based on whether a matching file exists here (matched by event year + first-author surname in the filename, or an explicit map in `scripts/sync_pdfs.py` if present).
