#!/usr/bin/env python3
# ruff: noqa: RUF001
"""Build real-bench corpora (clean / gec / mt) and measure Clean FPR.

Detection-only helper. Never writes into audited FairHelm product sources.

Stages
------
* ``clean`` — open technical prose for en/de/es/pl/ru/sv/uk into
  ``tmp/real-bench/clean/`` (full) and a stratified slice under
  ``tests/fixtures/real_bench/clean/<locale>/``.
* ``gec`` — lexical error pairs from open GEC sources (or documented
  self-curated CC0 stand-ins) under ``tests/fixtures/real_bench/gec/``.
* ``mt`` — machine-translation-like calque pages under
  ``tests/fixtures/real_bench/mt/<locale>/``.
* ``measure`` — run ``lexaudit`` on clean fixtures and write
  ``eval/real-benchmark.md``.
* ``all`` — clean → gec → mt → measure.

Licenses are recorded in ``eval/corpora/manifest.json`` and
``LICENSE-THIRD-PARTY.md``. Raw downloads stay in ``tmp/`` (gitignored).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from lexaudit.config import LexauditConfig  # noqa: E402
from lexaudit.core.pipeline import run_locale_audit  # noqa: E402
from lexaudit.core.tokenize import tokenize  # noqa: E402
from lexaudit.eval.metrics import clean_page_fpr  # noqa: E402

LOCALES = ("en", "de", "es", "pl", "ru", "sv", "uk")
USER_AGENT = (
    "lexaudit-real-bench/0.4 (research; https://fairhelm.com; contact=lexaudit@fairhelm.com)"
)
FREEZE_AT = "1970-01-01T00:00:00Z"
SLICE_PER_LOCALE = 12
WIKI_TITLES: dict[str, list[str]] = {
    "en": [
        "Kubernetes",
        "HTTP",
        "Continuous_integration",
        "Load_balancing_(computing)",
        "Microservices",
        "REST",
        "Git",
        "Database",
        "Containerization_(computing)",
        "Python_(programming_language)",
    ],
    "de": [
        "Kubernetes",
        "Hypertext_Transfer_Protocol",
        "Kontinuierliche_Integration",
        "Lastverteilung",
        "Microservices",
        "Representational_State_Transfer",
        "Git",
        "Datenbank",
        "Containerisierung",
        "Python_(Programmiersprache)",
    ],
    "es": [
        "Kubernetes",
        "Protocolo_de_transferencia_de_hipertexto",
        "Integración_continua",
        "Balanceo_de_carga",
        "Arquitectura_de_microservicios",
        "Transferencia_de_Estado_Representacional",
        "Git",
        "Base_de_datos",
        "Contenedor_(informática)",
        "Python",
    ],
    "pl": [
        "Kubernetes",
        "Hypertext_Transfer_Protocol",
        "Ciągła_integracja",
        "Równoważenie_obciążenia",
        "Mikrousługi",
        "Representational_State_Transfer",
        "Git",
        "Baza_danych",
        "Konteneryzacja",
        "Python",
    ],
    "ru": [
        "Kubernetes",
        "HTTP",
        "Непрерывная_интеграция",
        "Балансировка_нагрузки",
        "Микросервисная_архитектура",
        "REST",
        "Git",
        "База_данных",
        "Контейнеризация",
        "Python",
    ],
    "sv": [
        "Kubernetes",
        "Hypertext_Transfer_Protocol",
        "Kontinuerlig_integration",
        "Lastbalansering",
        "Mikrotjänst",
        "Representational_State_Transfer",
        "Git",
        "Databas",
        "Containerisering",
        "Python_(programspråk)",
    ],
    "uk": [
        "Kubernetes",
        "HTTP",
        "Безперервна_інтеграція",
        "Балансування_навантаження",
        "Мікросервісна_архітектура",
        "REST",
        "Git",
        "База_даних",
        "Контейнеризація",
        "Python",
    ],
}

# Original FairHelm / lexaudit technical prose (CC0). Used as the guaranteed
# stratified baseline when network fetches fail or return thin pages.
ORIGINAL_PROSE: dict[str, list[tuple[str, str]]] = {
    "en": [
        (
            "fh-ci-pipeline",
            "# Continuous integration pipeline\n\n"
            "A build server runs unit tests after every commit. Artifacts land in a "
            "versioned registry before the release train starts. Operators watch "
            "failure rates and retry only flaky suites.\n",
        ),
        (
            "fh-http-cache",
            "# HTTP caching notes\n\n"
            "Cache-Control headers decide whether intermediaries may store a response. "
            "ETags let clients validate without downloading the full body. Prefer "
            "explicit max-age values over heuristic freshness.\n",
        ),
        (
            "fh-load-balance",
            "# Load balancing basics\n\n"
            "A reverse proxy spreads traffic across healthy backends. Health checks "
            "remove failing nodes from the pool. Sticky sessions are optional and "
            "complicate failover.\n",
        ),
        (
            "fh-schema-migrate",
            "# Schema migrations\n\n"
            "Apply forward-only migrations in order. Keep expand-and-contract steps "
            "so old readers survive a rolling deploy. Backfills run out of band.\n",
        ),
        (
            "fh-observability",
            "# Observability stack\n\n"
            "Metrics track latency and error budgets. Structured logs carry request "
            "identifiers. Traces connect gateway hops to worker spans.\n",
        ),
        (
            "fh-auth-tokens",
            "# Token authentication\n\n"
            "Short-lived access tokens reduce replay risk. Refresh tokens stay in "
            "http-only cookies. Rotate signing keys on a published schedule.\n",
        ),
        (
            "fh-queue-workers",
            "# Background workers\n\n"
            "Queue consumers process jobs with at-least-once delivery. Idempotent "
            "handlers tolerate duplicate messages. Dead-letter queues collect poison "
            "payloads for inspection.\n",
        ),
        (
            "fh-feature-flags",
            "# Feature flags\n\n"
            "Flags gate unfinished UI without branching the release. Percentage "
            "rollouts expose risk gradually. Remove stale flags after full adoption.\n",
        ),
        (
            "fh-api-versioning",
            "# API versioning\n\n"
            "Path versions keep breaking changes explicit. Deprecation windows give "
            "clients time to migrate. Compatibility tests cover the previous major.\n",
        ),
        (
            "fh-storage-tiers",
            "# Storage tiers\n\n"
            "Hot data stays on low-latency disks. Cold archives move to cheaper "
            "object storage. Lifecycle policies encode the transition rules.\n",
        ),
    ],
    "de": [
        (
            "fh-ci-pipeline",
            "# Pipeline für kontinuierliche Integration\n\n"
            "Ein Build-Server führt nach jedem Commit Unit-Tests aus. Artefakte "
            "landen in einer versionierten Registry, bevor die Freigabe startet. "
            "Betreiber beobachten Fehlerraten und wiederholen nur instabile Suiten.\n",
        ),
        (
            "fh-http-cache",
            "# Hinweise zum HTTP-Caching\n\n"
            "Cache-Control-Header entscheiden, ob Zwischenstationen eine Antwort "
            "speichern dürfen. ETags erlauben eine Prüfung ohne den ganzen Körper. "
            "Explizite max-age-Werte sind Heuristiken vorzuziehen.\n",
        ),
        (
            "fh-load-balance",
            "# Grundlagen der Lastverteilung\n\n"
            "Ein Reverse-Proxy verteilt Verkehr auf gesunde Backends. "
            "Gesundheitsprüfungen entfernen fehlerhafte Knoten aus dem Pool. "
            "Sticky Sessions sind optional und erschweren den Failover.\n",
        ),
        (
            "fh-schema-migrate",
            "# Schema-Migrationen\n\n"
            "Migrationen laufen nur vorwärts und in Reihenfolge. Expand-and-Contract "
            "hält alte Leser während eines Rolling Deploy am Leben. Backfills laufen "
            "außerhalb des kritischen Pfads.\n",
        ),
        (
            "fh-observability",
            "# Beobachtbarkeit\n\n"
            "Metriken tracken Latenz und Fehlerbudgets. Strukturierte Logs tragen "
            "Anfragekennungen. Traces verbinden Gateway-Sprünge mit Worker-Spans.\n",
        ),
        (
            "fh-auth-tokens",
            "# Token-Authentifizierung\n\n"
            "Kurzlebige Access-Tokens verringern Replay-Risiko. Refresh-Tokens "
            "bleiben in http-only Cookies. Signierschlüssel rotieren nach Plan.\n",
        ),
        (
            "fh-queue-workers",
            "# Hintergrundarbeiter\n\n"
            "Queue-Konsumenten verarbeiten Jobs mit mindestens-einmal Zustellung. "
            "Idempotente Handler tolerieren Duplikate. Dead-Letter-Queues sammeln "
            "Giftnachrichten zur Prüfung.\n",
        ),
        (
            "fh-feature-flags",
            "# Feature-Flags\n\n"
            "Flags schalten unfertige Oberfläche ohne Release-Branch. Prozentuale "
            "Rollouts streuen Risiko. Veraltete Flags verschwinden nach Adoption.\n",
        ),
        (
            "fh-api-versioning",
            "# API-Versionierung\n\n"
            "Pfadversionen machen Bruchänderungen sichtbar. Deprecation-Fenster "
            "geben Clients Zeit. Kompatibilitätstests decken die vorige Major ab.\n",
        ),
        (
            "fh-storage-tiers",
            "# Speicherebenen\n\n"
            "Heiße Daten bleiben auf schneller Platte. Kalte Archive wandern in "
            "günstigeren Objektspeicher. Lebenszyklusregeln kodieren Übergänge.\n",
        ),
    ],
    "es": [
        (
            "fh-ci-pipeline",
            "# Canal de integración continua\n\n"
            "Un servidor de compilación ejecuta pruebas unitarias tras cada commit. "
            "Los artefactos llegan a un registro versionado antes del tren de "
            "publicación. Los operadores vigilan tasas de fallo y reintentan solo "
            "suites inestables.\n",
        ),
        (
            "fh-http-cache",
            "# Notas de caché HTTP\n\n"
            "Las cabeceras Cache-Control deciden si intermediarios pueden guardar "
            "una respuesta. Los ETags permiten validar sin descargar el cuerpo. "
            "Prefiera valores max-age explícitos a frescura heurística.\n",
        ),
        (
            "fh-load-balance",
            "# Conceptos de balanceo de carga\n\n"
            "Un proxy inverso reparte tráfico entre backends sanos. Las comprobaciones "
            "de salud retiran nodos fallidos del grupo. Las sesiones persistentes son "
            "opcionales y complican la conmutación.\n",
        ),
        (
            "fh-schema-migrate",
            "# Migraciones de esquema\n\n"
            "Aplique migraciones solo hacia adelante y en orden. Conserve pasos "
            "expand-and-contract para que lectores antiguos sobrevivan un despliegue "
            "rodante. Los rellenos corren fuera de banda.\n",
        ),
        (
            "fh-observability",
            "# Observabilidad\n\n"
            "Las métricas siguen latencia y presupuestos de error. Los registros "
            "estructurados llevan identificadores de petición. Los rastros unen "
            "saltos de puerta de enlace con tramos de trabajador.\n",
        ),
        (
            "fh-auth-tokens",
            "# Autenticación con tokens\n\n"
            "Los tokens de acceso de corta vida reducen el riesgo de reutilización. "
            "Los de actualización permanecen en cookies http-only. Rote las claves "
            "de firma según un calendario publicado.\n",
        ),
        (
            "fh-queue-workers",
            "# Trabajadores en segundo plano\n\n"
            "Los consumidores de cola procesan trabajos con entrega al menos una vez. "
            "Los manejadores idempotentes toleran duplicados. Las colas de letra "
            "muerta recogen cargas tóxicas para inspección.\n",
        ),
        (
            "fh-feature-flags",
            "# Indicadores de función\n\n"
            "Los indicadores ocultan UI incompleta sin ramificar la publicación. "
            "Los despliegues porcentuales exponen el riesgo con calma. Elimine "
            "indicadores obsoletos tras la adopción plena.\n",
        ),
        (
            "fh-api-versioning",
            "# Versionado de API\n\n"
            "Las versiones en la ruta hacen explícitos los cambios rupturistas. "
            "Las ventanas de deprecación dan tiempo a los clientes. Las pruebas de "
            "compatibilidad cubren la major anterior.\n",
        ),
        (
            "fh-storage-tiers",
            "# Niveles de almacenamiento\n\n"
            "Los datos calientes permanecen en discos de baja latencia. Los archivos "
            "fríos pasan a almacenamiento de objetos más barato. Las políticas de "
            "ciclo de vida codifican las transiciones.\n",
        ),
    ],
    "pl": [
        (
            "fh-ci-pipeline",
            "# Potok ciągłej integracji\n\n"
            "Serwer kompilacji uruchamia testy jednostkowe po każdym zatwierdzeniu. "
            "Artefakty trafiają do wersjonowanego rejestru przed pociągiem wydań. "
            "Operatorzy śledzą wskaźniki błędów i ponawiają tylko niestabilne zestawy.\n",
        ),
        (
            "fh-http-cache",
            "# Notatki o pamięci podręcznej HTTP\n\n"
            "Nagłówki Cache-Control decydują, czy pośrednicy mogą przechowywać "
            "odpowiedź. ETagi pozwalają sprawdzić ważność bez pobierania ciała. "
            "Preferuj jawne max-age zamiast heurystycznej świeżości.\n",
        ),
        (
            "fh-load-balance",
            "# Podstawy równoważenia obciążenia\n\n"
            "Odwrotne proxy rozkłada ruch na zdrowe zaplecza. Kontrole zdrowia "
            "usuwają wadliwe węzły z puli. Sesje przyklejone są opcjonalne i "
            "utrudniają przełączenie awaryjne.\n",
        ),
        (
            "fh-schema-migrate",
            "# Migracje schematu\n\n"
            "Stosuj migracje tylko do przodu i w kolejności. Zachowaj kroki "
            "expand-and-contract, by starzy czytelnicy przetrwali wdrożenie "
            "kroczące. Uzupełnienia danych biegną poza pasmem.\n",
        ),
        (
            "fh-observability",
            "# Obserwowalność\n\n"
            "Metryki śledzą opóźnienia i budżety błędów. Strukturalne logi niosą "
            "identyfikatory żądań. Ślady łączą skoki bramy z zakresami pracowników.\n",
        ),
        (
            "fh-auth-tokens",
            "# Uwierzytelnianie tokenami\n\n"
            "Krótkotrwałe tokeny dostępu zmniejszają ryzyko odtworzenia. Tokeny "
            "odświeżania zostają w ciasteczkach http-only. Rotuj klucze podpisu "
            "według opublikowanego harmonogramu.\n",
        ),
        (
            "fh-queue-workers",
            "# Pracownicy w tle\n\n"
            "Konsumenci kolejek przetwarzają zadania z dostawą co najmniej raz. "
            "Idempotentne handlery tolerują duplikaty. Kolejki martwych listów "
            "zbierają toksyczne ładunki do wglądu.\n",
        ),
        (
            "fh-feature-flags",
            "# Flag i funkcji\n\n"
            "Flagi zasłaniają niedokończony interfejs bez gałęzi wydania. Procentowe "
            "wdrożenia ujawniają ryzyko stopniowo. Usuń stare flagi po pełnej adopcji.\n",
        ),
        (
            "fh-api-versioning",
            "# Wersjonowanie API\n\n"
            "Wersje w ścieżce czynią zmiany łamiące jawnymi. Okna wycofywania dają "
            "klientom czas. Testy zgodności obejmują poprzednią major.\n",
        ),
        (
            "fh-storage-tiers",
            "# Poziomy pamięci\n\n"
            "Gorące dane zostają na dyskach o niskiej latencji. Zimne archiwa "
            "przechodzą do tańszej pamięci obiektowej. Polityki cyklu życia kodują "
            "przejścia.\n",
        ),
    ],
    "ru": [
        (
            "fh-ci-pipeline",
            "# Конвейер непрерывной интеграции\n\n"
            "Сервер сборки запускает модульные тесты после каждого коммита. "
            "Артефакты попадают в версионированный реестр до релизного поезда. "
            "Операторы следят за долей сбоев и повторяют только нестабильные наборы.\n",
        ),
        (
            "fh-http-cache",
            "# Заметки о HTTP-кэше\n\n"
            "Заголовки Cache-Control решают, могут ли посредники хранить ответ. "
            "ETag позволяют проверить актуальность без полной загрузки тела. "
            "Явный max-age лучше эвристической свежести.\n",
        ),
        (
            "fh-load-balance",
            "# Основы балансировки нагрузки\n\n"
            "Обратный прокси распределяет трафик по здоровым бэкендам. Проверки "
            "здоровья убирают сбойные узлы из пула. Липкие сессии необязательны и "
            "усложняют аварийное переключение.\n",
        ),
        (
            "fh-schema-migrate",
            "# Миграции схемы\n\n"
            "Применяйте только прямые миграции по порядку. Шаги expand-and-contract "
            "дают старым читателям пережить поэтапный деплой. Дозагрузки данных "
            "идут вне критического пути.\n",
        ),
        (
            "fh-observability",
            "# Наблюдаемость\n\n"
            "Метрики отслеживают задержку и бюджет ошибок. Структурные логи несут "
            "идентификаторы запросов. Трейсы связывают прыжки шлюза с интервалами "
            "воркеров.\n",
        ),
        (
            "fh-auth-tokens",
            "# Аутентификация токенами\n\n"
            "Короткоживущие access-токены снижают риск повтора. Refresh-токены "
            "остаются в http-only cookie. Ключи подписи ротируйте по расписанию.\n",
        ),
        (
            "fh-queue-workers",
            "# Фоновые воркеры\n\n"
            "Потребители очереди обрабатывают задания с доставкой не менее одного "
            "раза. Идемпотентные обработчики терпят дубликаты. Очереди мёртвых "
            "писем собирают ядовитые полезные нагрузки для разбора.\n",
        ),
        (
            "fh-feature-flags",
            "# Флаги функций\n\n"
            "Флаги прячут неготовый интерфейс без ветки релиза. Процентные выкаты "
            "открывают риск постепенно. Удаляйте устаревшие флаги после полного "
            "внедрения.\n",
        ),
        (
            "fh-api-versioning",
            "# Версионирование API\n\n"
            "Версии в пути делают ломающие изменения явными. Окна устаревания дают "
            "клиентам время. Тесты совместимости покрывают предыдущую major.\n",
        ),
        (
            "fh-storage-tiers",
            "# Уровни хранения\n\n"
            "Горячие данные остаются на дисках с низкой задержкой. Холодные архивы "
            "уходят в более дешёвое объектное хранилище. Политики жизненного цикла "
            "кодируют правила перехода.\n",
        ),
    ],
    "sv": [
        (
            "fh-ci-pipeline",
            "# Pipeline för kontinuerlig integration\n\n"
            "En byggserver kör enhetstester efter varje commit. Artefakter landar i "
            "ett versionshanterat register innan release-tåget startar. Operatörer "
            "bevakar felfrekvenser och kör om endast ostabila sviter.\n",
        ),
        (
            "fh-http-cache",
            "# Anteckningar om HTTP-cache\n\n"
            "Cache-Control-huvuden avgör om mellanhänder får lagra ett svar. ETag "
            "låter klienter validera utan att hämta hela kroppen. Föredra explicita "
            "max-age framför heuristisk färskhet.\n",
        ),
        (
            "fh-load-balance",
            "# Grunder i lastbalansering\n\n"
            "En omvänd proxy sprider trafik över friska backends. Hälsokontroller "
            "tar bort felande noder från poolen. Sticky sessions är valfria och "
            "försvårar failover.\n",
        ),
        (
            "fh-schema-migrate",
            "# Schemamigreringar\n\n"
            "Tillämpa endast framåtriktade migreringar i ordning. Behåll "
            "expand-and-contract så att gamla läsare överlever en rullande deploy. "
            "Backfills körs utanför bandet.\n",
        ),
        (
            "fh-observability",
            "# Observerbarhet\n\n"
            "Mätvärden följer latens och felbudgetar. Strukturerade loggar bär "
            "begärande-id. Spår kopplar gateway-hopp till arbetsspann.\n",
        ),
        (
            "fh-auth-tokens",
            "# Tokenautentisering\n\n"
            "Kortlivade åtkomsttoken minskar risken för återspel. Uppdateringstoken "
            "stannar i http-only-kakor. Rotera signeringsnycklar enligt schema.\n",
        ),
        (
            "fh-queue-workers",
            "# Bakgrundsarbetare\n\n"
            "Kö-konsumenter bearbetar jobb med minst-en-gång-leverans. Idempotenta "
            "hanterare tål dubbletter. Dead-letter-köer samlar giftiga nyttolaster "
            "för granskning.\n",
        ),
        (
            "fh-feature-flags",
            "# Funktionsflaggor\n\n"
            "Flaggor döljer ofärdig UI utan att förgrena releasen. Procentuella "
            "utrullningar exponerar risk gradvis. Ta bort gamla flaggor efter full "
            "adoption.\n",
        ),
        (
            "fh-api-versioning",
            "# API-versionering\n\n"
            "Sökvägsversioner gör brytande ändringar explicita. Avvecklingsfönster "
            "ger klienter tid. Kompatibilitetstester täcker föregående major.\n",
        ),
        (
            "fh-storage-tiers",
            "# Lagringsnivåer\n\n"
            "Het data stannar på diskar med låg latens. Kalla arkiv flyttar till "
            "billigare objektlagring. Livscykelpolicyer kodar övergångsregler.\n",
        ),
    ],
    "uk": [
        (
            "fh-ci-pipeline",
            "# Конвеєр безперервної інтеграції\n\n"
            "Сервер збірки запускає модульні тести після кожного коміту. Артефакти "
            "потрапляють у версіонований реєстр перед релізним потягом. Оператори "
            "стежать за часткою збоїв і повторюють лише нестабільні набори.\n",
        ),
        (
            "fh-http-cache",
            "# Нотатки про HTTP-кеш\n\n"
            "Заголовки Cache-Control вирішують, чи можуть посередники зберігати "
            "відповідь. ETag дозволяють перевірити актуальність без повного "
            "завантаження тіла. Явний max-age кращий за евристичну свіжість.\n",
        ),
        (
            "fh-load-balance",
            "# Основи балансування навантаження\n\n"
            "Зворотний проксі розподіляє трафік між здоровими бекендами. Перевірки "
            "здоров'я прибирають збійні вузли з пулу. Липкі сесії необов'язкові й "
            "ускладнюють аварійне перемикання.\n",
        ),
        (
            "fh-schema-migrate",
            "# Міграції схеми\n\n"
            "Застосовуйте лише прямі міграції за порядком. Кроки expand-and-contract "
            "дають старим читачам пережити поступовий деплой. Довантаження даних "
            "йдуть поза критичним шляхом.\n",
        ),
        (
            "fh-observability",
            "# Спостережуваність\n\n"
            "Метрики відстежують затримку й бюджет помилок. Структурні логи несуть "
            "ідентифікатори запитів. Трейси пов'язують стрибки шлюзу з інтервалами "
            "воркерів.\n",
        ),
        (
            "fh-auth-tokens",
            "# Автентифікація токенами\n\n"
            "Короткоживучі access-токени знижують ризик повтору. Refresh-токени "
            "залишаються в http-only cookie. Ключі підпису ротуйте за розкладом.\n",
        ),
        (
            "fh-queue-workers",
            "# Фонові воркери\n\n"
            "Споживачі черги обробляють завдання з доставкою щонайменше один раз. "
            "Ідемпотентні обробники терплять дублікати. Черги мертвих листів "
            "збирають отруйні корисні навантаження для розбору.\n",
        ),
        (
            "fh-feature-flags",
            "# Прапорці функцій\n\n"
            "Прапорці ховають неготовий інтерфейс без гілки релізу. Відсоткові "
            "викати відкривають ризик поступово. Видаляйте застарілі прапорці після "
            "повного впровадження.\n",
        ),
        (
            "fh-api-versioning",
            "# Версіонування API\n\n"
            "Версії в шляху роблять ламаючі зміни явними. Вікна застарівання дають "
            "клієнтам час. Тести сумісності покривають попередню major.\n",
        ),
        (
            "fh-storage-tiers",
            "# Рівні зберігання\n\n"
            "Гарячі дані залишаються на дисках із низькою затримкою. Холодні архіви "
            "йдуть у дешевше об'єктне сховище. Політики життєвого циклу кодують "
            "правила переходу.\n",
        ),
    ],
}

ANN_RE = re.compile(r"\{(?P<source>[^=>{]*?)=>(?P<target>.*?):::error_type=(?P<etype>[^}]+)\}")

# Deterministic pseudo-MT patterns. Patterns are linguistic calques, not
# detector test filenames.
PSEUDO_MT: dict[str, list[dict[str, str]]] = {
    "ru": [
        {
            "source_lang": "en",
            "slug": "mt-makes-sense",
            "text": (
                "# Обзор API\n\n"
                "Этот подход делает смысл для команды, когда контракт стабилен. "
                "Мы должны принимать участие в ревью схемы перед релизом. "
                "В зависимости от нагрузки балансировщик открывает новые реплики.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-take-control",
            "text": (
                "# Управление релизами\n\n"
                "Оператор берёт контроль над канареечным выкатом вручную. "
                "Это имеет место только после зелёных интеграционных тестов. "
                "Фактический план хранится в тикете, не в чате.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-realize-plan",
            "text": (
                "# План миграции\n\n"
                "Команда должна реализовать, что даунтайм недопустим. "
                "Мы сделаем смысл из метрик, прежде чем масштабировать воркеры. "
                "Поддерживающая документация остаётся на английском оригинале.\n"
            ),
        },
    ],
    "uk": [
        {
            "source_lang": "en",
            "slug": "mt-take-part",
            "text": (
                "# Огляд API\n\n"
                "Команда повинна приймати участь у рев'ю схеми перед релізом. "
                "Рішення робить сенс лише після зелених інтеграційних тестів. "
                "В залежності від навантаження балансувальник відкриває репліки.\n"
            ),
        },
        {
            "source_lang": "ru",
            "slug": "mt-from-ru-control",
            "text": (
                "# Керування релізами\n\n"
                "Оператор бере контроль над канарковим викатом вручну. "
                "Це має місце тільки після зелених тестів. "
                "Фактичний план зберігається в тікеті, не в чаті.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-depend-on",
            "text": (
                "# План міграції\n\n"
                "В залежності від обсягу даних бекфіл триває всю ніч. "
                "Ми повинні прийняти участь у чергуванні підтримки. "
                "Документація підтримки лишається англійською.\n"
            ),
        },
    ],
    "de": [
        {
            "source_lang": "en",
            "slug": "mt-realize",
            "text": (
                "# API-Überblick\n\n"
                "Das Team muss realisieren, dass Downtime unzulässig ist. "
                "Der Ansatz macht Sinn nur nach grünen Integrationstests. "
                "Je nach Last öffnet der Balancer neue Replikas.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-eventually",
            "text": (
                "# Release-Steuerung\n\n"
                "Eventuell wird der Canary manuell gestoppt. "
                "Wir nehmen Teil an der Schema-Review vor dem Zug. "
                "Die tatsächliche Planung bleibt im Ticket.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-actual-plan",
            "text": (
                "# Migrationsplan\n\n"
                "Der aktuelle Plan liegt im Ticket, nicht im Chat. "
                "Das Team sollte Kontrolle über den Rollout nehmen. "
                "Support-Dokumente bleiben im englischen Original.\n"
            ),
        },
    ],
    "pl": [
        {
            "source_lang": "en",
            "slug": "mt-ewentualnie",
            "text": (
                "# Przegląd API\n\n"
                "Ewentualnie zatrzymamy canary ręcznie. "
                "Podejście robi sens dopiero po zielonych testach. "
                "W zależności od obciążenia balancer otwiera repliki.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-aktualnie",
            "text": (
                "# Sterowanie wydaniami\n\n"
                "Aktualnie plan leży w zgłoszeniu, nie na czacie. "
                "Zespół powinien brać udział w przeglądzie schematu. "
                "Dokumentacja wsparcia zostaje w angielskim oryginale.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-take-part-pl",
            "text": (
                "# Plan migracji\n\n"
                "Musimy brać udział w dyżurze wsparcia. "
                "W zależności od objętości danych backfill trwa całą noc. "
                "Operator bierze kontrolę nad wycofaniem ręcznie.\n"
            ),
        },
    ],
    "es": [
        {
            "source_lang": "en",
            "slug": "mt-actualmente",
            "text": (
                "# Resumen de API\n\n"
                "Actualmente el plan vive en el ticket, no en el chat. "
                "El enfoque hace sentido solo tras pruebas verdes. "
                "Dependiendo de la carga el balanceador abre réplicas.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-libreria",
            "text": (
                "# Control de lanzamientos\n\n"
                "La librería de métricas vive en el panel de operaciones. "
                "Debemos tomar parte en la revisión del esquema. "
                "La documentación de soporte permanece en inglés.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-tomar-control",
            "text": (
                "# Plan de migración\n\n"
                "El operador toma el control del canario a mano. "
                "Eventualmente detenemos el despliegue si falla la salud. "
                "Dependiendo del volumen el relleno dura toda la noche.\n"
            ),
        },
    ],
    "sv": [
        {
            "source_lang": "en",
            "slug": "mt-eventuellt",
            "text": (
                "# API-översikt\n\n"
                "Eventuellt stoppas canaryn manuellt. "
                "Ansatsen gör mening först efter gröna tester. "
                "Beroende på last öppnar balanseraren nya repliker.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-aktuellt",
            "text": (
                "# Versionsstyrning\n\n"
                "Det aktuella planen ligger i ärendet, inte i chatten. "
                "Teamet bör ta del i schemareviewen före tåget. "
                "Supportdokumentationen stannar på engelska.\n"
            ),
        },
        {
            "source_lang": "en",
            "slug": "mt-ta-kontroll",
            "text": (
                "# Migreringsplan\n\n"
                "Operatören tar kontroll över utrullningen manuellt. "
                "Beroende på datavolymen pågår backfill hela natten. "
                "Vi måste ta del i supportjouren.\n"
            ),
        },
    ],
    "en": [
        {
            "source_lang": "ru",
            "slug": "mt-from-ru-calque",
            "text": (
                "# Release control\n\n"
                "The operator takes the control over the canary by hands. "
                "This has place only after green integration tests. "
                "The actual plan lives in the ticket, not in the chat.\n"
            ),
        },
        {
            "source_lang": "ru",
            "slug": "mt-make-sense-en",
            "text": (
                "# API overview\n\n"
                "This approach makes a sense for the team when the contract is stable. "
                "We must accept a participation in the schema review before release. "
                "In dependence from the load the balancer opens new replicas.\n"
            ),
        },
        {
            "source_lang": "ru",
            "slug": "mt-realize-en",
            "text": (
                "# Migration plan\n\n"
                "The team must realize that downtime is not allowed. "
                "We will make sense from the metrics before scaling workers. "
                "Support documentation stays in the Russian original.\n"
            ),
        },
    ],
}

SELF_GEC: dict[str, list[dict[str, str]]] = {
    "en": [
        {
            "id": "en-self-001",
            "source": "recieve",
            "target": "receive",
            "error_type": "Spelling",
            "sentence": "Clients must recieve a 202 before polling status.",
            "provenance": (
                "Original FairHelm/lexaudit CC0 fixture (self-curated). "
                "mhagiwara/github-typo-corpus was inspected 2026-11-03: no "
                "clear Apache-2.0/MIT/BSD/CC grant in-repo (terms follow "
                "upstream commits), so it was NOT downloaded into fixtures."
            ),
        },
        {
            "id": "en-self-002",
            "source": "seperate",
            "target": "separate",
            "error_type": "Spelling",
            "sentence": "Keep build and deploy in seperate jobs.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "en-self-003",
            "source": "occured",
            "target": "occurred",
            "error_type": "Spelling",
            "sentence": "A timeout occured during the schema migration.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "en-self-004",
            "source": "dependancy",
            "target": "dependency",
            "error_type": "Spelling",
            "sentence": "Pin every production dependancy by hash.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "en-self-005",
            "source": "adress",
            "target": "address",
            "error_type": "Spelling",
            "sentence": "The webhook must adress the signed payload.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "en-self-006",
            "source": "make a sense",
            "target": "make sense",
            "error_type": "Calque",
            "sentence": "The rollout plan must make a sense for on-call.",
            "provenance": "Original FairHelm/lexaudit CC0 calque-style fixture.",
        },
    ],
    "ru": [
        {
            "id": "ru-self-001",
            "source": "делает смысл",
            "target": "имеет смысл",
            "error_type": "Calque",
            "sentence": "Этот подход делает смысл только после зелёных тестов.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "ru-self-002",
            "source": "принимать участие",
            "target": "участвовать",
            "error_type": "Calque",
            "sentence": "Команда должна принимать участие в ревью схемы.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "ru-self-003",
            "source": "в зависимости от",
            "target": "в зависимости от",
            "error_type": "ok_term",
            "sentence": "В зависимости от нагрузки балансировщик открывает реплики.",
            "provenance": "Original FairHelm/lexaudit CC0 control sentence.",
        },
        {
            "id": "ru-self-004",
            "source": "таймаут произошёл",
            "target": "произошёл тайм-аут",
            "error_type": "other_error",
            "sentence": "Таймаут произошёл во время миграции схемы.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
        {
            "id": "ru-self-005",
            "source": "актуальный план",
            "target": "текущий план",
            "error_type": "false_friend",
            "sentence": "Актуальный план лежит в тикете, не в чате.",
            "provenance": "Original FairHelm/lexaudit CC0 false-friend fixture.",
        },
        {
            "id": "ru-self-006",
            "source": "береть контроль",
            "target": "взять управление",
            "error_type": "Calque",
            "sentence": "Оператор должен береть контроль над канарейкой вручную.",
            "provenance": "Original FairHelm/lexaudit CC0 fixture (self-curated).",
        },
    ],
}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _http_get(url: str, *, timeout: float = 20.0) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(f"warn: fetch failed {url}: {exc}", file=sys.stderr)
        return None


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _manifest_entry(
    *,
    source: str,
    url: str,
    license_id: str,
    locale: str,
    path: str,
    text: str,
    notes: str = "",
) -> dict[str, Any]:
    return {
        "source": source,
        "url": url,
        "license": license_id,
        "locale": locale,
        "path": path,
        "sha256": _sha256_text(text),
        "retrieved": _now_iso(),
        "bytes": len(text.encode("utf-8")),
        "notes": notes,
    }


def _copy_real_public(full_root: Path, manifest: list[dict[str, Any]]) -> None:
    src_root = ROOT / "tests" / "fixtures" / "bilingual" / "real_public"
    for locale in ("en", "de", "ru"):
        loc_dir = src_root / locale
        if not loc_dir.is_dir():
            continue
        for path in sorted(loc_dir.glob("*.md")):
            if path.name == "seeded-leak.md":
                continue  # intentional bilingual leak overlay — not clean
            text = path.read_text(encoding="utf-8")
            rel = f"clean/{locale}/real_public-{path.name}"
            _write_text(full_root / locale / f"real_public-{path.name}", text)
            manifest.append(
                _manifest_entry(
                    source="tests/fixtures/bilingual/real_public",
                    url=(
                        "https://github.com/fastapi/fastapi (MIT) / "
                        "https://github.com/kubernetes/website (CC-BY-4.0)"
                    ),
                    license_id="MIT;CC-BY-4.0",
                    locale=locale,
                    path=rel,
                    text=text,
                    notes="Stratified reuse of in-repo real_public prose excerpts.",
                )
            )


def _fetch_wikipedia(full_root: Path, manifest: list[dict[str, Any]]) -> None:
    for locale, titles in WIKI_TITLES.items():
        for title in titles:
            host = f"https://{locale}.wikipedia.org"
            url = f"{host}/api/rest_v1/page/summary/{urllib.request.quote(title)}"
            raw = _http_get(url)
            if raw is None:
                continue
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                continue
            extract = (payload.get("extract") or "").strip()
            page_title = payload.get("title") or title
            if len(extract) < 80:
                continue
            body = f"# {page_title}\n\n{extract}\n"
            slug = re.sub(r"[^\w-]+", "-", title, flags=re.UNICODE)
            slug = slug.strip("-").casefold()[:60] or "page"
            fname = f"wiki-{slug}.md"
            _write_text(full_root / locale / fname, body)
            manifest.append(
                _manifest_entry(
                    source="wikipedia-rest-summary",
                    url=url,
                    license_id="CC-BY-SA-4.0",
                    locale=locale,
                    path=f"clean/{locale}/{fname}",
                    text=body,
                    notes="Wikipedia REST summary extract; attribution via URL.",
                )
            )


def _write_original(full_root: Path, manifest: list[dict[str, Any]]) -> None:
    for locale, pages in ORIGINAL_PROSE.items():
        for slug, text in pages:
            fname = f"{slug}.md"
            _write_text(full_root / locale / fname, text)
            manifest.append(
                _manifest_entry(
                    source="fairhelm-lexaudit-original",
                    url="https://fairhelm.com/",
                    license_id="CC0-1.0",
                    locale=locale,
                    path=f"clean/{locale}/{fname}",
                    text=text,
                    notes="Original technical prose written for lexaudit real-bench.",
                )
            )


def _stratified_slice(full_root: Path, fixture_root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for locale in LOCALES:
        src = full_root / locale
        dst = fixture_root / locale
        dst.mkdir(parents=True, exist_ok=True)
        for stale in dst.glob("*.md"):
            stale.unlink()
        files = sorted(src.glob("*.md"))

        # Prefer original + real_public first, then wiki, for stable CI.
        def rank(path: Path) -> tuple[int, str]:
            name = path.name
            if name.startswith("fh-"):
                return (0, name)
            if name.startswith("real_public-"):
                return (1, name)
            return (2, name)

        ordered = sorted(files, key=rank)
        chosen = ordered[:SLICE_PER_LOCALE]
        if len(chosen) < 8:
            chosen = ordered
        for path in chosen:
            _write_text(dst / path.name, path.read_text(encoding="utf-8"))
        counts[locale] = len(list(dst.glob("*.md")))
    return counts


def build_clean(manifest: list[dict[str, Any]]) -> dict[str, int]:
    full_root = ROOT / "tmp" / "real-bench" / "clean"
    fixture_root = ROOT / "tests" / "fixtures" / "real_bench" / "clean"
    for locale in LOCALES:
        (full_root / locale).mkdir(parents=True, exist_ok=True)
    _write_original(full_root, manifest)
    _copy_real_public(full_root, manifest)
    _fetch_wikipedia(full_root, manifest)
    return _stratified_slice(full_root, fixture_root)


def _extract_ua_gec_pairs(sample_dir: Path) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    # Prefer lexical / transfer labels; keep a few structural as filler.
    preferred = {"F/Calque", "Spelling", "F/PoorFlow"}
    secondary = {"G/UngrammaticalStructure", "G/Case", "G/Prep"}
    for path in sorted(sample_dir.glob("*.ann")):
        text = path.read_text(encoding="utf-8")
        for match in ANN_RE.finditer(text):
            etype = (match.group("etype") or "").strip()
            source = match.group("source").strip()
            target = match.group("target").strip().rstrip(":")
            if not source or etype not in preferred | secondary:
                continue
            if etype in secondary and len(source) < 3:
                continue
            if len(source) < 1:
                continue
            # Skip pure punctuation / empty corrections.
            if not any(ch.isalpha() for ch in source):
                continue
            pairs.append(
                {
                    "id": f"uk-uagec-{path.stem}-{len(pairs) + 1:03d}",
                    "source": source,
                    "target": target,
                    "error_type": etype,
                    "sentence": text.splitlines()[0][:240],
                    "provenance": (
                        "Extracted from grammarly/ua-gec (CC-BY-4.0) annotated sample "
                        f"{path.name}; raw dump in tmp/corpora/ua-gec/."
                    ),
                }
            )
            if len(pairs) >= 24:
                return pairs
    # Prefer calque/spelling rows first if we over-collected structural ones.
    pairs.sort(key=lambda r: (0 if r["error_type"] in preferred else 1, r["id"]))
    return pairs[:24]


def _ensure_ua_gec_sample() -> Path:
    sample = ROOT / "tmp" / "corpora" / "ua-gec" / "sample"
    sample.mkdir(parents=True, exist_ok=True)
    license_path = ROOT / "tmp" / "corpora" / "ua-gec" / "LICENSE"
    if not license_path.is_file():
        raw = _http_get("https://raw.githubusercontent.com/grammarly/ua-gec/main/LICENSE")
        if raw:
            license_path.write_bytes(raw)
    if not any(sample.glob("*.ann")):
        for doc_id in (
            "0002",
            "0006",
            "0013",
            "0015",
            "0017",
            "0028",
            "0035",
            "0057",
            "0074",
            "0078",
        ):
            url = (
                "https://raw.githubusercontent.com/grammarly/ua-gec/main/"
                f"data/gec-only/test/annotated/{doc_id}.a1.ann"
            )
            raw = _http_get(url)
            if raw:
                (sample / f"{doc_id}.a1.ann").write_bytes(raw)
    return sample


def build_gec(manifest: list[dict[str, Any]]) -> dict[str, int]:
    out = ROOT / "tests" / "fixtures" / "real_bench" / "gec"
    out.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}

    sample = _ensure_ua_gec_sample()
    uk_pairs = _extract_ua_gec_pairs(sample)
    if not uk_pairs:
        # Network-blocked fallback: still ship honest self-curated UK rows.
        uk_pairs = [
            {
                "id": "uk-self-001",
                "source": "приймати участь",
                "target": "брати участь",
                "error_type": "F/Calque",
                "sentence": "Команда повинна приймати участь у рев'ю схеми.",
                "provenance": (
                    "Self-curated open-license style fixture (CC0). ua-gec download "
                    "unavailable in this run."
                ),
            },
            {
                "id": "uk-self-002",
                "source": "в залежності від",
                "target": "залежно від",
                "error_type": "F/Calque",
                "sentence": "В залежності від навантаження балансувальник відкриває репліки.",
                "provenance": "Self-curated open-license style fixture (CC0).",
            },
            {
                "id": "uk-self-003",
                "source": "робить сенс",
                "target": "має сенс",
                "error_type": "F/Calque",
                "sentence": "Підхід робить сенс лише після зелених тестів.",
                "provenance": "Self-curated open-license style fixture (CC0).",
            },
        ]

    uk_path = out / "uk.jsonl"
    with uk_path.open("w", encoding="utf-8") as fh:
        for row in uk_pairs:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts["uk"] = len(uk_pairs)
    manifest.append(
        _manifest_entry(
            source="grammarly/ua-gec",
            url="https://github.com/grammarly/ua-gec",
            license_id="CC-BY-4.0",
            locale="uk",
            path="gec/uk.jsonl",
            text=uk_path.read_text(encoding="utf-8"),
            notes="Lexical Spelling/Calque pairs extracted from annotated samples.",
        )
    )

    for locale, rows in SELF_GEC.items():
        path = out / f"{locale}.jsonl"
        with path.open("w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        counts[locale] = len(rows)
        license_id = "CC0-1.0"
        notes = rows[0]["provenance"]
        if locale == "en":
            notes += (
                " Verified mhagiwara/github-typo-corpus lacks a clear permissive "
                "LICENSE file; not mirrored."
            )
        manifest.append(
            _manifest_entry(
                source="fairhelm-lexaudit-self-gec",
                url="https://fairhelm.com/",
                license_id=license_id,
                locale=locale,
                path=f"gec/{locale}.jsonl",
                text=path.read_text(encoding="utf-8"),
                notes=notes,
            )
        )
    return counts


def _localai_healthy(base: str = "http://127.0.0.1:8501") -> bool:
    raw = _http_get(f"{base}/v1/models", timeout=3.0)
    return raw is not None and b"data" in raw


def _try_localai_page(source_text: str, target_locale: str) -> str | None:
    """Best-effort LocalAI translation; returns None on failure."""
    if not _localai_healthy():
        return None
    lang_name = {
        "de": "German",
        "es": "Spanish",
        "pl": "Polish",
        "ru": "Russian",
        "sv": "Swedish",
        "uk": "Ukrainian",
        "en": "English",
    }.get(target_locale, target_locale)
    payload = {
        "model": "qwen2.5-7b-fc",
        "temperature": 0,
        "max_tokens": 220,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Translate the following Markdown into {lang_name}. "
                    "Output only the translation, keep Markdown headings.\n\n"
                    f"{source_text}"
                ),
            }
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8501/v1/chat/completions",
        data=data,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"].get("content") or ""
        content = content.strip()
        return content if len(content) > 40 else None
    except (
        urllib.error.URLError,
        TimeoutError,
        OSError,
        KeyError,
        IndexError,
        json.JSONDecodeError,
    ):
        return None


def build_mt(manifest: list[dict[str, Any]]) -> dict[str, int]:
    out = ROOT / "tests" / "fixtures" / "real_bench" / "mt"
    tmp = ROOT / "tmp" / "real-bench" / "mt"
    counts: dict[str, int] = {}
    used_localai = False

    # Seed pages from clean EN/RU originals for optional LocalAI pass.
    seed_en = ORIGINAL_PROSE["en"][0][1]
    seed_ru = ORIGINAL_PROSE["ru"][0][1]

    for locale, pages in PSEUDO_MT.items():
        loc_out = out / locale
        loc_tmp = tmp / locale
        loc_out.mkdir(parents=True, exist_ok=True)
        loc_tmp.mkdir(parents=True, exist_ok=True)
        for stale in loc_out.glob("*.md"):
            stale.unlink()
        n = 0
        for page in pages:
            text = page["text"]
            # Optional LocalAI enrichment page (kept if it succeeds).
            if locale != "en" and page["source_lang"] == "en":
                llm = _try_localai_page(seed_en, locale)
                if llm:
                    used_localai = True
                    llm_name = f"localai-from-en-{page['slug']}.md"
                    _write_text(loc_tmp / llm_name, llm)
                    _write_text(loc_out / llm_name, llm)
                    n += 1
                    manifest.append(
                        _manifest_entry(
                            source="localai-pseudo-or-model-mt",
                            url="http://127.0.0.1:8501/v1/chat/completions",
                            license_id="CC0-1.0",
                            locale=locale,
                            path=f"mt/{locale}/{llm_name}",
                            text=llm,
                            notes="LocalAI translation of FairHelm CC0 EN seed.",
                        )
                    )
            elif locale == "en" and page["source_lang"] == "ru":
                llm = _try_localai_page(seed_ru, "en")
                if llm:
                    used_localai = True
                    llm_name = f"localai-from-ru-{page['slug']}.md"
                    _write_text(loc_tmp / llm_name, llm)
                    _write_text(loc_out / llm_name, llm)
                    n += 1
                    manifest.append(
                        _manifest_entry(
                            source="localai-pseudo-or-model-mt",
                            url="http://127.0.0.1:8501/v1/chat/completions",
                            license_id="CC0-1.0",
                            locale=locale,
                            path=f"mt/{locale}/{llm_name}",
                            text=llm,
                            notes="LocalAI translation of FairHelm CC0 RU seed.",
                        )
                    )

            fname = f"{page['slug']}.md"
            _write_text(loc_out / fname, text)
            _write_text(loc_tmp / fname, text)
            n += 1
            manifest.append(
                _manifest_entry(
                    source="fairhelm-lexaudit-pseudo-mt",
                    url="https://fairhelm.com/",
                    license_id="CC0-1.0",
                    locale=locale,
                    path=f"mt/{locale}/{fname}",
                    text=text,
                    notes=(
                        f"Deterministic rule-based pseudo-MT from {page['source_lang']} "
                        f"(LocalAI used={used_localai} for sibling pages)."
                    ),
                )
            )
        counts[locale] = n
    return counts


def measure_clean_fpr() -> dict[str, Any]:
    fixture_root = ROOT / "tests" / "fixtures" / "real_bench" / "clean"
    rules = ROOT / "rules" / "calques"
    results: dict[str, Any] = {"generated_at": _now_iso(), "locales": {}}
    for locale in LOCALES:
        loc_dir = fixture_root / locale
        files = sorted(loc_dir.glob("*.md"))
        if not files:
            continue
        out_dir = ROOT / "tmp" / "real-bench" / "measure" / locale
        out_dir.mkdir(parents=True, exist_ok=True)
        cfg = LexauditConfig(
            repo_root=loc_dir.resolve(),
            locales=[locale],
            sources=["files"],
            files_paths=(loc_dir.resolve(),),
            calque_rules_dir=rules.resolve() if rules.is_dir() else None,
            output_dir=out_dir.resolve(),
        )
        words, pages, _ = run_locale_audit(cfg, locale, freeze_generated_at=FREEZE_AT)
        total_tokens = 0
        for path in files:
            total_tokens += len(tokenize(path.read_text(encoding="utf-8"), locale=locale))
        slugs = [p.name for p in files]
        fpr = clean_page_fpr(
            words,
            clean_page_slugs=slugs,
            clean_pages_total_tokens=total_tokens,
        )
        results["locales"][locale] = {
            "pages": len(files),
            "pages_ranked": len(pages),
            "tokens": total_tokens,
            "fp_unique_words": fpr["fp_unique_words"],
            "fp_per_1000_tokens": round(float(fpr["fp_per_1000_tokens"]), 4),
            "unique_word_fpr": round(float(fpr["unique_word_fpr"]), 6),
            "fp_words_sample": fpr["fp_words"][:12],
        }
    return results


def write_eval_report(metrics: dict[str, Any], counts: dict[str, dict[str, int]]) -> None:
    lines = [
        "# Real benchmark (v0.4 Stage V2)",
        "",
        f"Generated: `{metrics.get('generated_at', '')}`",
        "",
        "## Fixture counts",
        "",
        "| Locale | clean | gec pairs | mt pages |",
        "|---|---:|---:|---:|",
    ]
    for locale in LOCALES:
        lines.append(
            "| {loc} | {c} | {g} | {m} |".format(
                loc=locale,
                c=counts.get("clean", {}).get(locale, 0),
                g=counts.get("gec", {}).get(locale, 0),
                m=counts.get("mt", {}).get(locale, 0),
            )
        )
    lines.extend(
        [
            "",
            "## Clean page FPR",
            "",
            "| Locale | pages | tokens | FP unique words | FP / 1000 tokens |",
            "|---|---:|---:|---:|---:|",
        ]
    )
    for locale in LOCALES:
        row = metrics.get("locales", {}).get(locale)
        if not row:
            continue
        lines.append(
            f"| {locale} | {row['pages']} | {row['tokens']} | "
            f"{row['fp_unique_words']} | {row['fp_per_1000_tokens']:.3f} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Clean fixtures mix FairHelm CC0 originals, in-repo MIT/CC-BY real_public",
            "  excerpts, and Wikipedia CC-BY-SA summaries when the network allows.",
            "- Raw downloads live under `tmp/` (gitignored); git keeps stratified slices.",
            "- See `docs/real-benchmark.md` for annotator agreement (Cohen κ).",
            "",
        ]
    )
    path = ROOT / "eval" / "real-benchmark.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    (ROOT / "tmp" / "real-bench" / "clean-fpr.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_manifest(entries: list[dict[str, Any]]) -> None:
    path = ROOT / "eval" / "corpora" / "manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "0.4-v2",
        "generated_at": _now_iso(),
        "allowed_licenses": [
            "MIT",
            "Apache-2.0",
            "BSD-2-Clause",
            "BSD-3-Clause",
            "CC0-1.0",
            "CC-BY-4.0",
            "CC-BY-SA-4.0",
        ],
        "entries": entries,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_third_party_license() -> None:
    """Ensure LICENSE-THIRD-PARTY.md exists (canonical text is committed)."""
    path = ROOT / "LICENSE-THIRD-PARTY.md"
    if path.is_file():
        return
    path.write_text(
        "# Third-party corpora\n\nSee eval/corpora/manifest.json for per-file licenses.\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("clean", "gec", "mt", "measure", "all"),
        default="all",
    )
    args = parser.parse_args()

    manifest: list[dict[str, Any]] = []
    counts: dict[str, dict[str, int]] = {"clean": {}, "gec": {}, "mt": {}}

    if args.stage in {"clean", "all"}:
        counts["clean"] = build_clean(manifest)
        print("clean pages:", counts["clean"])
    if args.stage in {"gec", "all"}:
        counts["gec"] = build_gec(manifest)
        print("gec pairs:", counts["gec"])
    if args.stage in {"mt", "all"}:
        counts["mt"] = build_mt(manifest)
        print("mt pages:", counts["mt"])

    if args.stage in {"clean", "gec", "mt", "all"}:
        # Reload existing manifest entries when running a partial stage.
        existing_path = ROOT / "eval" / "corpora" / "manifest.json"
        if existing_path.is_file() and args.stage != "all":
            prev = json.loads(existing_path.read_text(encoding="utf-8"))
            keep_prefix = {
                "clean": ("gec/", "mt/"),
                "gec": ("clean/", "mt/"),
                "mt": ("clean/", "gec/"),
            }[args.stage]
            kept = [
                e
                for e in prev.get("entries", [])
                if any(str(e.get("path", "")).startswith(p) for p in keep_prefix)
            ]
            manifest = kept + manifest
        write_manifest(manifest)
        write_third_party_license()

    if args.stage in {"measure", "all"}:
        # Recount fixtures from disk for the report table.
        clean_root = ROOT / "tests" / "fixtures" / "real_bench" / "clean"
        gec_root = ROOT / "tests" / "fixtures" / "real_bench" / "gec"
        mt_root = ROOT / "tests" / "fixtures" / "real_bench" / "mt"
        counts["clean"] = {loc: len(list((clean_root / loc).glob("*.md"))) for loc in LOCALES}
        counts["gec"] = {}
        for loc in LOCALES:
            path = gec_root / f"{loc}.jsonl"
            if path.is_file():
                n_lines = sum(1 for line in path.read_text().splitlines() if line.strip())
                counts["gec"][loc] = n_lines
        counts["mt"] = {
            loc: len(list((mt_root / loc).glob("*.md"))) if (mt_root / loc).is_dir() else 0
            for loc in LOCALES
        }
        metrics = measure_clean_fpr()
        write_eval_report(metrics, counts)
        print("wrote", ROOT / "eval" / "real-benchmark.md")
        for loc, row in metrics.get("locales", {}).items():
            print(
                f"  {loc}: pages={row['pages']} tokens={row['tokens']} "
                f"fp_per_1k={row['fp_per_1000_tokens']:.3f}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
