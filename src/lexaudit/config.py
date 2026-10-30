"""Configuration loading for lexaudit runs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from lexaudit.core.rank import DEFAULT_RANK_WEIGHTS, RankWeights
from lexaudit.detectors.hunspell import HunspellConfig


@dataclass
class LlmProfile:
    name: str
    base_url: str = "http://127.0.0.1:8501/v1"
    model: str = ""
    timeout_s: float = 120.0
    max_retries: int = 2
    temperature: float = 0.0
    api_key_env: str = "OPENAI_API_KEY"


@dataclass
class LexauditConfig:
    repo_root: Path
    output_dir: Path
    locales: list[str] = field(default_factory=lambda: ["ru", "en", "de"])
    sources: list[str] = field(default_factory=lambda: ["academy", "packs"])
    proper_names_path: Path | None = None
    acronyms_path: Path | None = None
    allowlist_path: Path | None = None
    packs_root: Path | None = None
    academy_root: Path | None = None
    files_paths: tuple[Path, ...] = ()
    gold_slugs: tuple[str, ...] = ()
    regression_needles: tuple[str, ...] = ()
    calque_rules_dir: Path | None = None
    hunspell: HunspellConfig = field(default_factory=HunspellConfig)
    llm_profiles: dict[str, LlmProfile] = field(default_factory=dict)
    llm_cache_dir: Path | None = None
    min_length: int = 2
    enable_llm: bool = False
    enable_morph: bool = True
    enable_compound: bool = True
    enable_foreign: bool = True
    enable_calque: bool = True
    enable_crosslocale: bool = False
    enable_bilingual: bool = False
    bilingual_pairs: tuple[dict[str, object], ...] = ()
    # Corpus-local intentional loans (e.g. DE UI nouns). Never merge into DEFAULT.
    bilingual_extra_loans_path: Path | None = None
    bilingual_extra_loans_locales: tuple[str, ...] = ()
    rank_mode: str = "weighted"
    rank_weights: RankWeights = field(default_factory=lambda: DEFAULT_RANK_WEIGHTS)
    needles: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    def config_hash(self) -> str:
        rw = self.rank_weights
        payload = {
            "locales": self.locales,
            "sources": self.sources,
            "min_length": self.min_length,
            "enable_llm": self.enable_llm,
            "enable_morph": self.enable_morph,
            "enable_compound": self.enable_compound,
            "enable_foreign": self.enable_foreign,
            "enable_calque": self.enable_calque,
            "enable_crosslocale": self.enable_crosslocale,
            "enable_bilingual": self.enable_bilingual,
            "rank_mode": self.rank_mode,
            "rank_weights": {
                "calque": rw.calque,
                "needle": rw.needle,
                "foreign_body_ru": rw.foreign_body_ru,
                "foreign_meta": rw.foreign_meta,
                "suspect_confirmed": rw.suspect_confirmed,
                "suspect_likely": rw.suspect_likely,
                "suspect_weak_hapax": rw.suspect_weak_hapax,
            },
            "needles": self.needles,
        }
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _path_or_none(base: Path, value: Any) -> Path | None:
    if not value:
        return None
    p = Path(str(value))
    if not p.is_absolute():
        p = (base / p).resolve()
    return p


def _str_list(raw: Any) -> list[str]:
    return [str(x).strip() for x in (raw or []) if str(x).strip()]


def _parse_hunspell(base: Path, hun: dict[str, Any]) -> HunspellConfig:
    local_root = _path_or_none(base, hun.get("local_root"))
    return HunspellConfig(
        binary=hun.get("binary"),
        dict_dirs=tuple(hun.get("dict_dirs") or ()),
        local_root=str(local_root) if local_root else None,
        ld_library_path_extra=hun.get("ld_library_path_extra"),
    )


def _parse_llm_profiles(raw: dict[str, Any]) -> dict[str, LlmProfile]:
    profiles: dict[str, LlmProfile] = {}
    for name, pdata in raw.items():
        if not isinstance(pdata, dict):
            continue
        profiles[name] = LlmProfile(
            name=name,
            base_url=str(pdata.get("base_url") or "http://127.0.0.1:8501/v1"),
            model=str(pdata.get("model") or ""),
            timeout_s=float(pdata.get("timeout_s") or 120),
            max_retries=int(pdata.get("max_retries") or 2),
            temperature=float(pdata.get("temperature") or 0.0),
            api_key_env=str(pdata.get("api_key_env") or "OPENAI_API_KEY"),
        )
    return profiles


def _parse_rank_weights(raw: dict[str, Any]) -> RankWeights:
    d = DEFAULT_RANK_WEIGHTS
    return RankWeights(
        calque=float(raw.get("calque", d.calque)),
        needle=float(raw.get("needle", d.needle)),
        foreign_body_ru=float(raw.get("foreign_body_ru", d.foreign_body_ru)),
        foreign_meta=float(raw.get("foreign_meta", d.foreign_meta)),
        suspect_confirmed=float(raw.get("suspect_confirmed", d.suspect_confirmed)),
        suspect_likely=float(raw.get("suspect_likely", d.suspect_likely)),
        suspect_weak_hapax=float(raw.get("suspect_weak_hapax", d.suspect_weak_hapax)),
    )


def _parse_rank_mode(data: dict[str, Any]) -> str:
    rank_mode = str(data.get("rank_mode") or "weighted")
    if rank_mode not in ("raw", "weighted"):
        msg = f"rank_mode must be raw or weighted, got {rank_mode!r}"
        raise ValueError(msg)
    return rank_mode


def load_config(path: Path) -> LexauditConfig:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        msg = f"config must be a mapping: {path}"
        raise TypeError(msg)
    base = path.parent
    files_raw = data.get("files_paths") or data.get("docs_paths") or []
    files_paths = tuple(p for p in (_path_or_none(base, x) for x in files_raw) if p is not None)

    return LexauditConfig(
        repo_root=_path_or_none(base, data.get("repo_root")) or base,
        output_dir=_path_or_none(base, data.get("output_dir")) or (base / "tmp" / "lexaudit"),
        locales=list(data.get("locales") or ["ru", "en", "de"]),
        sources=list(data.get("sources") or ["academy", "packs"]),
        proper_names_path=_path_or_none(base, data.get("proper_names_path")),
        acronyms_path=_path_or_none(base, data.get("acronyms_path")),
        allowlist_path=_path_or_none(base, data.get("allowlist_path")),
        packs_root=_path_or_none(base, data.get("packs_root")),
        academy_root=_path_or_none(base, data.get("academy_root")),
        files_paths=files_paths,
        gold_slugs=tuple(_str_list(data.get("gold_slugs"))),
        regression_needles=tuple(_str_list(data.get("regression_needles"))),
        calque_rules_dir=_path_or_none(base, data.get("calque_rules_dir")),
        hunspell=_parse_hunspell(base, data.get("hunspell") or {}),
        llm_profiles=_parse_llm_profiles(data.get("llm_profiles") or {}),
        llm_cache_dir=_path_or_none(base, data.get("llm_cache_dir")),
        min_length=int(data.get("min_length") or 2),
        enable_llm=bool(data.get("enable_llm") or False),
        enable_morph=bool(data.get("enable_morph", True)),
        enable_compound=bool(data.get("enable_compound", True)),
        enable_foreign=bool(data.get("enable_foreign", True)),
        enable_calque=bool(data.get("enable_calque", True)),
        enable_crosslocale=bool(data.get("enable_crosslocale") or False),
        enable_bilingual=bool(data.get("enable_bilingual") or False),
        bilingual_pairs=tuple(
            x for x in (data.get("bilingual_pairs") or []) if isinstance(x, dict)
        ),
        bilingual_extra_loans_path=_path_or_none(
            base, data.get("bilingual_extra_loans_path")
        ),
        bilingual_extra_loans_locales=tuple(
            _str_list(data.get("bilingual_extra_loans_locales"))
        ),
        rank_mode=_parse_rank_mode(data),
        rank_weights=_parse_rank_weights(data.get("rank_weights") or {}),
        needles=_str_list(data.get("needles")),
        raw=data,
    )


def resolve_or_default_config(
    path: Path | None = None,
    *,
    cwd: Path | None = None,
) -> LexauditConfig:
    """Load explicit config, or auto-discover ./lexaudit.config.yaml, or build zero-config."""
    if path is not None:
        return load_config(path)
    base = (cwd or Path.cwd()).resolve()
    default_file = base / "lexaudit.config.yaml"
    if default_file.is_file():
        return load_config(default_file)
    from lexaudit.detectors.calque import default_calque_rules_dir

    dicts_dir = base / "dicts"
    p_file = dicts_dir / "proper-names.yaml"
    a_file = dicts_dir / "acronyms.yaml"
    al_file = dicts_dir / "allowlist.yaml"
    proper_path = p_file if p_file.is_file() else None
    acronyms_path = a_file if a_file.is_file() else None
    allowlist_path = al_file if al_file.is_file() else None
    return LexauditConfig(
        repo_root=base,
        output_dir=base / "tmp" / "lexaudit",
        locales=["en"],
        sources=["files"],
        proper_names_path=proper_path,
        acronyms_path=acronyms_path,
        allowlist_path=allowlist_path,
        calque_rules_dir=default_calque_rules_dir(),
        needles=["orientir", "denseness", "предпокуп", "блувотер", "чеклист"],
    )
