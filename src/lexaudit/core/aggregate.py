"""Aggregate tokens into occurrence maps."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from lexaudit.core.types import VocabOccurrence, VocabSample


def add_tokens(
    occ_map: dict[str, VocabOccurrence],
    tokens: Sequence[Mapping[str, object]],
    *,
    path: str,
    scope: str,
    max_samples: int = 5,
    line_base: int = 1,
) -> None:
    """Mutate occurrence map with tokens from one chunk.

    Token mappings may include ``line`` / ``start_col`` / ``end_col`` (1-based within
    the chunk). ``line_base`` shifts chunk-local lines to file-absolute lines.
    """
    for tok in tokens:
        normalized = str(tok["normalized"])
        surface = str(tok["surface"])
        local_line = tok.get("line")
        start_col = tok.get("start_col")
        end_col = tok.get("end_col")
        line = line_base + local_line - 1 if isinstance(local_line, int) else None
        sample = VocabSample(
            path=path,
            scope=scope,
            line=line,
            start_col=int(start_col) if isinstance(start_col, int) else None,
            end_col=int(end_col) if isinstance(end_col, int) else None,
        )
        occ = occ_map.get(normalized)
        if occ is None:
            occ = VocabOccurrence(normalized=normalized, surface=surface)
            occ_map[normalized] = occ
        occ.count += 1
        if len(occ.samples) < max_samples:
            dup = any(
                s.path == sample.path
                and s.scope == sample.scope
                and s.line == sample.line
                and s.start_col == sample.start_col
                for s in occ.samples
            )
            if not dup:
                occ.samples.append(sample)
