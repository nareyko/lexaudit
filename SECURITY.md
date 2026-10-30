# Security

## Reporting

Contact the maintainer (**Vadim Nareyko**, [github.com/nareyko](https://github.com/nareyko)) via GitHub for sensitive security reports. Do not open public issues for corpus leakage or credential exposure.

## Scope notes

- `lexaudit` reads local files configured by the user; it never uploads corpora by default.
- Optional LLM labeling calls a user-configured OpenAI-compatible endpoint; treat prompts and context snippets as sensitive.
- Local LLM caches and evaluation datasets (`gold/`, `eval/`) may embed private document snippets and are excluded from version control via `.gitignore`.
