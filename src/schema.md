# Event table schema

One row = one timeline event. Multi-branch events use semicolon-separated tags in `branches`.

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
| `branches` | yes | Semicolon-separated tags from `data/branches.yaml` |
| `branch_primary` | no | One branch for default lane color when multi-tagged |
| `importance` | yes | `1` full only; `2` web; `3` poster + PPT highlight |
| `image` | no | Path under `assets/images/` |
| `image_credit` | no | Credit / rights string |

## Branches vs eras

- **eras** — chronological sections (deep time → research periods).
- **branches** — thematic lanes / filters (mapping, sedimentology, petroleum, …). An event can have many branches; it belongs to one era.
