# mypy: ignore-errors
"""Optional MCP server: audit / explain / expand-needle / fetch-dicts.

Install with ``pip install 'lexaudit[mcp]'`` then run ``lexaudit-mcp``.
Registry metadata: ``packages/mcp-lexaudit/server.json`` (publish with 0.3.0).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _run_audit(path: str, locale: str = "en") -> dict[str, Any]:
    from lexaudit.config import resolve_or_default_config
    from lexaudit.core.pipeline import run_locale_audit
    from lexaudit.report.ci import build_findings

    cfg = resolve_or_default_config(None)
    cfg.sources = ["files"]
    cfg.files_paths = (Path(path).resolve(),)
    words, pages, _ = run_locale_audit(cfg, locale, freeze_generated_at="1970-01-01T00:00:00Z")
    return {
        "texts": [{"path": p.path, "score": p.score} for p in pages[:20]],
        "findings": build_findings(words, locale=locale, repo_root=cfg.repo_root)[:50],
    }


def main() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("mcp package missing; install with: pip install 'lexaudit[mcp]'") from exc

    mcp = FastMCP("lexaudit")

    @mcp.tool()
    def audit(path: str, locale: str = "en") -> str:
        """Audit a file or folder; return JSON findings (detection only)."""
        return json.dumps(_run_audit(path, locale), ensure_ascii=False, indent=2)

    @mcp.tool()
    def explain(word: str, locale: str = "en") -> str:
        """Explain how a single word is classified."""
        from click.testing import CliRunner

        from lexaudit.cli.main import main as cli_main

        res = CliRunner().invoke(cli_main, ["explain", word, "--locale", locale, "--json"])
        return res.output or res.stdout or ""

    @mcp.tool()
    def expand_needle(needle: str, locale: str = "all") -> str:
        """List texts where a needle appears in prior audit reports (detection only)."""
        from click.testing import CliRunner

        from lexaudit.cli.main import main as cli_main

        res = CliRunner().invoke(
            cli_main,
            ["expand-needle", "--needle", needle, "--locale", locale, "--json"],
        )
        return res.output or res.stdout or ""

    @mcp.tool()
    def fetch_dicts(locale: str = "en") -> str:
        """Download spelling dictionaries for a locale into the user cache."""
        from lexaudit.detectors.dictfetch import cache_dir, fetch_dictionary

        stem = fetch_dictionary(locale, cache_dir())
        return str(stem)

    mcp.run()


if __name__ == "__main__":
    main()
