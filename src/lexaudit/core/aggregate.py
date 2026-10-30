"""Aggregate tokens into occurrence maps."""

from __future__ import annotations

from lexaudit.core.types import VocabOccurrence, VocabSample


def add_tokens(
    occ_map: dict[str, VocabOccurrence],
    tokens: list[dict[str, str]],
    *,
    path: str,
    scope: str,
    max_samples: int = 5,
) -> None:
    """Mutate occurrence map with tokens from one chunk."""
    sample = VocabSample(path=path, scope=scope)
    for tok in tokens:
        normalized = tok["normalized"]
        surface = tok["surface"]
        occ = occ_map.get(normalized)
        if occ is None:
            occ = VocabOccurrence(normalized=normalized, surface=surface)
            occ_map[normalized] = occ
        occ.count += 1
        if len(occ.samples) < max_samples:
            dup = any(s.path == sample.path and s.scope == sample.scope for s in occ.samples)
            if not dup:
                occ.samples.append(sample)
