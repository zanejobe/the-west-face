# Event table schema

One row = one timeline event.

Multi-select tags use **semicolon-separated** ids (no spaces around `;` preferred: `mapping;sedimentology`).

| Column | Required | Description |
|---|---|---|
| `id` | yes | Stable slug (`king-1948-guadalupe`) |
| `timescale` | yes | `geologic` or `human` |
| `date_start` | yes | ISO year (`1948`) or geologic age (`272 Ma`) |
| `date_end` | no | End of interval; blank if instantaneous / unknown |
| `era` | yes | Section key matching `data/eras.yaml` |
| `title` | yes | Short display title |
| `summary` | yes | 1–3 sentences |
| `people` | no | Semicolon-separated names |
| `orgs` | no | Semicolon-separated organizations |
| `citations` | no | Short cite, DOI, or URL |
| `branches` | yes | Thematic tags from `data/branches.yaml` |
| `branch_primary` | no | One branch for default lane color when multi-tagged |
| `formations` | no | Formation tags from `data/formations.yaml`; blank = Guads-wide / not unit-specific |
| `importance` | yes | `1` full only; `2` web; `3` poster + PPT highlight |
| `image` | no | Filename under `assets/images/` (`{year}-{slug}.ext`) |
| `image_credit` | no | Credit / rights string |

## Eras vs branches vs formations

These are **three independent filters**:

| Field | What it answers | Example |
|---|---|---|
| **eras** | *When* in the story? | `usgs_mapping` |
| **branches** | *What kind of research?* | `mapping;stratigraphy` |
| **formations** | *Which rock unit(s)?* | `brushy_canyon;cherry_canyon` |

Do **not** put formation names in `branches`. Use `basin_fill` / `reef_and_shelf` for the *style* of geology, and `formations` for the lithostratigraphic filter (e.g. Brushy Canyon only).

Example: a paper on Brushy Canyon turbidites might be:

- `branches`: `sedimentology;basin_fill`
- `branch_primary`: `sedimentology`
- `formations`: `brushy_canyon`
