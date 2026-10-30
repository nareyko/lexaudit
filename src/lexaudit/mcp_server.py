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


def build_mcp() -> Any:
    """Construct FastMCP app with tools registered (no network)."""
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

    return mcp


def list_tool_names(mcp: Any | None = None) -> list[str]:
    """Return registered tool names for unit smoke (no LLM / no network)."""
    app = mcp if mcp is not None else build_mcp()
    tools = getattr(app, "_tool_manager", None)
    if tools is not None and hasattr(tools, "list_tools"):
        listed = tools.list_tools()
        names = []
        for t in listed:
            name = getattr(t, "name", None) or (t.get("name") if isinstance(t, dict) else None)
            if name:
                names.append(str(name))
        if names:
            return sorted(names)
    # FastMCP variants expose tools differently across versions.
    for attr in ("_tools", "tools"):
        bag = getattr(app, attr, None)
        if isinstance(bag, dict):
            return sorted(str(k) for k in bag)
    return []


def main() -> None:
    mcp = build_mcp()
    mcp.run()


if __name__ == "__main__":
    main()
