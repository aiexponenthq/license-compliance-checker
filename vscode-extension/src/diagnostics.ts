/**
 * Diagnostic mapping — turns LCC scan findings into VS Code diagnostics
 * (squiggly underlines with severity, messages, and recommendations).
 */

import * as vscode from "vscode";
import { Finding, ScanResult } from "./scanner";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Diagnostic source label shown in the Problems pane. */
const DIAGNOSTIC_SOURCE = "LCC";

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Replace the diagnostics for `document` with entries derived from
 * `scanResult`.
 *
 * Each `ComponentFinding` is mapped to a diagnostic whose severity depends
 * on the resolved confidence and the presence of a policy decision stored
 * in the finding's evidence metadata.
 *
 * Placement: the function searches the document text for the component name
 * so the squiggly appears on the correct line.  If the name cannot be found
 * the diagnostic is attached to line 0.
 */
export function updateDiagnostics(
  document: vscode.TextDocument,
  scanResult: ScanResult,
  diagnosticCollection: vscode.DiagnosticCollection
): void {
  const diagnostics: vscode.Diagnostic[] = [];
  const text = document.getText();

  for (const finding of scanResult.findings) {
    const diag = findingToDiagnostic(finding, document, text);
    if (diag) {
      diagnostics.push(diag);
    }
  }

  diagnosticCollection.set(document.uri, diagnostics);
}

/**
 * Clear diagnostics for a single document.
 */
export function clearDiagnostics(
  uri: vscode.Uri,
  diagnosticCollection: vscode.DiagnosticCollection
): void {
  diagnosticCollection.delete(uri);
}

/**
 * Clear every diagnostic owned by the collection.
 */
export function clearAllDiagnostics(
  diagnosticCollection: vscode.DiagnosticCollection
): void {
  diagnosticCollection.clear();
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Determine the VS Code severity for a finding.
 *
 * Strategy:
 * 1. If the finding's summary context contains a policy decision with status
 *    "violation" -> Error.
 * 2. If the policy decision status is "warning" -> Warning.
 * 3. If there is no resolved license or confidence is 0 -> Warning.
 * 4. If confidence is below the "low confidence" threshold (0.5) -> Information.
 * 5. Otherwise -> Information (pass).
 */
function deriveSeverity(finding: Finding): vscode.DiagnosticSeverity {
  // Look for a policy status embedded in the evidence metadata.
  const policyStatus = extractPolicyStatus(finding);

  if (policyStatus === "violation") {
    return vscode.DiagnosticSeverity.Error;
  }
  if (policyStatus === "warning") {
    return vscode.DiagnosticSeverity.Warning;
  }

  // No explicit policy decision — fall back to heuristics.
  if (!finding.resolved_license) {
    return vscode.DiagnosticSeverity.Warning;
  }
  if (finding.confidence < 0.5) {
    return vscode.DiagnosticSeverity.Information;
  }

  return vscode.DiagnosticSeverity.Information;
}

/**
 * Extract the policy status string from a finding's evidence metadata.
 *
 * LCC stores the policy decision in `summary.context.policy.decisions`
 * keyed by component name, but the JSON reporter serialises the full
 * `ScanReport` which includes per-finding metadata.  We look in the
 * first evidence's `raw_data` for a `policy_status` key, falling back
 * to the component metadata.
 */
function extractPolicyStatus(finding: Finding): string | null {
  // Check component metadata first (LCC >= 0.12 may embed this).
  const meta = finding.component.metadata;
  if (meta && typeof meta === "object") {
    if (typeof meta["policy_status"] === "string") {
      return meta["policy_status"];
    }
    // Nested under a "policy" key.
    const policy = meta["policy"] as Record<string, unknown> | undefined;
    if (policy && typeof policy["status"] === "string") {
      return policy["status"];
    }
  }

  // Check evidence raw_data.
  for (const ev of finding.evidences) {
    if (ev.raw_data && typeof ev.raw_data["policy_status"] === "string") {
      return ev.raw_data["policy_status"];
    }
  }

  return null;
}

/**
 * Build a human-readable diagnostic message for a finding.
 */
function buildMessage(finding: Finding): string {
  const name = finding.component.name;
  const version = finding.component.version;
  const license = finding.resolved_license || "UNKNOWN";
  const confidence = (finding.confidence * 100).toFixed(0);
  const policyStatus = extractPolicyStatus(finding);

  let msg = `${name}@${version} \u2014 License: ${license}`;

  if (policyStatus) {
    msg += ` [${policyStatus.toUpperCase()}]`;
  }

  msg += ` (confidence: ${confidence}%)`;

  // Append recommendation based on severity.
  if (policyStatus === "violation") {
    msg +=
      "\nThis dependency violates your license policy. Consider replacing it or requesting an exception.";
  } else if (policyStatus === "warning") {
    msg +=
      "\nThis dependency requires manual license review before use.";
  } else if (!finding.resolved_license) {
    msg +=
      "\nLicense could not be determined. Verify the license manually.";
  } else if (finding.confidence < 0.5) {
    msg +=
      "\nLow confidence detection. Verify the license manually.";
  }

  return msg;
}

/**
 * Locate the component name inside the document text and return the line
 * range.  Falls back to line 0 column 0 if not found.
 */
function findComponentRange(
  componentName: string,
  document: vscode.TextDocument,
  text: string
): vscode.Range {
  // Search for the component name as a whole word (case-sensitive first,
  // then case-insensitive).
  let idx = text.indexOf(componentName);
  if (idx === -1) {
    // Try case-insensitive
    idx = text.toLowerCase().indexOf(componentName.toLowerCase());
  }

  if (idx !== -1) {
    const pos = document.positionAt(idx);
    return new vscode.Range(
      pos,
      document.positionAt(idx + componentName.length)
    );
  }

  // Fallback: highlight the first line entirely.
  const firstLine = document.lineAt(0);
  return firstLine.range;
}

/**
 * Convert a single LCC finding into a VS Code Diagnostic.
 */
function findingToDiagnostic(
  finding: Finding,
  document: vscode.TextDocument,
  text: string
): vscode.Diagnostic | null {
  const severity = deriveSeverity(finding);
  const message = buildMessage(finding);
  const range = findComponentRange(finding.component.name, document, text);

  const diag = new vscode.Diagnostic(range, message, severity);
  diag.source = DIAGNOSTIC_SOURCE;

  // Attach the license as a code so it appears in the Problems pane.
  diag.code = finding.resolved_license || "UNKNOWN";

  return diag;
}
