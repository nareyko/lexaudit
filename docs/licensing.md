# Licensing (crystal-clear)

## What GitHub / PyPI distribute today

The **published package** (`pip install lexaudit`, this repository’s default
`LICENSE` file, and `pyproject.toml` `license = "MIT"`) is **MIT**.

Under MIT you may use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the software, including in proprietary products and
private SaaS, **without** opening your own application source — provided you
keep the MIT copyright notice.

## What the AGPL file is (and is not)

| File | Applies to |
|---|---|
| [`LICENSE`](../LICENSE) | **Everything in this repo that is our code**: CLI, library, YAML rules, packs, docs we wrote. |
| [`LICENSE-AGPL-HOSTED.md`](../LICENSE-AGPL-HOSTED.md) | **Policy intent** for a future **multi-tenant hosted SaaS** that exposes lexaudit (or a fork) as a network service to third parties. It is **not** a second license on the MIT PyPI wheel. This repository does **not** currently ship that hosted service. |
| [`LICENSE-THIRD-PARTY.md`](../LICENSE-THIRD-PARTY.md) | Third-party **corpora / dictionaries** used in benchmarks and `fetch-dicts`. Their upstream licenses are unchanged. |

There is **no** “MIT + AGPL dual license on the same PyPI artifact.” The artifact
is MIT. The AGPL document records the author’s intent if/when a hosted network
service is published under a separate distribution.

## Third-party assets

| Asset | License handling |
|---|---|
| Hunspell / LibreOffice dictionaries via `lexaudit fetch-dicts` | Upstream licenses next to each dict (`*.license.txt`); not relicensed |
| Real-bench fixtures (`tests/fixtures/real_bench/`) | See `LICENSE-THIRD-PARTY.md` + `eval/corpora/manifest.json` |
| Marine / yacht domain dictionaries | Not shipped in the public package |

## Where this is restated

- Root [`README.md`](../README.md) license table
- [`LICENSE-THIRD-PARTY.md`](../LICENSE-THIRD-PARTY.md)
- Changelog release notes for `0.4.0`
