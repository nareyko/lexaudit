#!/usr/bin/env python3
"""Deterministically generate SVG diagrams for lexaudit docs.

SVGs are the git SSOT. Optional high-DPI JPGs (``--jpg``) stay local —
``docs/images/*.jpg`` is gitignored (~1 MiB of raster duplicates).
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "docs" / "images"

OVERVIEW_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-label="lexaudit overview">
  <rect width="1280" height="720" fill="#f7f5f0"/>
  <rect x="40" y="32" width="1200" height="84" rx="12" fill="#1b2a4a"/>
  <text x="72" y="72" font-family="DejaVu Sans,sans-serif" font-size="28" font-weight="700" fill="#ffffff">lexaudit - Multilingual Vocabulary Audit &amp; Page Queue</text>
  <text x="72" y="100" font-family="DejaVu Sans,sans-serif" font-size="16" fill="#cfe8e8">7 European Languages: EN, DE, ES, PL, RU, SV, UK  |  CPU-Only (No GPU Required)  |  Read-Only on Your Files</text>

  <!-- Step 1: Inputs -->
  <rect x="40" y="148" width="340" height="430" rx="14" fill="#ffffff" stroke="#1b2a4a" stroke-width="2.5"/>
  <rect x="40" y="148" width="340" height="54" rx="14" fill="#1b2a4a"/>
  <text x="210" y="182" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="20" font-weight="700" fill="#ffffff">1. Your Text &amp; Dictionaries</text>

  <rect x="68" y="226" width="284" height="76" rx="8" fill="#f0f4f8" stroke="#c5cdd8"/>
  <text x="86" y="254" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#1b2a4a">Markdown &amp; Docs (files)</text>
  <text x="86" y="280" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">README.md, docs/**/*.md, courses</text>

  <rect x="68" y="320" width="284" height="76" rx="8" fill="#f0f4f8" stroke="#c5cdd8"/>
  <text x="86" y="348" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#1b2a4a">Structured JSON / JSONL</text>
  <text x="86" y="374" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">Articles, encyclopedias, model packs</text>

  <rect x="68" y="414" width="284" height="136" rx="8" fill="#eaf6f6" stroke="#0d7377"/>
  <text x="86" y="442" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#0d7377">Project Allowlists &amp; Rules</text>
  <text x="86" y="468" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- proper-names.yaml (brands)</text>
  <text x="86" y="492" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- acronyms.yaml (abbreviations)</text>
  <text x="86" y="516" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- rules/calques/*.yaml (7 locales)</text>

  <!-- Arrow 1 -> 2 -->
  <path d="M388 360 H436" stroke="#0d7377" stroke-width="4" fill="none"/>
  <polygon points="436,352 452,360 436,368" fill="#0d7377"/>

  <!-- Step 2: Pipeline -->
  <rect x="458" y="148" width="384" height="430" rx="14" fill="#ffffff" stroke="#0d7377" stroke-width="2.5"/>
  <rect x="458" y="148" width="384" height="54" rx="14" fill="#0d7377"/>
  <text x="650" y="182" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="20" font-weight="700" fill="#ffffff">2. 6-Stage CPU Analysis (~1 sec)</text>

  <g font-family="DejaVu Sans,sans-serif" font-size="14" fill="#1b2a4a">
    <rect x="484" y="220" width="332" height="48" rx="6" fill="#f7f9fb" stroke="#c5cdd8"/>
    <text x="500" y="249"><tspan font-weight="700">1. Tokenize (NFC):</tspan> strip URLs, code, links</text>

    <rect x="484" y="278" width="332" height="48" rx="6" fill="#f7f9fb" stroke="#c5cdd8"/>
    <text x="500" y="307"><tspan font-weight="700">2. Allowlists:</tspan> clear brands &amp; acronyms</text>

    <rect x="484" y="336" width="332" height="48" rx="6" fill="#f7f9fb" stroke="#c5cdd8"/>
    <text x="500" y="365"><tspan font-weight="700">3. Hunspell:</tspan> check 7 European dictionaries</text>

    <rect x="484" y="394" width="332" height="48" rx="6" fill="#f7f9fb" stroke="#c5cdd8"/>
    <text x="500" y="423"><tspan font-weight="700">4. Morph &amp; Compounds:</tspan> RU/UK + DE/SV</text>

    <rect x="484" y="452" width="332" height="48" rx="6" fill="#fdf2f2" stroke="#d9a3a3"/>
    <text x="500" y="481"><tspan font-weight="700" fill="#8b3a4a">5. Foreign &amp; Calques:</tspan> catch false friends</text>

    <rect x="484" y="510" width="332" height="48" rx="6" fill="#eaf6f6" stroke="#0d7377"/>
    <text x="500" y="539"><tspan font-weight="700" fill="#0d7377">6. Weighted Rank:</tspan> score pages by priority</text>
  </g>

  <!-- Arrow 2 -> 3 -->
  <path d="M848 360 H896" stroke="#0d7377" stroke-width="4" fill="none"/>
  <polygon points="896,352 912,360 896,368" fill="#0d7377"/>

  <!-- Step 3: Outputs -->
  <rect x="918" y="148" width="322" height="430" rx="14" fill="#ffffff" stroke="#1b2a4a" stroke-width="2.5"/>
  <rect x="918" y="148" width="322" height="54" rx="14" fill="#1b2a4a"/>
  <text x="1079" y="182" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="20" font-weight="700" fill="#ffffff">3. Editor-Ready Reports</text>

  <rect x="944" y="226" width="270" height="84" rx="8" fill="#eaf6f6" stroke="#0d7377"/>
  <text x="962" y="256" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#0d7377">queue.md &amp; rewrite-queue</text>
  <text x="962" y="280" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">Pages sorted by defect severity</text>
  <text x="962" y="298" font-family="DejaVu Sans,sans-serif" font-size="12" fill="#4a5568">(fix top pages first)</text>

  <rect x="944" y="328" width="270" height="84" rx="8" fill="#f0f4f8" stroke="#c5cdd8"/>
  <text x="962" y="358" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#1b2a4a">summary.md &amp; suspect.csv</text>
  <text x="962" y="382" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">Spreadsheet-ready word table</text>
  <text x="962" y="400" font-family="DejaVu Sans,sans-serif" font-size="12" fill="#4a5568">with counts and file locations</text>

  <rect x="944" y="430" width="270" height="120" rx="8" fill="#f0f4f8" stroke="#c5cdd8"/>
  <text x="962" y="460" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#1b2a4a">lexaudit explain &lt;word&gt;</text>
  <text x="962" y="486" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">Shows why a word was flagged</text>
  <text x="962" y="508" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#0d7377">and suggests natural phrasing</text>
  <text x="962" y="530" font-family="DejaVu Sans,sans-serif" font-size="12" fill="#4a5568">+ report.json (Schema v1)</text>

  <!-- Bottom Safety Banner -->
  <rect x="40" y="608" width="1200" height="68" rx="10" fill="#ffffff" stroke="#0d7377" stroke-width="2"/>
  <text x="640" y="649" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#1b2a4a">Safe by Design (Detection Only): lexaudit never overwrites or auto-replaces your source articles.</text>
</svg>
"""

CLASSIFY_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="960" height="1120" viewBox="0 0 960 1120" role="img" aria-label="Word classification pipeline">
  <rect width="960" height="1120" fill="#f7f5f0"/>
  <rect x="40" y="28" width="880" height="78" rx="12" fill="#1b2a4a"/>
  <text x="480" y="64" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="25" font-weight="700" fill="#ffffff">How lexaudit Classifies Every Word (Step by Step)</text>
  <text x="480" y="92" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#cfe8e8">Supported European Locales: EN, DE, ES, PL, RU, SV, UK  |  Deterministic CPU Pipeline</text>

  <!-- Step boxes -->
  <g font-family="DejaVu Sans,sans-serif">
    <!-- Step 1 -->
    <rect x="80" y="132" width="800" height="92" rx="10" fill="#ffffff" stroke="#1b2a4a" stroke-width="2"/>
    <text x="110" y="168" font-size="18" font-weight="700" fill="#1b2a4a">Step 1. Extract Word from Page (Unicode NFC + Scope)</text>
    <text x="110" y="198" font-size="14" fill="#4a5568">Strips code blocks, URLs, and domain links; records whether the word is in a Title or Body paragraph.</text>

    <path d="M480 224 V252" stroke="#0d7377" stroke-width="3"/><polygon points="473,250 480,262 487,250" fill="#0d7377"/>

    <!-- Step 2 -->
    <rect x="80" y="262" width="800" height="92" rx="10" fill="#ffffff" stroke="#3a5a8c" stroke-width="2"/>
    <text x="110" y="298" font-size="18" font-weight="700" fill="#3a5a8c">Step 2. Project Allowlists (Brands, Acronyms, Section Headings)</text>
    <text x="110" y="328" font-size="14" fill="#4a5568">Known brand names -> status "proper" | Abbreviations (EPIRB, GPS) -> "acronym" | Headings -> "template".</text>

    <path d="M480 354 V382" stroke="#0d7377" stroke-width="3"/><polygon points="473,380 480,392 487,380" fill="#0d7377"/>

    <!-- Step 3 -->
    <rect x="80" y="392" width="800" height="92" rx="10" fill="#ffffff" stroke="#2f6f4e" stroke-width="2"/>
    <text x="110" y="428" font-size="18" font-weight="700" fill="#2f6f4e">Step 3. Hunspell Dictionary Check (EN, DE, ES, PL, RU, SV, UK)</text>
    <text x="110" y="458" font-size="14" fill="#4a5568">Standard words in the language dictionary are marked "ok" (still checked for false friends in Step 6).</text>

    <path d="M480 484 V512" stroke="#0d7377" stroke-width="3"/><polygon points="473,510 480,522 487,510" fill="#0d7377"/>

    <!-- Step 4 -->
    <rect x="80" y="522" width="800" height="92" rx="10" fill="#ffffff" stroke="#0d7377" stroke-width="2"/>
    <text x="110" y="558" font-size="18" font-weight="700" fill="#0d7377">Step 4. Morphology (RU, UK) &amp; Compound Word Splitting (DE, SV)</text>
    <text x="110" y="588" font-size="14" fill="#4a5568">Clears valid Slavic case endings (pymorphy3) and German/Swedish compounds built from known roots -> "ok".</text>

    <path d="M480 614 V642" stroke="#0d7377" stroke-width="3"/><polygon points="473,640 480,652 487,640" fill="#0d7377"/>

    <!-- Step 5 -->
    <rect x="80" y="652" width="800" height="92" rx="10" fill="#ffffff" stroke="#a15c2a" stroke-width="2"/>
    <text x="110" y="688" font-size="18" font-weight="700" fill="#a15c2a">Step 5. Foreign Script &amp; Untranslated Stop-Word Leak</text>
    <text x="110" y="718" font-size="14" fill="#4a5568">Flags untranslated Latin words inside Russian/Ukrainian prose or English stop words ("of", "the") in German -> "foreign".</text>

    <path d="M480 744 V772" stroke="#0d7377" stroke-width="3"/><polygon points="473,770 480,782 487,770" fill="#0d7377"/>

    <!-- Step 6 -->
    <rect x="80" y="782" width="800" height="92" rx="10" fill="#fdf2f2" stroke="#8b3a4a" stroke-width="2.5"/>
    <text x="110" y="818" font-size="18" font-weight="700" fill="#8b3a4a">Step 6. Calque &amp; False-Friend Rules (Including override_ok)</text>
    <text x="110" y="848" font-size="14" fill="#1b2a4a">Matches rules/calques/{en,de,es,pl,ru,sv,uk}.yaml; flips dictionary false friends (e.g. "denseness") -> "calque".</text>

    <path d="M480 874 V902" stroke="#0d7377" stroke-width="3"/><polygon points="473,900 480,912 487,900" fill="#0d7377"/>

    <!-- Step 7 -->
    <rect x="80" y="912" width="800" height="84" rx="10" fill="#ffffff" stroke="#b45309" stroke-width="2"/>
    <text x="110" y="946" font-size="18" font-weight="700" fill="#b45309">Step 7. Remaining Unknown Words -> "suspect" (3 tiers)</text>
    <text x="110" y="974" font-size="14" fill="#4a5568">Single-occurrence part codes get low weight (0.1); repeated unknown words get higher review priority.</text>
  </g>

  <!-- Legend -->
  <rect x="80" y="1018" width="800" height="74" rx="10" fill="#ffffff" stroke="#c5cdd8" stroke-width="1.5"/>
  <text x="104" y="1044" font-family="DejaVu Sans,sans-serif" font-size="13" font-weight="700" fill="#1b2a4a">Final Word Statuses:</text>
  <g font-family="DejaVu Sans,sans-serif" font-size="13" font-weight="700" fill="#ffffff">
    <rect x="104" y="1054" width="68" height="26" rx="5" fill="#2f6f4e"/><text x="138" y="1072" text-anchor="middle">ok</text>
    <rect x="182" y="1054" width="82" height="26" rx="5" fill="#3a5a8c"/><text x="223" y="1072" text-anchor="middle">proper</text>
    <rect x="274" y="1054" width="92" height="26" rx="5" fill="#3a5a8c"/><text x="320" y="1072" text-anchor="middle">acronym</text>
    <rect x="376" y="1054" width="96" height="26" rx="5" fill="#6b7280"/><text x="424" y="1072" text-anchor="middle">template</text>
    <rect x="482" y="1054" width="88" height="26" rx="5" fill="#a15c2a"/><text x="526" y="1072" text-anchor="middle">foreign</text>
    <rect x="580" y="1054" width="84" height="26" rx="5" fill="#8b3a4a"/><text x="622" y="1072" text-anchor="middle">calque</text>
    <rect x="674" y="1054" width="92" height="26" rx="5" fill="#8b3a4a"/><text x="720" y="1072" text-anchor="middle">invented</text>
    <rect x="776" y="1054" width="84" height="26" rx="5" fill="#b45309"/><text x="818" y="1072" text-anchor="middle">suspect</text>
  </g>
</svg>
"""

HOST_BRIDGE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-label="Host project and editorial workflow">
  <rect width="1280" height="720" fill="#f7f5f0"/>
  <rect x="40" y="32" width="1200" height="78" rx="12" fill="#1b2a4a"/>
  <text x="72" y="68" font-family="DejaVu Sans,sans-serif" font-size="26" font-weight="700" fill="#ffffff">How Editors &amp; Projects Use lexaudit (Standalone or Submodule)</text>
  <text x="72" y="94" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#cfe8e8">Your articles and custom brand dictionaries stay in your project folder  |  lexaudit only reads and ranks</text>

  <!-- Left Box: Project Folder -->
  <rect x="40" y="138" width="520" height="270" rx="12" fill="#ffffff" stroke="#1b2a4a" stroke-width="2.5"/>
  <rect x="40" y="138" width="520" height="48" rx="12" fill="#1b2a4a"/>
  <text x="300" y="168" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#ffffff">Your Project Folder (Articles &amp; Custom Lists)</text>

  <g font-family="DejaVu Sans,sans-serif" font-size="14" fill="#1b2a4a">
    <rect x="68" y="204" width="464" height="42" rx="6" fill="#f0f4f8" stroke="#c5cdd8"/>
    <text x="86" y="230"><tspan font-weight="700">1. Markdown / JSON content:</tspan> README.md, docs/, courses/</text>

    <rect x="68" y="256" width="464" height="42" rx="6" fill="#f0f4f8" stroke="#c5cdd8"/>
    <text x="86" y="282"><tspan font-weight="700">2. dicts/proper-names.yaml:</tspan> your brand &amp; product names</text>

    <rect x="68" y="308" width="464" height="42" rx="6" fill="#f0f4f8" stroke="#c5cdd8"/>
    <text x="86" y="334"><tspan font-weight="700">3. dicts/acronyms.yaml:</tspan> industry abbreviations</text>

    <rect x="68" y="358" width="464" height="36" rx="6" fill="#eaf6f6" stroke="#0d7377"/>
    <text x="86" y="381"><tspan font-weight="700" fill="#0d7377">4. lexaudit.config.yaml:</tspan> created automatically by "lexaudit init"</text>
  </g>

  <!-- Center Arrow -->
  <path d="M570 272 H700" stroke="#0d7377" stroke-width="4" fill="none"/>
  <polygon points="700,264 718,272 700,280" fill="#0d7377"/>
  <rect x="582" y="226" width="116" height="34" rx="6" fill="#0d7377"/>
  <text x="640" y="248" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="13" font-weight="700" fill="#ffffff">lexaudit audit</text>

  <!-- Right Box: Output Reports -->
  <rect x="720" y="138" width="520" height="270" rx="12" fill="#ffffff" stroke="#0d7377" stroke-width="2.5"/>
  <rect x="720" y="138" width="520" height="48" rx="12" fill="#0d7377"/>
  <text x="980" y="168" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#ffffff">Generated Reports (output_dir/&lt;locale&gt;/)</text>

  <g font-family="DejaVu Sans,sans-serif" font-size="14" fill="#1b2a4a">
    <rect x="748" y="204" width="464" height="48" rx="6" fill="#eaf6f6" stroke="#0d7377"/>
    <text x="766" y="233"><tspan font-weight="700" fill="#0d7377">queue.md:</tspan> ranked list of pages needing editorial review first</text>

    <rect x="748" y="264" width="464" height="48" rx="6" fill="#f0f4f8" stroke="#c5cdd8"/>
    <text x="766" y="293"><tspan font-weight="700">summary.md &amp; suspect.csv:</tspan> word counts, reasons, and file paths</text>

    <rect x="748" y="324" width="464" height="64" rx="6" fill="#f0f4f8" stroke="#c5cdd8"/>
    <text x="766" y="352"><tspan font-weight="700">report.json &amp; words.json:</tspan> machine-readable data for CI diffs</text>
    <text x="766" y="374" font-size="12" fill="#4a5568">and curated rewrite-queue tables</text>
  </g>

  <!-- Bottom Editorial Loop -->
  <rect x="40" y="440" width="1200" height="176" rx="12" fill="#ffffff" stroke="#c5cdd8" stroke-width="2"/>
  <text x="72" y="476" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#1b2a4a">3-Step Editorial Review Loop (For Human Editors or AI Rewrite Agents)</text>

  <rect x="72" y="498" width="330" height="92" rx="8" fill="#f0f4f8" stroke="#1b2a4a" stroke-width="1.5"/>
  <text x="92" y="528" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#1b2a4a">Step A. Pick Top Page in Queue</text>
  <text x="92" y="552" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">Open queue.md or run</text>
  <text x="92" y="572" font-family="DejaVu Sans,monospace" font-size="12" fill="#0d7377">lexaudit explain &lt;word&gt; --locale de</text>

  <path d="M408 544 H462" stroke="#0d7377" stroke-width="3"/><polygon points="462,537 476,544 462,551" fill="#0d7377"/>

  <rect x="480" y="498" width="330" height="92" rx="8" fill="#f0f4f8" stroke="#1b2a4a" stroke-width="1.5"/>
  <text x="500" y="528" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#1b2a4a">Step B. Rewrite or Allowlist</text>
  <text x="500" y="552" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">Fix real translation calques in prose,</text>
  <text x="500" y="572" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#4a5568">or add valid new terms to proper-names</text>

  <path d="M816 544 H870" stroke="#0d7377" stroke-width="3"/><polygon points="870,537 884,544 870,551" fill="#0d7377"/>

  <rect x="888" y="498" width="320" height="92" rx="8" fill="#eaf6f6" stroke="#0d7377" stroke-width="1.5"/>
  <text x="908" y="528" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#0d7377">Step C. Re-Audit &amp; Verify</text>
  <text x="908" y="552" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">Re-run "lexaudit audit" to confirm</text>
  <text x="908" y="572" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">the page score drops to clean</text>

  <text x="640" y="662" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#4a5568">Privacy Guarantee: Your project dictionaries and articles stay in your repository and are never uploaded.</text>
</svg>
"""

BENCHMARK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720" role="img" aria-label="lexaudit 7-locale scientific ablation benchmark">
  <rect width="1280" height="720" fill="#f7f5f0"/>
  <rect x="40" y="28" width="1200" height="84" rx="12" fill="#1b2a4a"/>
  <text x="72" y="66" font-family="DejaVu Sans,sans-serif" font-size="25" font-weight="700" fill="#ffffff">Scientific Ablation Study: 42 Stratified Pages Across 7 European Languages</text>
  <text x="72" y="94" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#cfe8e8">EN, DE, ES, PL, RU, SV, UK (6 pages/language: 3 clean incl. unseen specialist jargon vs 3 defective incl. unseen neologisms)</text>

  <!-- Column A -->
  <rect x="40" y="138" width="376" height="466" rx="12" fill="#ffffff" stroke="#c5cdd8" stroke-width="2.5"/>
  <rect x="40" y="138" width="376" height="52" rx="12" fill="#8b3a4a"/>
  <text x="228" y="170" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#ffffff">A. Naive Spellchecker (Raw)</text>

  <text x="64" y="220" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#4a5568">Raw Hunspell count only (no allowlists,</text>
  <text x="64" y="240" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#4a5568">no morphology, no compound splitting)</text>

  <rect x="64" y="264" width="328" height="146" rx="8" fill="#fdf2f2" stroke="#e5b4b4"/>
  <text x="84" y="296" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#8b3a4a">MAP (Ranking Quality): 0.389</text>
  <text x="84" y="326" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#1b2a4a">- Top-2 Precision (P@2): 0.0%</text>
  <text x="84" y="354" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#1b2a4a">- Top-3 Precision (P@3): 23.8%</text>
  <text x="84" y="382" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#1b2a4a">- Calque Recall: 0.0% (0 / 33)</text>

  <text x="64" y="444" font-family="DejaVu Sans,sans-serif" font-size="14" font-weight="700" fill="#8b3a4a">Why it fails editors:</text>
  <text x="64" y="470" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Flags every brand (Garmin, Victron) and</text>
  <text x="64" y="492" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">  acronym (EPIRB, SOLAS) as an error.</text>
  <text x="64" y="518" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Clean technical articles rank #1 and #2</text>
  <text x="64" y="540" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">  in all 7 European languages.</text>
  <text x="64" y="566" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Completely misses dictionary false friends.</text>

  <!-- Column B -->
  <rect x="452" y="138" width="376" height="466" rx="12" fill="#ffffff" stroke="#3a5a8c" stroke-width="2.5"/>
  <rect x="452" y="138" width="376" height="52" rx="12" fill="#3a5a8c"/>
  <text x="640" y="170" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#ffffff">B. Dicts + Morph/Compounds</text>

  <text x="476" y="220" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#4a5568">Clears brands, DE/SV compounds &amp; RU/UK</text>
  <text x="476" y="240" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#4a5568">cases, but ranks by unweighted word count</text>

  <rect x="476" y="264" width="328" height="146" rx="8" fill="#f0f4f8" stroke="#c5cdd8"/>
  <text x="496" y="296" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#3a5a8c">MAP (Ranking Quality): 0.421</text>
  <text x="496" y="326" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#1b2a4a">- Top-2 Precision (P@2): 7.1%</text>
  <text x="496" y="354" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#1b2a4a">- Top-3 Precision (P@3): 23.8%</text>
  <text x="496" y="382" font-family="DejaVu Sans,sans-serif" font-size="15" fill="#1b2a4a">- Calque Recall: 0.0% (0 / 33)</text>

  <text x="476" y="444" font-family="DejaVu Sans,sans-serif" font-size="14" font-weight="700" fill="#3a5a8c">Why raw counts are still not enough:</text>
  <text x="476" y="470" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Eliminates ~50% of false alarms on brands</text>
  <text x="476" y="492" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">  and compound nouns.</text>
  <text x="476" y="518" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- However, 4 rare catalogue part codes on a</text>
  <text x="476" y="540" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">  clean page still outrank 1-2 real calques.</text>
  <text x="476" y="566" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Still blind to false friends ("denseness").</text>

  <!-- Column C -->
  <rect x="864" y="138" width="376" height="466" rx="12" fill="#ffffff" stroke="#0d7377" stroke-width="3"/>
  <rect x="864" y="138" width="376" height="52" rx="12" fill="#0d7377"/>
  <text x="1052" y="170" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="18" font-weight="700" fill="#ffffff">C. Full lexaudit (Weighted CPU)</text>

  <text x="888" y="220" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#4a5568">Calque rules + override_ok + context</text>
  <text x="888" y="240" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#4a5568">weights + singleton noise floor (0.1)</text>

  <rect x="888" y="264" width="328" height="156" rx="8" fill="#eaf6f6" stroke="#0d7377"/>
  <text x="908" y="294" font-family="DejaVu Sans,sans-serif" font-size="16" font-weight="700" fill="#0d7377">MAP: 0.838 (+115% vs Naive)</text>
  <text x="908" y="322" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#0d7377">- Top-2 Precision (P@2): 100.0%</text>
  <text x="908" y="348" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#1b2a4a">- Top-3 Precision (P@3): 66.7%</text>
  <text x="908" y="374" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#1b2a4a">- Known-Rule Recall: 100.0% (26/26)</text>
  <text x="908" y="398" font-family="DejaVu Sans,sans-serif" font-size="14" fill="#1b2a4a">- Open-Set Recall: 77.9% (26/33)</text>

  <text x="888" y="448" font-family="DejaVu Sans,sans-serif" font-size="14" font-weight="700" fill="#0d7377">Honest scientific boundary (P@3 = 66.7%):</text>
  <text x="888" y="474" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Known calques &amp; false friends rank #1 &amp; #2.</text>
  <text x="888" y="500" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">- Repeated unseen specialist jargon (score ~1.6)</text>
  <text x="888" y="522" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">  outranks a single unseen neologism (score 0.1)</text>
  <text x="888" y="544" font-family="DejaVu Sans,sans-serif" font-size="13" fill="#1b2a4a">  until added to dicts or triaged via LLM label.</text>

  <!-- Footer -->
  <rect x="40" y="626" width="1200" height="60" rx="10" fill="#ffffff" stroke="#c5cdd8" stroke-width="1.5"/>
  <text x="640" y="662" text-anchor="middle" font-family="DejaVu Sans,sans-serif" font-size="15" font-weight="700" fill="#1b2a4a">Total CPU Runtime (42 pages, 7 languages): 0.66 seconds (0 GPU)  |  Reproduce: uv run pytest tests/test_synthetic_benchmark.py</text>
</svg>
"""


def _svg_to_jpg(svg_path: Path, jpg_path: Path, width: int) -> None:
    from PIL import Image  # type: ignore[import-untyped]

    png_tmp = jpg_path.with_suffix(".tmp.png")
    subprocess.run(
        [
            "inkscape",
            str(svg_path),
            f"--export-width={width}",
            f"--export-filename={png_tmp}",
        ],
        check=True,
        capture_output=True,
    )
    with Image.open(png_tmp) as im:
        rgb = im.convert("RGB")
        rgb.save(jpg_path, format="JPEG", quality=94, optimize=True)
    png_tmp.unlink(missing_ok=True)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--jpg",
        action="store_true",
        help="Also rasterize JPGs under docs/images/ (gitignored; needs inkscape+Pillow)",
    )
    args = p.parse_args()

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    # overview.svg is canonical; pipeline-flow.svg kept as alias for old links.
    specs = [
        ("overview.svg", "lexaudit-overview.jpg", OVERVIEW_SVG, 1600),
        ("classify-pipeline.svg", "lexaudit-classify-pipeline.jpg", CLASSIFY_SVG, 1200),
        ("host-bridge.svg", "lexaudit-host-bridge.jpg", HOST_BRIDGE_SVG, 1600),
        ("synthetic-benchmark.svg", "lexaudit-synthetic-benchmark.jpg", BENCHMARK_SVG, 1600),
    ]
    for svg_name, jpg_name, svg_content, width in specs:
        svg_path = IMG_DIR / svg_name
        svg_path.write_text(svg_content, encoding="utf-8")
        print(f"Wrote {svg_path.name}")
        if svg_name == "overview.svg":
            alias = IMG_DIR / "pipeline-flow.svg"
            alias.write_text(svg_content, encoding="utf-8")
            print(f"Wrote {alias.name} (alias of overview)")
        if args.jpg:
            jpg_path = IMG_DIR / jpg_name
            _svg_to_jpg(svg_path, jpg_path, width=width)
            print(f"  -> {jpg_path.name} ({jpg_path.stat().st_size // 1024} KB, local only)")


if __name__ == "__main__":
    main()
