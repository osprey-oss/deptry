import * as vscode from "vscode";
import * as cp from "child_process";
import * as os from "os";
import * as path from "path";
import * as fs from "fs";

// ─── Types ────────────────────────────────────────────────────────────────────

interface DeptryViolation {
  error: {
    code: string;
    message: string;
  };
  module: string;
  location: {
    file: string;
    line: number | null;
    column: number | null;
  };
}

type SeverityLabel = "error" | "warning" | "information" | "hint";

// ─── Constants ────────────────────────────────────────────────────────────────

const DIAGNOSTIC_SOURCE = "deptry";
const RULE_URLS: Record<string, string> = {
  DEP001:
    "https://deptry.com/rules-violations/#dep001-imported-but-missing-from-the-dependency-definitions",
  DEP002:
    "https://deptry.com/rules-violations/#dep002-defined-as-a-dependency-but-not-used-in-the-codebase",
  DEP003:
    "https://deptry.com/rules-violations/#dep003-imported-but-it-is-a-transitive-dependency",
  DEP004:
    "https://deptry.com/rules-violations/#dep004-imported-but-declared-as-a-dev-dependency",
  DEP005:
    "https://deptry.com/rules-violations/#dep005-defined-as-a-dependency-but-it-is-a-standard-library-module",
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

function getSeverity(code: string): vscode.DiagnosticSeverity {
  const cfg = vscode.workspace
    .getConfiguration("deptry")
    .get<Record<string, SeverityLabel>>("severityMap", {});
  const label: SeverityLabel = cfg[code] ?? "error";
  switch (label) {
    case "warning":
      return vscode.DiagnosticSeverity.Warning;
    case "information":
      return vscode.DiagnosticSeverity.Information;
    case "hint":
      return vscode.DiagnosticSeverity.Hint;
    default:
      return vscode.DiagnosticSeverity.Error;
  }
}

function getWorkspaceRoot(): string | undefined {
  const folders = vscode.workspace.workspaceFolders;
  return folders && folders.length > 0 ? folders[0].uri.fsPath : undefined;
}

/**
 * Resolve the deptry executable, in priority order:
 *  1. Explicit `deptry.executable` setting (non-default).
 *  2. bin/ of the Python interpreter VS Code has selected (Python extension API).
 *  3. Common local venv directories (.venv, venv, env).
 *  4. Plain "deptry" on PATH.
 */
async function resolveExecutable(workspaceRoot: string): Promise<string> {
  const config = vscode.workspace.getConfiguration("deptry");
  const configured: string = config.get("executable", "deptry");

  if (configured !== "deptry") {
    return configured;
  }

  // Python extension API
  const pythonInterpreter = await getActivePythonInterpreter(workspaceRoot);
  if (pythonInterpreter) {
    const candidate = path.join(path.dirname(pythonInterpreter), "deptry");
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  // Common local venv directories
  const binSubdir = process.platform === "win32" ? "Scripts" : "bin";
  for (const venvDir of [".venv", "venv", "env", ".env"]) {
    const candidate = path.join(workspaceRoot, venvDir, binSubdir, "deptry");
    if (fs.existsSync(candidate)) {
      return candidate;
    }
  }

  return "deptry";
}

/**
 * Resolve the directory argument passed to deptry.
 *
 * Defaults to "." so that deptry runs from the workspace root and picks up
 * the project's own pyproject.toml config (including [tool.deptry] excludes,
 * per_rule_ignores, etc.). This avoids false positives from scanning test
 * directories that are excluded in the project's deptry config.
 *
 * Set `deptry.rootDirectory` to override (e.g. "src" or "python").
 */
function resolveRootDirectory(workspaceRoot: string): string {
  const config = vscode.workspace.getConfiguration("deptry");
  const configured: string = config.get("rootDirectory", "");
  if (configured) {
    return path.isAbsolute(configured)
      ? configured
      : path.join(workspaceRoot, configured);
  }
  return ".";
}

async function getActivePythonInterpreter(
  workspaceRoot: string
): Promise<string | undefined> {
  // Prefer the Python extension API (ms-python.python).
  const pythonExt = vscode.extensions.getExtension("ms-python.python");
  if (pythonExt) {
    if (!pythonExt.isActive) {
      await pythonExt.activate();
    }
    // The Python extension API exposes getActiveEnvironmentPath() since 2022.
    const api = pythonExt.exports as
      | {
          environments?: {
            getActiveEnvironmentPath: (resource?: vscode.Uri) => {
              path: string;
            };
          };
        }
      | undefined;
    const envPath = api?.environments?.getActiveEnvironmentPath(
      vscode.Uri.file(workspaceRoot)
    )?.path;
    if (envPath) {
      return envPath;
    }
  }

  // Fallback: read from VS Code Python settings.
  const pythonConfig = vscode.workspace.getConfiguration(
    "python",
    vscode.Uri.file(workspaceRoot)
  );
  return (
    pythonConfig.get<string>("defaultInterpreterPath") ||
    pythonConfig.get<string>("pythonPath")
  );
}

function buildDiagnostic(
  violation: DeptryViolation,
  workspaceRoot: string
): { uri: vscode.Uri; diagnostic: vscode.Diagnostic } | null {
  const { file, line, column } = violation.location;
  const absolutePath = path.isAbsolute(file)
    ? file
    : path.join(workspaceRoot, file);
  const uri = vscode.Uri.file(absolutePath);

  // For violations with no line (e.g. DEP002 pointing at pyproject.toml),
  // pin the diagnostic to line 0, column 0.
  const startLine = line != null ? line - 1 : 0;
  const startChar = column != null ? column : 0;
  const range = new vscode.Range(startLine, startChar, startLine, startChar + 1);

  const diagnostic = new vscode.Diagnostic(
    range,
    violation.error.message,
    getSeverity(violation.error.code)
  );
  diagnostic.source = DIAGNOSTIC_SOURCE;
  diagnostic.code = {
    value: violation.error.code,
    target: vscode.Uri.parse(
      RULE_URLS[violation.error.code] ?? "https://deptry.com/rules-violations/"
    ),
  };

  return { uri, diagnostic };
}

// ─── Runner ───────────────────────────────────────────────────────────────────

async function runDeptry(
  diagnosticCollection: vscode.DiagnosticCollection,
  statusBarItem: vscode.StatusBarItem,
  outputChannel: vscode.OutputChannel
): Promise<void> {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    return;
  }

  const config = vscode.workspace.getConfiguration("deptry");
  const executable = await resolveExecutable(workspaceRoot);
  const extraArgs: string[] = config.get("args", []);
  const runRoot = resolveRootDirectory(workspaceRoot);

  // Write JSON output to a temp file so we can parse it reliably.
  const tmpFile = path.join(
    os.tmpdir(),
    `deptry-${Date.now()}-${Math.random().toString(36).slice(2)}.json`
  );

  const args = [runRoot, "--json-output", tmpFile, ...extraArgs];

  statusBarItem.text = "$(sync~spin) deptry";
  statusBarItem.tooltip = "deptry is running…";
  statusBarItem.show();

  outputChannel.appendLine(`[deptry] Running: ${executable} ${args.join(" ")}`);

  return new Promise((resolve) => {
    const proc = cp.spawn(executable, args, {
      cwd: workspaceRoot,
      env: process.env,
    });

    let stderr = "";
    proc.stderr.on("data", (chunk: Buffer) => {
      stderr += chunk.toString();
    });
    proc.stdout.on("data", (chunk: Buffer) => {
      outputChannel.append(chunk.toString());
    });

    proc.on("error", (err) => {
      statusBarItem.text = "$(error) deptry";
      statusBarItem.tooltip = `deptry failed to start: ${err.message}`;
      outputChannel.appendLine(`[deptry] Error: ${err.message}`);
      if (err.message.includes("ENOENT")) {
        vscode.window.showErrorMessage(
          `deptry: executable '${executable}' not found. ` +
            "Set deptry.executable in settings to point at your virtualenv's deptry binary."
        );
      }
      cleanup();
      resolve();
    });

    proc.on("close", (code) => {
      if (stderr) {
        outputChannel.appendLine(`[deptry] stderr: ${stderr}`);
      }
      outputChannel.appendLine(`[deptry] Exit code: ${code}`);

      // Exit code 0 → no issues, 1 → violations found. Both are normal.
      if (code !== 0 && code !== 1) {
        statusBarItem.text = "$(warning) deptry";
        statusBarItem.tooltip = `deptry exited with code ${code}. See Output panel.`;
        cleanup();
        resolve();
        return;
      }

      let violations: DeptryViolation[] = [];
      try {
        if (fs.existsSync(tmpFile)) {
          const raw = fs.readFileSync(tmpFile, "utf8");
          violations = JSON.parse(raw) as DeptryViolation[];
        }
      } catch (e) {
        outputChannel.appendLine(`[deptry] Failed to parse JSON output: ${e}`);
      }

      // Group diagnostics by file URI.
      const diagMap = new Map<string, vscode.Diagnostic[]>();
      for (const violation of violations) {
        const result = buildDiagnostic(violation, workspaceRoot);
        if (!result) continue;
        const key = result.uri.toString();
        if (!diagMap.has(key)) {
          diagMap.set(key, []);
        }
        diagMap.get(key)!.push(result.diagnostic);
      }

      diagnosticCollection.clear();
      for (const [uriStr, diags] of diagMap) {
        diagnosticCollection.set(vscode.Uri.parse(uriStr), diags);
      }

      const count = violations.length;
      if (count === 0) {
        statusBarItem.text = "$(check) deptry";
        statusBarItem.tooltip = "deptry: no dependency issues found";
      } else {
        statusBarItem.text = `$(warning) deptry: ${count} issue${count === 1 ? "" : "s"}`;
        statusBarItem.tooltip = `deptry found ${count} dependency issue${count === 1 ? "" : "s"}. Click to open Problems panel.`;
        statusBarItem.command = "workbench.actions.view.problems";
      }

      cleanup();
      resolve();
    });

    function cleanup() {
      try {
        if (fs.existsSync(tmpFile)) {
          fs.unlinkSync(tmpFile);
        }
      } catch {
        // ignore cleanup errors
      }
    }
  });
}

// ─── Activation ───────────────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext): void {
  const diagnosticCollection =
    vscode.languages.createDiagnosticCollection(DIAGNOSTIC_SOURCE);
  context.subscriptions.push(diagnosticCollection);

  const outputChannel = vscode.window.createOutputChannel("deptry");
  context.subscriptions.push(outputChannel);

  const statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    100
  );
  statusBarItem.name = "deptry";
  context.subscriptions.push(statusBarItem);

  // Debounce — avoid hammering deptry on rapid saves.
  let debounceTimer: ReturnType<typeof setTimeout> | undefined;
  function scheduleRun(delay = 500) {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      runDeptry(diagnosticCollection, statusBarItem, outputChannel);
    }, delay);
  }

  // Command: run manually.
  context.subscriptions.push(
    vscode.commands.registerCommand("deptry.run", () => {
      scheduleRun(0);
    })
  );

  // Command: clear diagnostics.
  context.subscriptions.push(
    vscode.commands.registerCommand("deptry.clearDiagnostics", () => {
      diagnosticCollection.clear();
      statusBarItem.hide();
    })
  );

  // Auto-run on Python file or pyproject.toml save.
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((doc) => {
      const runOnSave = vscode.workspace
        .getConfiguration("deptry")
        .get<boolean>("runOnSave", true);
      if (!runOnSave) return;
      if (doc.languageId === "python" || doc.fileName.endsWith(".toml")) {
        scheduleRun();
      }
    })
  );

  // Run once on activation.
  scheduleRun(1000);
}

export function deactivate(): void {
  // Subscriptions are disposed automatically.
}
