# Dual license (MIT + AGPL for hosted)

lexaudit uses a **dual license**, depending on *how* you use the software.

| Use | License | Text |
|---|---|---|
| CLI, Python library, rule YAML, packs from this repo (local / CI / embed in your product) | **MIT** | [`LICENSE`](../LICENSE) |
| **Hosted** multi-tenant SaaS that exposes lexaudit (or a fork) as a **network service** to third parties | **AGPL-3.0-or-later** | [`LICENSE-AGPL-HOSTED.md`](../LICENSE-AGPL-HOSTED.md) |
| Spelling dictionaries from `lexaudit fetch-dicts` | **Upstream** (unchanged) | `*.license.txt` next to each dict |

## Plain words

- Laptop or own CI: MIT. Fork, ship, sell, keep private: fine under MIT.
- Hosted multi-tenant service that other people’s clients talk to: that hosted
  service code is intended under AGPL-3.0-or-later (network copyleft).
- This repository does not currently ship a hosted service. The AGPL file is the
  license text for that intended use, not a second license on the MIT package.
- Packs (`packs/*`, `packs/_lab/*`) stay MIT, same as the library.
- Embedding the MIT package inside another product does not change that product’s
  license.

## What is *not* dual-licensed here

| Asset | Note |
|---|---|
| Marine / yacht domain dictionaries and content | Hard rule: not shipped in the public package |
| Hunspell / system dictionaries | Keep their own licenses; lexaudit does not relicense them |

## Where else it is stated

- Root [`README.md`](../README.md), [`docs/README.md`](README.md), [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- Package metadata: `pyproject.toml` → MIT (the published artifact)
- Changelog: MIT package; hosted AGPL note points here
