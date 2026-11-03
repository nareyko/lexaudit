# Real benchmark (v0.4 Stage V2)

Generated: `2026-11-03T20:34:14Z`

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
| en | 12 | 1051 | 3 | 2.854 |
| de | 12 | 831 | 3 | 3.610 |
| es | 12 | 424 | 0 | 0.000 |
| pl | 12 | 297 | 0 | 0.000 |
| ru | 12 | 818 | 3 | 3.667 |
| sv | 12 | 314 | 5 | 15.924 |
| uk | 12 | 343 | 3 | 8.746 |

## Notes

- Clean fixtures mix FairHelm CC0 originals, in-repo MIT/CC-BY real_public
  excerpts, and Wikipedia CC-BY-SA summaries when the network allows.
- Raw downloads live under `tmp/` (gitignored); git keeps stratified slices.
- See `docs/real-benchmark.md` for annotator agreement (Cohen κ).
