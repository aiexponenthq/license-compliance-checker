/**
 * Status bar management for the LCC extension.
 *
 * Shows a shield icon with a summary of the most recent scan result.
 */

import * as vscode from "vscode";
import { ScanResult } from "./scanner";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Priority controls the position of the item in the status bar. */
const STATUS_BAR_PRIORITY = 100;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Create and return a new status bar item bound to `lcc.scanWorkspace`.
 *
 * The item starts hidden; call `updateStatusBar` to populate and show it.
 */
export function createStatusBarItem(): vscode.StatusBarItem {
  const item = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Left,
    STATUS_BAR_PRIORITY
  );
  item.command = "lcc.scanWorkspace";
  item.tooltip = "Click to scan workspace with LCC";
  item.text = "$(shield) LCC";
  item.show();
  return item;
}

/**
 * Update the status bar item to reflect the latest scan result.
 *
 * - `null` result -> initial/idle state (neutral colour).
 * - Scanning in progress -> yellow "Scanning..." text.
 * - Violations found -> red text showing the count.
 * - All clear -> green "Compliant" text.
 */
export function updateStatusBar(
  item: vscode.StatusBarItem,
  scanResult: ScanResult | null
): void {
  if (!scanResult) {
    item.text = "$(shield) LCC";
    item.backgroundColor = undefined;
    item.tooltip = "Click to scan workspace with LCC";
    return;
  }

  const violations = scanResult.summary.violations;
  const total = scanResult.summary.component_count;

  if (violations > 0) {
    item.text = `$(shield) LCC: ${violations} violation${violations === 1 ? "" : "s"}`;
    item.backgroundColor = new vscode.ThemeColor(
      "statusBarItem.errorBackground"
    );
    item.tooltip = `${violations} license violation${violations === 1 ? "" : "s"} found across ${total} component${total === 1 ? "" : "s"}. Click to re-scan.`;
  } else {
    item.text = "$(shield) LCC: Compliant";
    item.backgroundColor = undefined;
    item.tooltip = `All ${total} component${total === 1 ? "" : "s"} are compliant. Click to re-scan.`;
  }
}

/**
 * Show a transient "scanning" state in the status bar.
 */
export function showScanning(item: vscode.StatusBarItem): void {
  item.text = "$(shield) LCC: Scanning...";
  item.backgroundColor = new vscode.ThemeColor(
    "statusBarItem.warningBackground"
  );
  item.tooltip = "LCC scan in progress...";
}
