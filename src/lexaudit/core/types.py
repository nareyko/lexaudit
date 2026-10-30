"""Shared types for the classification pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

VocabStatus = Literal[
    "ok",
    "proper",
    "acronym",
    "foreign",
    "calque",
    "invented",
    "morph-miss",
    "template",
    "unsure",
    "suspect",
]

Tier = Literal["confirmed", "likely", "weak"]

V1_LOCALES = ("en", "de", "pl", "ru", "es", "sv", "uk")
DEEP_LOCALES = ("ru", "en", "de")


@dataclass
class VocabSample:
    path: str
    scope: str


@dataclass
class VocabOccurrence:
    normalized: str
    surface: str
    count: int = 0
    samples: list[VocabSample] = field(default_factory=list)


@dataclass
class ClassifiedWord:
    normalized: str
    surface: str
    count: int
    status: VocabStatus
    samples: list[VocabSample]
    tier: Tier | None = None
    reason: str = ""
    detectors: list[str] = field(default_factory=list)


@dataclass
class TextChunk:
    path: str
    scope: str
    text: str
    source: str


@dataclass
class PageSuspectRank:
    path: str
    unique_suspects: int
    sample_words: list[str]
    score: float = 0.0
