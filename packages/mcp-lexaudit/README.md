# lexaudit MCP (stdio)

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

`server.json` describes the PyPI package + stdio transport. Publish to the MCP
registry only after PyPI `lexaudit==0.3.0` is live (owner publish go).

## License

MIT package; hosted multi-tenant SaaS use is AGPL — see `docs/licensing.md`.
