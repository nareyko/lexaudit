# Glossary: the words used in these docs

No linguistics degree needed. Each term below has a one-line meaning and an example.

| Term | Plain meaning | Example |
|---|---|---|
| Calque | A word or phrase copied from another language that sounds odd in yours | Russian "листинг" for a boat advert list |
| False friend | A real dictionary word that is used with the wrong meaning | English "denseness" used where "density" is meant |
| Invented word | A word that does not exist and is not a known name | "wavetension" |
| Foreign word | A word from another language or script that slipped into the text | English "the" inside a German article |
| Suspect | A word the dictionary does not know and no rule explains. It may be fine | A new product name |
| Needle | A word you already know is a problem and want found everywhere | "orientir" |
| Allowlist | Words you tell the tool are fine (names, abbreviations) | "Bavaria", "ISO" |
| Compound | German or Swedish long words built from shorter ones | "Rumpfverstärkung" |
| Hapax | A word that appears only once in the whole text. Often a typo | "recieve" |
| Page score | How many problems a page has, weighted by how serious they are | 14.5 |
| Precision@K | Of the K pages the tool puts first, how many really are bad | P@3 = 2 of 3 |
| Recall | Of all real problems, how many the tool found | 77.9% |
| MAP | One number from 0 to 1 for "bad pages are near the top". Higher is better | 0.838 |
| Open-set | Problems that no rule knew about in advance | A brand new calque |
| CLEAR | A soft check that a fixed page no longer has its old problem | CLEAR / FAIL |
| Deterministic | Same input always gives the same output | Reports are byte-identical |
| Bilingual leftover | Same Latin (or Cyrillic) token in source and target (often untranslated) | EN "sidebar" left in RU UI copy |
| Crosslocale | Opt-in boost when a suspect in RU/DE also looks normal in EN | `enable_crosslocale` + `ref_ok` |
| Pack | Installable YAML rule bundle under `packs/` | `saas-ui-v0` |

Short rule of thumb: lexaudit points at pages and words. A person decides what to change. The tool never edits your files.
