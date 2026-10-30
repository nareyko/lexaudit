# lexaudit MCP (stdio)

Grew out of auditing multilingual courses and encyclopedias at
[FairHelm](https://fairhelm.com). CLI package:
[github.com/nareyko/lexaudit](https://github.com/nareyko/lexaudit).

Publish-ready metadata for the official MCP registry. The server entry point is
the Python package extra:

```bash
pip install 'lexaudit[mcp]'
# or: uvx --from 'lexaudit[mcp]' lexaudit-mcp
```

## Cursor / Claude Desktop

```json
{
  "mcpServers": {
    "lexaudit": {
      "command": "lexaudit-mcp"
    }
  }
}
```

Tools: `audit`, `explain`, `expand_needle`, `fetch_dicts`. Detection only.

## Registry artifact

`server.json` describes the PyPI package + stdio transport. Current registry
entry: `io.github.nareyko/lexaudit` (PyPI `lexaudit`).

## License

MIT package; hosted multi-tenant SaaS use is AGPL. See `docs/licensing.md`.
