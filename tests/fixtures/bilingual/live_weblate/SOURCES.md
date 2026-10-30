# Live Weblate leftover sample (time-boxed · 2026-10-30)

Help-style EN pages wrap **live** source/target strings sampled from
[hosted.weblate.org](https://hosted.weblate.org) public API (`/api/units/`).
Surrounding Russian/German prose is original fixture glue, not upstream UI chrome.

| Fixture | Upstream unit (checksum URL) | Note |
|---|---|---|
| `soapbox-onboarding` | [soapbox-pub/soapbox ru](https://hosted.weblate.org/translate/soapbox-pub/soapbox/ru/?checksum=0f75f859e43deb99) | identical `Onboarding complete` |
| `soapbox-inbox` | [soapbox-pub/soapbox ru](https://hosted.weblate.org/translate/soapbox-pub/soapbox/ru/?checksum=7a21bc3fc53bdd3c) | identical EN confirmation paragraph |
| `dicio-toast` | [dicio-android/strings ru](https://hosted.weblate.org/translate/dicio-android/strings/ru/?checksum=87a94b7ce54b3b74) | `Toast (…) ` kept |
| `muos-toast-animation` | [muos/mux ru](https://hosted.weblate.org/translate/muos/mux/ru/?checksum=32b25b8aec71fd9f) | identical EN appearance string |
| `goosemod-toast` | [goosemod de](https://hosted.weblate.org/translate/goosemod/goosemod/de/?checksum=56c52f99999dac20) | DE keeps Toast/Store loans |
| `galette-dashboard` | [galette de](https://hosted.weblate.org/translate/galette/galette/de/?checksum=feb3bc79ed725161) (+ RU imperfect wrap) | DE Dashboard loan |
| `navigate-marketplace` | [navigate-cms ru](https://hosted.weblate.org/translate/navigate-cms/translations/ru/?checksum=16a3fb74b21343fb) | identical EN marketplace sentence |

Refresh (optional):

```bash
# requires network; throttled without Weblate token
uv run python scripts/fetch_weblate_leftover_sample.py --out /tmp/live-units.json
```

Crowdin: no authenticated public bulk sample in this pass — deferred.
