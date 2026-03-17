/**
 * LCC CLI wrapper.
 *
 * Spawns `lcc scan` as a child process, parses JSON output, and exposes
 * typed results to the rest of the extension.
 */

import { execFile } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

// ---------------------------------------------------------------------------
// Public interfaces
// ---------------------------------------------------------------------------

/** Extension-level configuration sourced from VS Code settings. */
export interface LccConfig {
  lccPath: string;
  policy: string;
  threshold: number;
}

/** Mirrors the LCC LicenseEvidence dataclass. */
export interface LicenseEvidence {
  source: string;
  license_expression: string;
  confidence: number;
  raw_data: Record<string, unknown>;
  url: string | null;
}

/** Mirrors the LCC Component dataclass. */
export interface ComponentInfo {
  type: string;
  name: string;
  version: string;
  namespace: string | null;
  path: string | null;
  metadata: Record<string, unknown>;
}

/** Mirrors the LCC ComponentFinding dataclass. */
export interface Finding {
  component: ComponentInfo;
  evidences: LicenseEvidence[];
  resolved_license: string | null;
  confidence: number;
}

/** Mirrors the LCC ScanSummary dataclass. */
export interface ScanSummary {
  component_count: number;
  violations: number;
  generated_at: string;
  duration_seconds: number;
  context: Record<string, unknown>;
}

/** Mirrors the LCC ScanReport dataclass (JSON-serialised output). */
export interface ScanResult {
  findings: Finding[];
  summary: ScanSummary;
  errors: string[];
}

/** Wraps scan outcome or error for the caller. */
export interface ScanOutcome {
  success: boolean;
  result: ScanResult | null;
  error: string | null;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Maximum time (ms) to wait for `lcc scan` before killing the process. */
const SCAN_TIMEOUT_MS = 120_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Creates a temporary file path in the OS temp directory.
 * The caller is responsible for deleting it after use.
 */
function tmpJsonPath(): string {
  const name = `lcc-scan-${Date.now()}-${Math.random().toString(36).slice(2)}.json`;
  return path.join(os.tmpdir(), name);
}

/**
 * Silently remove a file. No-op if the file does not exist.
 */
function cleanupFile(filePath: string): void {
  try {
    fs.unlinkSync(filePath);
  } catch {
    // Ignore — the file may already have been removed or never created.
  }
}

/**
 * Build the argument list for `lcc scan`.
 */
function buildArgs(
  targetPath: string,
  outputPath: string,
  config: LccConfig
): string[] {
  const args = ["scan", targetPath, "--format", "json", "--output", outputPath];

  if (config.policy) {
    args.push("--policy", config.policy);
  }

  args.push("--threshold", String(config.threshold));

  return args;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Scan a single manifest file (or the directory containing it).
 *
 * The function spawns `lcc scan <directory> --format json --output <tmp>`,
 * reads the resulting JSON, and returns a typed `ScanOutcome`.
 */
export function scanFile(
  filePath: string,
  config: LccConfig
): Promise<ScanOutcome> {
  // LCC operates on directories, so we pass the parent of the manifest file.
  const targetDir = path.dirname(filePath);
  return runScan(targetDir, config);
}

/**
 * Scan an entire workspace root.
 */
export function scanWorkspace(
  workspacePath: string,
  config: LccConfig
): Promise<ScanOutcome> {
  return runScan(workspacePath, config);
}

/**
 * Core scan implementation shared by `scanFile` and `scanWorkspace`.
 */
function runScan(
  targetPath: string,
  config: LccConfig
): Promise<ScanOutcome> {
  const outFile = tmpJsonPath();
  const args = buildArgs(targetPath, outFile, config);

  return new Promise<ScanOutcome>((resolve) => {
    execFile(
      config.lccPath,
      args,
      {
        timeout: SCAN_TIMEOUT_MS,
        maxBuffer: 10 * 1024 * 1024, // 10 MB
        cwd: targetPath,
      },
      (error, _stdout, stderr) => {
        // LCC exits with code 2 when violations are found — that is NOT an
        // error from our perspective.  We only treat non-zero codes other
        // than 2 (and spawn failures) as real errors.
        if (error) {
          const code = (error as NodeJS.ErrnoException).code;

          // `lcc` not found on PATH
          if (code === "ENOENT") {
            cleanupFile(outFile);
            resolve({
              success: false,
              result: null,
              error:
                "lcc CLI not found. Install it with: pip install license-compliance-checker",
            });
            return;
          }

          // Timeout
          if (error.killed) {
            cleanupFile(outFile);
            resolve({
              success: false,
              result: null,
              error: `lcc scan timed out after ${SCAN_TIMEOUT_MS / 1000}s`,
            });
            return;
          }

          // Exit code 2 is "violations found" — the JSON file should still
          // have been written. Fall through to the JSON-parsing logic.
          const exitCode = (error as { code?: string | number }).code;
          if (exitCode !== 2 && typeof exitCode === "number") {
            cleanupFile(outFile);
            const msg = stderr?.trim() || error.message;
            resolve({
              success: false,
              result: null,
              error: `lcc scan failed (exit ${exitCode}): ${msg}`,
            });
            return;
          }
        }

        // Read the JSON output file.
        let raw: string;
        try {
          raw = fs.readFileSync(outFile, "utf-8");
        } catch {
          cleanupFile(outFile);
          // The file might not exist if lcc crashed before writing.
          resolve({
            success: false,
            result: null,
            error:
              "lcc scan completed but no output file was produced. " +
              (stderr?.trim() || "Unknown error."),
          });
          return;
        }

        cleanupFile(outFile);

        // Parse JSON.
        let parsed: ScanResult;
        try {
          parsed = JSON.parse(raw) as ScanResult;
        } catch (parseErr) {
          resolve({
            success: false,
            result: null,
            error: `Failed to parse lcc JSON output: ${parseErr}`,
          });
          return;
        }

        resolve({ success: true, result: parsed, error: null });
      }
    );
  });
}
