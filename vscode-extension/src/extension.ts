/**
 * LCC VS Code Extension — main entry point.
 *
 * Activates when a workspace contains recognised manifest files and
 * provides:
 *   - Scan-on-save with inline diagnostics.
 *   - "LCC: Scan Workspace" and "LCC: Scan Current File" commands.
 *   - A status bar item showing violation counts.
 */

import * as vscode from "vscode";
import { isManifestFile } from "./manifest";
import {
  type LccConfig,
  type ScanResult,
  scanFile,
  scanWorkspace,
} from "./scanner";
import {
  clearAllDiagnostics,
  clearDiagnostics,
  updateDiagnostics,
} from "./diagnostics";
import {
  createStatusBarItem,
  showScanning,
  updateStatusBar,
} from "./statusbar";

// ---------------------------------------------------------------------------
// Module-level state
// ---------------------------------------------------------------------------

let diagnosticCollection: vscode.DiagnosticCollection;
let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;

/** Debounce timer handle for scan-on-save. */
let debounceTimer: ReturnType<typeof setTimeout> | undefined;

/** Tracks whether a scan is already in flight to avoid stacking. */
let scanInFlight = false;

/** The most recent scan result, used for status bar rendering. */
let lastScanResult: ScanResult | null = null;

// ---------------------------------------------------------------------------
// Activation / Deactivation
// ---------------------------------------------------------------------------

export function activate(context: vscode.ExtensionContext): void {
  outputChannel = vscode.window.createOutputChannel("LCC");
  diagnosticCollection =
    vscode.languages.createDiagnosticCollection("lcc");
  statusBarItem = createStatusBarItem();

  context.subscriptions.push(
    outputChannel,
    diagnosticCollection,
    statusBarItem
  );

  // ---- Commands ----
  context.subscriptions.push(
    vscode.commands.registerCommand("lcc.scanWorkspace", () =>
      commandScanWorkspace()
    )
  );
  context.subscriptions.push(
    vscode.commands.registerCommand("lcc.scanCurrentFile", () =>
      commandScanCurrentFile()
    )
  );

  // ---- Scan on save ----
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((doc) => onDocumentSaved(doc))
  );

  // ---- Clean up diagnostics when a file is closed ----
  context.subscriptions.push(
    vscode.workspace.onDidCloseTextDocument((doc) => {
      clearDiagnostics(doc.uri, diagnosticCollection);
    })
  );

  log("LCC extension activated.");
}

export function deactivate(): void {
  if (debounceTimer !== undefined) {
    clearTimeout(debounceTimer);
    debounceTimer = undefined;
  }
  // Disposables registered via context.subscriptions are cleaned up
  // automatically by VS Code, but we clear our module state just in case.
  lastScanResult = null;
}

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

function getConfig(): LccConfig {
  const cfg = vscode.workspace.getConfiguration("lcc");
  return {
    lccPath: cfg.get<string>("lccPath", "lcc"),
    policy: cfg.get<string>("policy", ""),
    threshold: cfg.get<number>("threshold", 0.5),
  };
}

function isEnabled(): boolean {
  return vscode.workspace.getConfiguration("lcc").get<boolean>("enabled", true);
}

function isScanOnSaveEnabled(): boolean {
  return vscode.workspace
    .getConfiguration("lcc")
    .get<boolean>("scanOnSave", true);
}

// ---------------------------------------------------------------------------
// Save handler (with debounce)
// ---------------------------------------------------------------------------

function onDocumentSaved(document: vscode.TextDocument): void {
  if (!isEnabled() || !isScanOnSaveEnabled()) {
    return;
  }

  const filePath = document.uri.fsPath;
  if (!isManifestFile(filePath)) {
    return;
  }

  // Debounce: reset the timer on each save so rapid successive saves do
  // not queue multiple scans.
  if (debounceTimer !== undefined) {
    clearTimeout(debounceTimer);
  }

  debounceTimer = setTimeout(() => {
    debounceTimer = undefined;
    void runFileScan(document);
  }, 300);
}

// ---------------------------------------------------------------------------
// Scan runners
// ---------------------------------------------------------------------------

async function runFileScan(document: vscode.TextDocument): Promise<void> {
  if (scanInFlight) {
    log("Scan already in progress, skipping.");
    return;
  }

  const config = getConfig();
  const filePath = document.uri.fsPath;

  scanInFlight = true;
  showScanning(statusBarItem);
  log(`Scanning file: ${filePath}`);

  try {
    const outcome = await scanFile(filePath, config);
    if (!outcome.success || !outcome.result) {
      handleScanError(outcome.error);
      return;
    }

    lastScanResult = outcome.result;
    updateDiagnostics(document, outcome.result, diagnosticCollection);
    updateStatusBar(statusBarItem, outcome.result);
    logScanSummary(outcome.result);
  } catch (err) {
    handleUnexpectedError(err);
  } finally {
    scanInFlight = false;
  }
}

async function commandScanCurrentFile(): Promise<void> {
  if (!isEnabled()) {
    vscode.window.showWarningMessage("LCC is disabled. Enable it in settings.");
    return;
  }

  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active editor.");
    return;
  }

  const filePath = editor.document.uri.fsPath;
  if (!isManifestFile(filePath)) {
    vscode.window.showInformationMessage(
      "The current file is not a recognised manifest file."
    );
    return;
  }

  await runFileScan(editor.document);
}

async function commandScanWorkspace(): Promise<void> {
  if (!isEnabled()) {
    vscode.window.showWarningMessage("LCC is disabled. Enable it in settings.");
    return;
  }

  const folders = vscode.workspace.workspaceFolders;
  if (!folders || folders.length === 0) {
    vscode.window.showWarningMessage("No workspace folder open.");
    return;
  }

  if (scanInFlight) {
    vscode.window.showInformationMessage("A scan is already in progress.");
    return;
  }

  const config = getConfig();
  scanInFlight = true;
  showScanning(statusBarItem);
  clearAllDiagnostics(diagnosticCollection);

  try {
    // Scan each workspace root (supports multi-root workspaces).
    let aggregated: ScanResult | null = null;

    for (const folder of folders) {
      log(`Scanning workspace folder: ${folder.uri.fsPath}`);
      const outcome = await scanWorkspace(folder.uri.fsPath, config);

      if (!outcome.success || !outcome.result) {
        handleScanError(outcome.error);
        continue;
      }

      if (!aggregated) {
        aggregated = outcome.result;
      } else {
        // Merge findings and errors from additional roots.
        aggregated.findings.push(...outcome.result.findings);
        aggregated.errors.push(...outcome.result.errors);
        aggregated.summary.component_count +=
          outcome.result.summary.component_count;
        aggregated.summary.violations +=
          outcome.result.summary.violations;
      }
    }

    if (aggregated) {
      lastScanResult = aggregated;
      updateStatusBar(statusBarItem, aggregated);
      logScanSummary(aggregated);

      // Map findings back to open documents for inline diagnostics.
      applyDiagnosticsToOpenEditors(aggregated);

      const v = aggregated.summary.violations;
      const c = aggregated.summary.component_count;
      if (v > 0) {
        vscode.window.showWarningMessage(
          `LCC: ${v} violation${v === 1 ? "" : "s"} found across ${c} component${c === 1 ? "" : "s"}.`
        );
      } else {
        vscode.window.showInformationMessage(
          `LCC: All ${c} component${c === 1 ? "" : "s"} are compliant.`
        );
      }
    }
  } catch (err) {
    handleUnexpectedError(err);
  } finally {
    scanInFlight = false;
  }
}

// ---------------------------------------------------------------------------
// Diagnostics helpers
// ---------------------------------------------------------------------------

/**
 * After a workspace-wide scan, push diagnostics into every open editor
 * whose document matches a manifest file.
 */
function applyDiagnosticsToOpenEditors(scanResult: ScanResult): void {
  for (const editor of vscode.window.visibleTextEditors) {
    const doc = editor.document;
    if (isManifestFile(doc.uri.fsPath)) {
      updateDiagnostics(doc, scanResult, diagnosticCollection);
    }
  }
}

// ---------------------------------------------------------------------------
// Error handling
// ---------------------------------------------------------------------------

function handleScanError(errorMessage: string | null): void {
  const msg = errorMessage || "Unknown scan error.";
  log(`Scan error: ${msg}`);

  if (msg.includes("not found") || msg.includes("ENOENT")) {
    vscode.window
      .showErrorMessage(
        "lcc CLI not found. Install it with: pip install license-compliance-checker",
        "Copy Install Command"
      )
      .then((selection) => {
        if (selection === "Copy Install Command") {
          vscode.env.clipboard.writeText(
            "pip install license-compliance-checker"
          );
          vscode.window.showInformationMessage(
            "Install command copied to clipboard."
          );
        }
      });
  } else {
    vscode.window.showErrorMessage(`LCC scan failed: ${msg}`);
  }

  updateStatusBar(statusBarItem, null);
}

function handleUnexpectedError(err: unknown): void {
  const msg =
    err instanceof Error ? err.message : String(err);
  log(`Unexpected error: ${msg}`);
  vscode.window.showErrorMessage(`LCC: unexpected error — ${msg}`);
  updateStatusBar(statusBarItem, null);
}

// ---------------------------------------------------------------------------
// Logging
// ---------------------------------------------------------------------------

function log(message: string): void {
  const ts = new Date().toISOString();
  outputChannel.appendLine(`[${ts}] ${message}`);
}

function logScanSummary(result: ScanResult): void {
  const s = result.summary;
  log(
    `Scan complete: ${s.component_count} components, ${s.violations} violations, ` +
      `${s.duration_seconds.toFixed(1)}s`
  );
  if (result.errors.length > 0) {
    log(`Scan errors: ${result.errors.join("; ")}`);
  }
}
