# Stratified 42-Page Benchmark & Ablation Study (7 European Languages)

![Synthetic Benchmark](images/lexaudit-synthetic-benchmark.jpg)

Also available as a compact vector graphic: [synthetic-benchmark.svg](images/synthetic-benchmark.svg)

## In plain words

We made 42 short test pages, 6 in each of the 7 languages. Half are clean, half contain planted problems, including brand new invented words that no rule knows. Then we asked: does lexaudit put the bad pages first? A plain spellchecker does not. lexaudit does in most cases, and below we show where it still fails. Terms are explained in the [glossary](glossary.md).

## 1. Methodology & Why Naive Benchmarks Are Misleading

A tiny benchmark where every error is already in the rule dictionary and every clean page has zero unknown words will artificially report "100% precision and 100% recall." Real-world multilingual repositories do not look like that.

To evaluate `lexaudit` scientifically across **all 7 supported European languages** (`en`, `de`, `es`, `pl`, `ru`, `sv`, `uk`), the reproducible corpus in [`examples/synthetic-demo/`](../examples/synthetic-demo/lexaudit.config.yaml) contains **42 Markdown documents (6 pages per language)** stratified into 6 distinct document types:

| Page ID | Stratum | Ground Truth | Linguistic & Technical Characteristics |
|---|---|---|---|
| **`01`** | Clean: Brands & Compounds | **Clean** | Valid brand names (`Hallberg-Rassy`, `Garmin`, `Victron`), marine acronyms (`EPIRB`, `SOLAS`, `AIS`, `VHF`), German/Swedish compounds (`Weltumsegelung`, `Skrovbesiktning`), Slavic prepositional cases (`на скеге`, `на скезі`), and 4 single-occurrence part codes. |
| **`02`** | Clean: Technical Specs | **Clean** | Standard technical reference prose with acronyms (`LED`, `USB`) and 4 single-occurrence catalogue codes (`rtkepsilon`, `vbkzeta`, `jkltheta`, `dfkappa`). |
| **`03`** | Clean: Unseen Domain Jargon | **Clean (Hard FP test)** | Editorially valid specialist terms **not yet added** to `proper-names.yaml` or Hunspell (`vinylester`, `haulout`, `Epoxidgrundierung`, `винилэфирной`, `слеминга`, `epoxiprimer`), repeated 2+ times on the page. |
| **`04`** | Defective: Known Calques | **Defective** | Contains known translation calques covered by `rules/calques/{en,de,es,pl,ru,sv,uk}.yaml` (`orientir`, `surveyness`, `checklista`, `przedzakupowy`, `предпокупочный`, `чеклисте`, `в листинге`, `bluewaterig`, `передпокупочний`). |
| **`05`** | Defective: Dictionary False Friends & Leaks | **Defective** | Contains false friends accepted by standard Hunspell (`denseness` in the sense of "data density / notes") or untranslated English stop-word chains in German prose (`of the boat ... for the crew`). |
| **`06`** | Defective: Unseen Open-Set Neologism & Phrase Calque | **Defective (Hard FN test)** | Contains a novel single-occurrence coinage **absent from `rules/calques/*.yaml`** (`dockwalkish`, `Stegmanöverig`, `pantanalezca`, `kejowaty`, `пирсовыйосмотр`, `bryggcheckig`, `причальноогляд`) plus a phrase-level idiom calque composed of valid dictionary words. |

---

## 2. Three-Stage Ablation Results (42 Pages, CPU-Only)

We compare three pipeline configurations across all 7 languages (3 defective pages and 3 clean pages per language, 21 defective pages total):

- **Ablation A - Naive Hunspell (`--mode raw`)**: raw dictionary spellcheck without project allowlists, morphology, compound splitting, or calque rules.
- **Ablation B - Allowlists + Morphology + Compound Splitting (`--mode raw`)**: removes brand/acronym/compound noise, but still ranks pages by raw unweighted suspect count.
- **Ablation C - Full `lexaudit` (`--mode weighted`)**: adds `rules/calques/*.yaml` (including `override_ok`), context-scoped foreign weights, and hapax down-weighting (`0.1` for single-occurrence unknown tokens).

### Macro-Averaged Summary Across All 7 Languages

| Configuration | `Precision@2` | `Precision@3` | `MAP` (Mean Average Precision) | Known-Rule Calque Recall | Open-Set Calque Recall (including unseen) | Total CPU Time (42 pages) |
|---|---:|---:|---:|---:|---:|---:|
| **A. Naive Hunspell (`raw`)** | 0.0% | 23.8% | 0.389 | 0.0% (0/26) | 0.0% (0/33) | 0.54 s |
| **B. Dictionaries + Morph/Compound (`raw`)** | 7.1% | 23.8% | 0.421 | 0.0% (0/26) | 0.0% (0/33) | 0.62 s |
| **C. Full `lexaudit` (`weighted`)** | **100.0%** | **66.7%** | **0.838** | **100.0% (26/26)** | **77.9% (26/33)** | **0.66 s** |

### Per-Language Breakdown (Ablation C vs. Ablation A)

| Locale | Language | Ablation A `P@3` | `lexaudit` `P@2` | `lexaudit` `P@3` | Ablation A `MAP` | `lexaudit` `MAP` | Open-Set Calque Recall |
|---|---|---:|---:|---:|---:|---:|---:|
| **`en`** | English | 33.3% (1/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.244 | **0.833** | **75.0% (3/4)** |
| **`de`** | German | 33.3% (1/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.411 | **0.833** | **66.7% (2/3)** |
| **`es`** | Spanish | 33.3% (1/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.411 | **0.833** | **80.0% (4/5)** |
| **`pl`** | Polish | 33.3% (1/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.478 | **0.867** | **80.0% (4/5)** |
| **`ru`** | Russian | 0.0% (0/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.383 | **0.833** | **83.3% (5/6)** |
| **`sv`** | Swedish | 33.3% (1/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.411 | **0.833** | **80.0% (4/5)** |
| **`uk`** | Ukrainian | 0.0% (0/3) | 100.0% (2/2) | **66.7% (2/3)** | 0.383 | **0.833** | **80.0% (4/5)** |

---

## 3. Error Analysis & Honest Limitations (Why `P@3 = 66.7%` and `MAP = 0.838`)

Examining the exact English ranking output explains both the strength and the boundary of deterministic lexical auditing:

```markdown
| Rank | Ground Truth | Score | Unique Suspects | Page | Top Flagged Tokens |
|---:|---|---:|---:|---|---|
| #1 | DEFECT (page 04) | 12.0 | 2 | en-04-defect-known-calques.md | orientir, surveyness |
| #2 | DEFECT (page 05) |  6.0 | 1 | en-05-defect-false-friend.md | denseness |
| #3 | CLEAN  (page 03) |  1.6 | 2 | en-03-clean-unseen-jargon.md | vinylester, haulout |
| #4 | CLEAN  (page 01) |  0.4 | 4 | en-01-clean-navigation-brands.md | mnvdelta, plkgamma, qwpbeta, zxqalpha |
| #5 | CLEAN  (page 02) |  0.4 | 4 | en-02-clean-battery-specs.md | dfkappa, jkltheta, rtkepsilon, vbkzeta |
| #6 | DEFECT (page 06) |  0.1 | 1 | en-06-defect-unseen-neologism.md | dockwalkish |
```

1. **Why `Precision@2 = 100.0%`:** Pages `04` and `05` contain curated calques (`orientir`, `surveyness`) and the false friend `denseness` (`override_ok: true`). Weighted scoring (`8.0` for `calque`, `6.0` for needle match) lifts them to `#1` and `#2` across all 7 languages.
2. **Why `Precision@3 = 66.7%` (False Positive on Page `03` vs. False Negative on Page `06`):**
   - On clean page `03`, specialist terms not yet in `proper-names.yaml` (`vinylester`, `Epoxidgrundierung`, `винилэфирной`) appear multiple times (`count >= 2`), earning a `suspect` score of `1.5 - 1.8`.
   - On defective page `06`, the planted coinage `dockwalkish` (`Stegmanöverig`, `пирсовыйосмотр`) is an **unseen single-occurrence token** (`count = 1`) not yet in `rules/calques/*.yaml`. Because `lexaudit` down-weights unknown singletons to `0.1` to suppress catalogue-code noise (pages `01` and `02`), an unseen singleton neologism also receives `0.1`.
   - Furthermore, multi-word phrase calques made of valid dictionary words cannot be detected by token-level rules alone.
3. **How teams close the remaining gap in production:**
   - **Step 1:** Add recurring valid domain terms from page `03` (`vinylester`, `haulout`) to `dicts/proper-names.yaml` (drops page `03` score to `0.0`).
   - **Step 2:** Run optional `lexaudit label --tiers likely,weak` (LLM triage) or promote recurring editorial mistakes into `rules/calques/<locale>.yaml`.

## 4. Reproduce the Study Locally

```bash
uv run lexaudit audit --config examples/synthetic-demo/lexaudit.config.yaml
uv run pytest tests/test_synthetic_benchmark.py
```
