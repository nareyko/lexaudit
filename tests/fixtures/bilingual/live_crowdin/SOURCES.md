# Crowdin-synced leftover sample (via public GitHub mirrors · 2026-10-30)

Crowdin REST API requires a token (401 unauthenticated). This pass samples
**Crowdin-synced locale trees published on GitHub** instead.

| Fixture | Upstream mirror | Crowdin note |
|---|---|---|
| `jellyfin-dashboard` / `jellyfin-download` | [jellyfin/jellyfin-web](https://github.com/jellyfin/jellyfin-web) `src/strings/{en-us,ru,de}.json` | Jellyfin uses Crowdin; DE keeps `Dashboard` / `Download` |
| `immich-transfer` | [immich-app/immich](https://github.com/immich-app/immich) `i18n/{en,ru,de}.json` | Immich uses Crowdin; DE keeps `Download` / `Upload` |

Help-style EN pages wrap live source strings; RU/DE body text is fixture glue
plus the cited loan/leftover spans.

Refresh without Crowdin token: re-download the JSON mirrors and re-curate.
Authenticated Crowdin `/api/v2` export remains optional for the owner.
