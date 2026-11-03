# Real benchmark (v0.4 Stage V2)

Generated: `2026-11-03T19:04:03Z`

## Fixture counts

| Locale | clean | gec pairs | mt pages |
|---|---:|---:|---:|
| en | 12 | 6 | 6 |
| de | 12 | 6 | 6 |
| es | 12 | 6 | 6 |
| pl | 12 | 6 | 6 |
| ru | 12 | 6 | 6 |
| sv | 12 | 6 | 6 |
| uk | 12 | 24 | 5 |

## Clean page FPR

| Locale | pages | tokens | FP unique words | FP / 1000 tokens |
|---|---:|---:|---:|---:|
| en | 12 | 1051 | 9 | 8.563 |
| de | 12 | 831 | 3 | 3.610 |
| es | 12 | 424 | 18 | 42.453 |
| pl | 12 | 297 | 4 | 13.468 |
| ru | 12 | 818 | 35 | 42.787 |
| sv | 12 | 314 | 5 | 15.924 |
| uk | 12 | 343 | 12 | 34.985 |

## Notes

- Clean fixtures mix FairHelm CC0 originals, in-repo MIT/CC-BY real_public
  excerpts, and Wikipedia CC-BY-SA summaries when the network allows.
- Raw downloads live under `tmp/` (gitignored); git keeps stratified slices.
- See `docs/real-benchmark.md` for annotator agreement (Cohen κ).
