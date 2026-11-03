/* eslint-disable @typescript-eslint/no-require-imports */
"use strict";

/**
 * VS Code extension: shells out to lexaudit CLI.
 * No hosted service. Package a .vsix with npm run package; publish on owner go.
 */

const { spawnSync } = require("node:child_process");
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");

function runLexaudit(cli, args, cwd) {
  const res = spawnSync(cli, args, {
    cwd,
    encoding: "utf8",
    maxBuffer: 8 * 1024 * 1024,
  });
  return res;
}

function collectDiagnosticsFromFindings(findingsPath, vscode, diagnosticCollection) {
  if (!fs.existsSync(findingsPath)) {
    return 0;
  }
  const rows = JSON.parse(fs.readFileSync(findingsPath, "utf8"));
  const byFile = new Map();
  for (const row of rows) {
    const filePath = row.path;
    if (!filePath) continue;
    const list = byFile.get(filePath) || [];
    const line = typeof row.line === "number" && row.line > 0 ? row.line - 1 : 0;
    // Prefer precise 1-based columns from CLI / SARIF (start_col / end_col / column).
    const startCol1 =
      (typeof row.start_col === "number" && row.start_col > 0 && row.start_col) ||
      (typeof row.startColumn === "number" && row.startColumn > 0 && row.startColumn) ||
      (typeof row.column === "number" && row.column > 0 && row.column) ||
      0;
    const endCol1 =
      (typeof row.end_col === "number" && row.end_col > 0 && row.end_col) ||
      (typeof row.endColumn === "number" && row.endColumn > 0 && row.endColumn) ||
      0;
    const word = String(row.word || row.normalized || "");
    let startCol0;
    let endCol0;
    if (startCol1 > 0) {
      startCol0 = startCol1 - 1;
      endCol0 = endCol1 > startCol1 ? endCol1 - 1 : startCol0 + Math.max(word.length, 1);
    } else {
      // Fallback: whole line when CLI omitted columns (pre-0.4 findings).
      startCol0 = 0;
      endCol0 = 200;
    }
    const range = new vscode.Range(line, startCol0, line, endCol0);
    const msg = `${row.word || row.normalized || "?"} [${row.status || "?"}]: ${
      row.hint || row.reason || "lexaudit finding"
    }`;
    const sev =
      row.status === "calque" || row.status === "invented"
        ? vscode.DiagnosticSeverity.Error
        : vscode.DiagnosticSeverity.Warning;
    list.push(new vscode.Diagnostic(range, msg, sev));
    byFile.set(filePath, list);
  }
  diagnosticCollection.clear();
  for (const [filePath, diags] of byFile) {
    const uri = vscode.Uri.file(
      path.isAbsolute(filePath) ? filePath : path.join(vscode.workspace.rootPath || "", filePath),
    );
    diagnosticCollection.set(uri, diags);
  }
  return rows.length;
}

function activate(context) {
  const vscode = require("vscode");
  const collection = vscode.languages.createDiagnosticCollection("lexaudit");
  context.subscriptions.push(collection);

  context.subscriptions.push(
    vscode.commands.registerCommand("lexaudit.auditWorkspace", async () => {
      const folder = vscode.workspace.workspaceFolders?.[0];
      if (!folder) {
        vscode.window.showErrorMessage("lexaudit: open a workspace folder first");
        return;
      }
      const cfg = vscode.workspace.getConfiguration("lexaudit");
      const cli = cfg.get("cli") || "lexaudit";
      const locale = cfg.get("locale") || "en";
      const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "lexaudit-vsc-"));
      const configHint = path.join(folder.uri.fsPath, "lexaudit.config.yaml");
      const args = [
        "audit",
        "--path",
        folder.uri.fsPath,
        "--locale",
        locale,
        "--check",
        "--format",
        "json",
        "--no-html",
      ];
      if (fs.existsSync(configHint)) {
        args.push("--config", configHint);
      }
      const res = runLexaudit(cli, args, folder.uri.fsPath);
      const findingsCandidates = [
        path.join(folder.uri.fsPath, "tmp", "lexaudit", locale, "findings.json"),
        path.join(outDir, locale, "findings.json"),
      ];
      let findingsPath = findingsCandidates.find((p) => fs.existsSync(p));
      // JSON stdout may be the findings list when --format json
      if (!findingsPath && res.stdout && res.stdout.trim().startsWith("[")) {
        findingsPath = path.join(outDir, "findings.json");
        fs.writeFileSync(findingsPath, res.stdout, "utf8");
      }
      if (!findingsPath) {
        vscode.window.showWarningMessage(
          `lexaudit finished (exit ${res.status}). No findings.json found. stderr: ${
            (res.stderr || "").slice(0, 200)
          }`,
        );
        return;
      }
      const n = collectDiagnosticsFromFindings(findingsPath, vscode, collection);
      vscode.window.showInformationMessage(`lexaudit: ${n} findings → Problems panel`);
    }),
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("lexaudit.explainSelection", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const word = editor.document.getText(editor.selection).trim() || "";
      if (!word) {
        vscode.window.showErrorMessage("lexaudit: select a word first");
        return;
      }
      const cfg = vscode.workspace.getConfiguration("lexaudit");
      const cli = cfg.get("cli") || "lexaudit";
      const locale = cfg.get("locale") || "en";
      const res = runLexaudit(cli, ["explain", word, "--locale", locale], path.dirname(editor.document.uri.fsPath));
      const out = (res.stdout || res.stderr || "").trim() || `(exit ${res.status})`;
      vscode.window.showInformationMessage(out.slice(0, 400));
    }),
  );
}

function deactivate() {}

if (require.main === module && process.argv.includes("--smoke")) {
  function resolveCli() {
    if (process.env.LEXAUDIT_CLI) return { cli: process.env.LEXAUDIT_CLI, argsPrefix: [] };
    const which = runLexaudit("lexaudit", ["--help"], process.cwd());
    if (which.status === 0) return { cli: "lexaudit", argsPrefix: [] };
    const uv = runLexaudit("uv", ["run", "lexaudit", "--help"], path.join(__dirname, "../.."));
    if (uv.status === 0) return { cli: "uv", argsPrefix: ["run", "lexaudit"] };
    return null;
  }
  const resolved = resolveCli();
  let helpStatus = "missing";
  if (resolved) {
    const help = runLexaudit(resolved.cli, [...resolved.argsPrefix, "--help"], path.join(__dirname, "../.."));
    helpStatus = String(help.status);
  } else {
    console.error("smoke: lexaudit CLI not on PATH and uv run failed; continuing diagnostics-only");
  }
  // Offline diagnostics parser smoke (no vscode runtime required)
  const fakeVscode = {
    Range: class {
      constructor(a, b, c, d) {
        this.a = a;
        this.b = b;
        this.c = c;
        this.d = d;
      }
    },
    Uri: { file: (p) => ({ fsPath: p }) },
    DiagnosticSeverity: { Error: 0, Warning: 1 },
    Diagnostic: class {
      constructor(range, msg, sev) {
        this.range = range;
        this.msg = msg;
        this.sev = sev;
      }
    },
  };
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "lexaudit-vsc-smoke-"));
  const findingsPath = path.join(tmp, "findings.json");
  fs.writeFileSync(
    findingsPath,
    JSON.stringify([
      {
        path: path.join(tmp, "a.md"),
        line: 1,
        start_col: 5,
        end_col: 14,
        word: "denseness",
        status: "calque",
        reason: "template-calque-denseness",
        hint: "notes",
      },
    ]),
    "utf8",
  );
  const captured = [];
  const collection = {
    clear() {},
    set(_uri, diags) {
      captured.push(...diags);
    },
  };
  const n = collectDiagnosticsFromFindings(findingsPath, fakeVscode, collection);
  if (n !== 1) {
    console.error("smoke: expected 1 diagnostic, got", n);
    process.exit(1);
  }
  const range = captured[0] && captured[0].range;
  if (!range || range.b !== 4 || range.d !== 13) {
    console.error("smoke: expected Range cols 4..13 from start_col/end_col, got", range);
    process.exit(1);
  }
  console.log("smoke: extension module loads; CLI status=", helpStatus, "; diagnostics=", n);
  process.exit(0);
}

module.exports = { activate, deactivate, runLexaudit, collectDiagnosticsFromFindings };
