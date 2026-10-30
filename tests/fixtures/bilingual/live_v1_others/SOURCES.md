# Live V1 others harvest (es/pl/sv/uk · 2026-10-30)

Time-boxed samples from [hosted.weblate.org](https://hosted.weblate.org) public
`/api/units/` for languages beyond the earlier EN/DE/RU dogfood. Help-style EN
pages wrap live source/target leftover spans; surrounding prose is fixture glue.

| Fixture | Upstream | Locales with leftover |
|---|---|---|
| `soapbox-onboarding` | soapbox-pub/soapbox ES `Onboarding complete` | es |
| `dicio-toast` | dicio-android/strings Toast | es, pl, sv, uk |
| `taiga-dashboard` | taiga/taiga-front Dashboard | es, pl |
| `soapbox-dashboard` | soapbox-pub/soapbox Dashboard | sv, uk |
| `muos-toast-animation` | muos/mux UK identical EN appearance string | uk |
| `godot-toast` | godot-engine properties Toast Notifications | es, pl, sv |

Refresh:

```bash
uv run python scripts/fetch_weblate_leftover_sample.py --out /tmp/lexaudit-live-units.json
# plus es/pl/sv/uk queries (see script DEFAULT_QUERIES after 2026-10-30)
```

Jellyfin/Immich GitHub mirrors for es/pl/sv/uk mostly **translate** Dashboard/Download
(e.g. ES `Panel de control` / `Descargar`), so they are weak leftover sources for this pass.
