/**
 * Manifest file detection and ecosystem mapping.
 *
 * Maps manifest filenames/patterns to their respective package ecosystems
 * so the extension knows which files to scan on save.
 */

import * as path from "path";

/** Ecosystem identifier returned by LCC. */
export type Ecosystem =
  | "python"
  | "javascript"
  | "go"
  | "rust"
  | "ruby"
  | "java"
  | "dotnet";

/**
 * Each entry maps a filename (or basename glob) to an ecosystem.
 * The `exclude` field lists path segments that should cause the file to be
 * skipped (e.g. node_modules for package.json).
 */
interface ManifestPattern {
  /** Exact basename or a simple glob understood by the matcher below. */
  pattern: string;
  ecosystem: Ecosystem;
  /** Path segments that disqualify the file (checked case-insensitively). */
  exclude?: string[];
}

const MANIFEST_PATTERNS: ManifestPattern[] = [
  // Python
  { pattern: "requirements.txt", ecosystem: "python" },
  { pattern: "setup.py", ecosystem: "python" },
  { pattern: "pyproject.toml", ecosystem: "python" },
  { pattern: "Pipfile", ecosystem: "python" },

  // JavaScript / Node
  {
    pattern: "package.json",
    ecosystem: "javascript",
    exclude: ["node_modules"],
  },

  // Go
  { pattern: "go.mod", ecosystem: "go" },

  // Rust
  { pattern: "Cargo.toml", ecosystem: "rust" },

  // Ruby
  { pattern: "Gemfile", ecosystem: "ruby" },

  // Java / JVM
  { pattern: "pom.xml", ecosystem: "java" },
  { pattern: "build.gradle", ecosystem: "java" },
  { pattern: "build.gradle.kts", ecosystem: "java" },

  // .NET
  { pattern: "packages.config", ecosystem: "dotnet" },
];

/**
 * Checks whether a file path matches a known manifest pattern by its basename,
 * with special handling for:
 *   - `requirements/*.txt` (Python requirements split into sub-files)
 *   - `*.csproj` (.NET project files)
 *   - exclusion of paths containing `node_modules`
 */
export function isManifestFile(filePath: string): boolean {
  return getEcosystem(filePath) !== undefined;
}

/**
 * Returns the ecosystem string for a manifest file, or `undefined` if the
 * file is not a recognised manifest.
 */
export function getEcosystem(filePath: string): Ecosystem | undefined {
  const normalised = filePath.replace(/\\/g, "/");
  const basename = path.basename(normalised);
  const lowerPath = normalised.toLowerCase();

  // --- Special-case patterns ---

  // requirements/*.txt  (e.g. requirements/dev.txt)
  if (
    basename.endsWith(".txt") &&
    /requirements\/[^/]+\.txt$/i.test(normalised)
  ) {
    return "python";
  }

  // *.csproj
  if (basename.endsWith(".csproj")) {
    return "dotnet";
  }

  // --- Table-driven exact-match on basename ---
  for (const entry of MANIFEST_PATTERNS) {
    if (basename === entry.pattern) {
      // Check exclusions
      if (entry.exclude) {
        const excluded = entry.exclude.some((seg) =>
          lowerPath.includes(`/${seg.toLowerCase()}/`)
        );
        if (excluded) {
          return undefined;
        }
      }
      return entry.ecosystem;
    }
  }

  return undefined;
}
