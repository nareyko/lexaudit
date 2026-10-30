"""Gold labeling helpers using versioned prompts."""

from __future__ import annotations

from pathlib import Path

from lexaudit.llm.client import LlmClient

PROMPT_PATH = Path(__file__).parent / "prompts" / "label-v1.md"
PROMPT_VERSION = "label-v1"
ALLOWED = frozenset(
    {
        "ok",
        "proper",
        "acronym",
        "foreign",
        "calque",
        "invented",
        "morph-miss",
        "template",
        "unsure",
    }
)


def load_label_prompt() -> tuple[str, str]:
    """Return (system, user_template) from label-v1.md."""
    text = PROMPT_PATH.read_text(encoding="utf-8")
    system = ""
    if "## System" in text:
        system = text.split("## System", 1)[1]
        if "## User template" in system:
            system = system.split("## User template", 1)[0]
    system = system.strip()
    user_template = "locale: {{locale}}\nword: {{word}}\ncontext: {{context}}\npath: {{path}}\n"
    return system, user_template


def label_word(
    client: LlmClient,
    *,
    locale: str,
    word: str,
    context: str,
    path: str,
) -> dict[str, object]:
    system, user_template = load_label_prompt()
    user = (
        user_template.replace("{{locale}}", locale)
        .replace("{{word}}", word)
        .replace("{{context}}", context)
        .replace("{{path}}", path)
    )
    parsed = client.chat_json(
        system=system,
        user=user,
        prompt_version=PROMPT_VERSION,
        word=word,
        context=context,
    )
    label = str(parsed.get("label") or "unsure")
    if label not in ALLOWED:
        label = "unsure"
    return {
        "label": label,
        "confidence": float(parsed.get("confidence") or 0.0),
        "rationale": str(parsed.get("rationale") or "")[:200],
        "model": client.profile.model,
        "prompt_version": PROMPT_VERSION,
    }
