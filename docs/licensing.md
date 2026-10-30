# Dual license (MIT + AGPL for hosted) — lexaudit only

This dual license applies to the **lexaudit** package repository
(`github.com/nareyko/lexaudit`), not to FairHelm.

| Product | License |
|---|---|
| **lexaudit** (this repo) | Dual — see table below |
| **FairHelm** (fairhelm.com / host monorepo) | **Proprietary** — not MIT, not AGPL, not dual-licensed |

| Use of **lexaudit** | License | Text |
|---|---|---|
| CLI, Python library, rule YAML, packs from this repo (local / CI / embed in *your* product) | **MIT** | [`LICENSE`](../LICENSE) |
| **Hosted** multi-tenant SaaS that exposes lexaudit (or a fork) as a **network service** to third parties | **AGPL-3.0-or-later** | [`LICENSE-AGPL-HOSTED.md`](../LICENSE-AGPL-HOSTED.md) |
| Spelling dictionaries from `lexaudit fetch-dicts` | **Upstream** (unchanged) | `*.license.txt` next to each dict |

## Plain words

- **You run lexaudit on your laptop or in your own CI** → MIT. Fork, ship, sell, keep private — fine under MIT.
- **You offer lexaudit as a hosted service that other people’s browsers/API clients talk to** → that hosted service code is intended under AGPL-3.0-or-later (network copyleft: users of the service get source rights).
- This repository **does not currently ship** a hosted service. The AGPL file is the license text for that intended use, not a second license on the MIT package itself.
- Packs (`packs/*`, `packs/_lab/*`) stay **MIT**, same as the library.
- Embedding lexaudit (MIT) inside a proprietary product such as FairHelm does **not** open-source FairHelm.

## What is *not* dual-licensed

| Asset | Note |
|---|---|
| FairHelm site, courses, content, dictionaries, bridge configs | **Proprietary** (host product) |
| Marine / yacht FairHelm dictionaries | Stay outside this public package |
| Hunspell / system dictionaries | Keep their own licenses; lexaudit does not relicense them |

## Where else it is stated

- Root [`README.md`](../README.md) · [`docs/README.md`](README.md) · [`CONTRIBUTING.md`](../CONTRIBUTING.md)
- Package metadata: `pyproject.toml` → MIT (the published artifact)
- Changelog: MIT package; hosted AGPL note points here
