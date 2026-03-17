# LCC — License Compliance Checker (VS Code Extension)

Inline license compliance scanning for VS Code. Scans manifest files on save
and displays diagnostics (errors, warnings, information) directly in the
editor, backed by the [License Compliance Checker](https://pypi.org/project/license-compliance-checker/) CLI.

## Features

- **Scan on save** — automatically scans recognised manifest files every time
  you save. A 300 ms debounce prevents rapid re-scans.
- **Inline diagnostics** — violations appear as red squiggly underlines,
  warnings as yellow, and informational notes for low-confidence detections.
  Each diagnostic includes the detected license, policy status, and a
  recommendation.
- **Status bar indicator** — shows a shield icon with the violation count
  (red) or "Compliant" (green). Click to trigger a full workspace scan.
- **Commands** — `LCC: Scan Workspace` and `LCC: Scan Current File` are
  available from the Command Palette.
- **Multi-root workspace support** — scans every root when you trigger
  a workspace scan.

### Supported manifest files

| Ecosystem   | Files                                                       |
|-------------|-------------------------------------------------------------|
| Python      | `requirements.txt`, `requirements/*.txt`, `setup.py`, `pyproject.toml`, `Pipfile` |
| JavaScript  | `package.json` (excludes `node_modules`)                    |
| Go          | `go.mod`                                                    |
| Rust        | `Cargo.toml`                                                |
| Ruby        | `Gemfile`                                                   |
| Java        | `pom.xml`, `build.gradle`, `build.gradle.kts`               |
| .NET        | `*.csproj`, `packages.config`                               |

## Requirements

The extension requires the `lcc` CLI to be installed and available on your
`PATH` (or configured via the `lcc.lccPath` setting).

```bash
pip install license-compliance-checker
```

Verify the installation:

```bash
lcc --version
```

## Configuration

All settings live under the `lcc.*` namespace in VS Code settings.

| Setting          | Type    | Default | Description                                             |
|------------------|---------|---------|---------------------------------------------------------|
| `lcc.enabled`    | boolean | `true`  | Enable or disable the extension entirely.               |
| `lcc.scanOnSave` | boolean | `true`  | Automatically scan manifest files when they are saved.  |
| `lcc.lccPath`    | string  | `"lcc"` | Path to the `lcc` CLI executable.                       |
| `lcc.policy`     | string  | `""`    | Policy name to apply (e.g. `permissive`, `eu-ai-act-compliance`). |
| `lcc.threshold`  | number  | `0.5`   | Confidence threshold for violations (0.0 -- 1.0).       |

## Usage

1. Open a project that contains one or more manifest files.
2. The extension activates automatically.
3. Save a manifest file — LCC scans the containing directory and reports
   findings inline.
4. Open the **Problems** pane (`Ctrl+Shift+M` / `Cmd+Shift+M`) for a
   consolidated view of all diagnostics.
5. Click the shield icon in the status bar (or run `LCC: Scan Workspace`
   from the Command Palette) to scan the full workspace.

## Development

```bash
cd vscode-extension
npm install
npm run compile    # one-shot build
npm run watch      # incremental rebuild on change
```

Press `F5` in VS Code to launch the Extension Development Host.

## Screenshots

> _Coming soon._

## License

Apache-2.0 — see the repository root [LICENSE](../LICENSE) file.
