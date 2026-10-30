# Spelling backends on the same text

## In plain words

lexaudit can check spelling with the system `hunspell` program, or with a built-in
Python checker (`spylls`) that reads the same `.aff` / `.dic` files. Most words get
the same label either way. A few edge cases differ. Calque rules and ranking weights
are identical for both backends.

## How to compare on one corpus

```bash
uv run lexaudit fetch-dicts --locale en
uv run python scripts/backend_compare.py
```

The script runs the English half of `examples/synthetic-demo` twice: once with the
normal resolver (system hunspell when present, otherwise spylls), and once forcing
spylls. It prints Precision@2, Precision@3, MAP, runtime, and a Jaccard overlap of
`word:status` pairs.

## How to read the numbers

| Signal | Meaning |
|---|---|
| P@2 / P@3 / MAP | Same ranking metrics as the published benchmark |
| `en_status_jaccard` | Share of identical word:status pairs; closer to 1.0 is better |
| seconds | Wall time for that backend on the demo |

Prefer system hunspell when it is installed: it is usually a bit faster after warm-up.
Prefer spylls when you cannot install system packages (CI without apt, locked laptops).
Dictionaries themselves come from `lexaudit fetch-dicts` in both cases.

## One-file check

```bash
# Same file, two environments
lexaudit audit --path ./README.md --locale en --check --no-html
# After uninstalling hunspell, the built-in checker is used automatically.
```
