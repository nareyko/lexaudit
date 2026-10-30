#!/usr/bin/env python3
# ruff: noqa: RUF001
"""Write packs_field ``02-clean-domain.md`` (ordinary domain prose, no pack coinages).

Safe to re-run. Does not touch defect seeds. Keep short — no dumps.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELD = ROOT / "tests" / "fixtures" / "packs_field"

# Ordinary domain words only — never invent *-ness / *-ize pack coinages here.
TEXTS: dict[str, dict[str, str]] = {
    "saas-ui-v0": {
        "en": (
            "# Workspace settings\n\n"
            "Open the project menu, review notifications, and save preferences. "
            "Help articles use ordinary product language without invented jargon.\n"
        ),
        "de": (
            "# Arbeitsbereich-Einstellungen\n\n"
            "Öffnen Sie das Projektmenü, prüfen Sie Benachrichtigungen und speichern "
            "Sie Einstellungen. Die Hilfe nutzt gewöhnliche Produktsprache.\n"
        ),
        "ru": (
            "# Настройки рабочего пространства\n\n"
            "Откройте меню проекта, просмотрите уведомления и сохраните настройки. "
            "Справка использует обычный язык продукта без выдуманных терминов.\n"
        ),
    },
    "fintech-v0": {
        "en": (
            "# Payments overview\n\n"
            "Check the account balance, send a transfer, and download the invoice. "
            "Currency codes and bank labels stay ordinary finance vocabulary.\n"
        ),
        "de": (
            "# Zahlungsübersicht\n\n"
            "Prüfen Sie den Kontostand, senden Sie eine Überweisung und laden Sie "
            "die Rechnung herunter. Währungen und Bankbegriffe bleiben üblich.\n"
        ),
        "ru": (
            "# Обзор платежей\n\n"
            "Проверьте баланс счёта, отправьте перевод и скачайте счёт. "
            "Коды валют и банковские подписи — обычная финансовая лексика.\n"
        ),
    },
    "developer-docs-v0": {
        "en": (
            "# API documentation\n\n"
            "Describe the request, response schema, and versioned endpoints. "
            "Examples use ordinary engineering words, not invented verbs.\n"
        ),
        "de": (
            "# API-Dokumentation\n\n"
            "Beschreiben Sie Anfrage, Antwortschema und versionierte Endpunkte. "
            "Beispiele nutzen gewöhnliche Technikbegriffe.\n"
        ),
        "ru": (
            "# Документация API\n\n"
            "Опишите запрос, схему ответа и версионированные эндпоинты. "
            "Примеры используют обычные инженерные слова.\n"
        ),
    },
    "ecommerce-ui-v0": {
        "en": (
            "# Shopping bag\n\n"
            "Add a product, choose shipping, and place the order. "
            "Refund and stock notes stay ordinary retail language.\n"
        ),
        "de": (
            "# Warenkorb\n\n"
            "Legen Sie ein Produkt hinein, wählen Sie den Versand und bestellen Sie. "
            "Rückgabe und Lagerhinweise bleiben übliche Handelssprache.\n"
        ),
        "ru": (
            "# Корзина\n\n"
            "Добавьте товар, выберите доставку и оформите заказ. "
            "Возврат и остатки — обычный язык витрины.\n"
        ),
    },
    "healthcare-ui-v0": {
        "en": (
            "# Patient chart\n\n"
            "Review the visit summary, medications, and lab results. "
            "Clinical notes use ordinary care vocabulary.\n"
        ),
        "de": (
            "# Patientenakte\n\n"
            "Prüfen Sie den Besuchsbereich, Medikamente und Laborwerte. "
            "Klinische Notizen nutzen gewöhnliche Fachsprache.\n"
        ),
        "ru": (
            "# Карта пациента\n\n"
            "Просмотрите итог визита, лекарства и результаты анализов. "
            "Клинические заметки — обычная медицинская лексика.\n"
        ),
    },
    "legal-docs-v0": {
        "en": (
            "# Contract summary\n\n"
            "List the parties, term, and obligations. "
            "Definitions stay ordinary legal English without coinages.\n"
        ),
        "de": (
            "# Vertragsübersicht\n\n"
            "Nennen Sie Parteien, Laufzeit und Pflichten. "
            "Definitionen bleiben gewöhnliche Rechtssprache.\n"
        ),
        "ru": (
            "# Краткое содержание договора\n\n"
            "Укажите стороны, срок и обязательства. "
            "Определения — обычный юридический язык.\n"
        ),
    },
    "gaming-ui-v0": {
        "en": (
            "# Game HUD notes\n\n"
            "Show health, score, and inventory slots. "
            "Interface copy uses ordinary game words.\n"
        ),
        "de": (
            "# HUD-Hinweise\n\n"
            "Zeigen Sie Gesundheit, Punktestand und Inventarplätze. "
            "Die Oberfläche nutzt gewöhnliche Spielbegriffe.\n"
        ),
        "ru": (
            "# Заметки по HUD\n\n"
            "Покажите здоровье, счёт и слоты инвентаря. "
            "Интерфейс использует обычные игровые слова.\n"
        ),
    },
    "edtech-v0": {
        "en": (
            "# Course home\n\n"
            "Open the lesson, submit the assignment, and check grades. "
            "Platform copy stays ordinary classroom language.\n"
        ),
        "de": (
            "# Kursstart\n\n"
            "Öffnen Sie die Lektion, geben Sie die Aufgabe ab und prüfen Sie Noten. "
            "Die Plattform nutzt gewöhnliche Unterrichtssprache.\n"
        ),
        "ru": (
            "# Главная курса\n\n"
            "Откройте урок, сдайте задание и проверьте оценки. "
            "Текст платформы — обычный учебный язык.\n"
        ),
    },
    "security-docs-v0": {
        "en": (
            "# Vulnerability report\n\n"
            "Describe the severity, affected component, and fix status. "
            "Security notes use ordinary advisory language.\n"
        ),
        "de": (
            "# Schwachstellenbericht\n\n"
            "Beschreiben Sie Schweregrad, betroffene Komponente und Fix-Status. "
            "Hinweise nutzen gewöhnliche Advisory-Sprache.\n"
        ),
        "ru": (
            "# Отчёт об уязвимости\n\n"
            "Опишите критичность, затронутый компонент и статус исправления. "
            "Текст использует обычный язык advisory.\n"
        ),
    },
    "hr-ats-v0": {
        "en": (
            "# Candidate pipeline\n\n"
            "Move the applicant to interview, attach a resume, and record feedback. "
            "Hiring copy uses ordinary HR language.\n"
        ),
        "de": (
            "# Bewerberpipeline\n\n"
            "Verschieben Sie die Bewerbung zum Interview, hängen Sie den Lebenslauf an "
            "und erfassen Sie Feedback. Texte nutzen gewöhnliche HR-Sprache.\n"
        ),
        "ru": (
            "# Воронка кандидатов\n\n"
            "Переведите кандидата на собеседование, приложите резюме и запишите отзыв. "
            "Текст найма — обычный HR-язык.\n"
        ),
    },
}


def main() -> int:
    written = 0
    for pack, locales in TEXTS.items():
        for loc, body in locales.items():
            dest = FIELD / pack / loc / "02-clean-domain.md"
            if not dest.parent.is_dir():
                continue
            dest.write_text(body, encoding="utf-8")
            written += 1
            print(f"OK {dest.relative_to(ROOT)}")
    print(f"wrote {written} clean-domain fixtures")
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
