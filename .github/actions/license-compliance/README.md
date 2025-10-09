# License Compliance Checker Action

Composite GitHub Action that installs LCC and runs a scan.

## Inputs
- `path`: project path to scan (default: `.`)
- `format`: output format (`json`, `markdown`, `html`, `csv`)
- `policy`: optional policy name/file
- `output`: report file path (default `lcc-report.json`)
- `threshold`: confidence threshold (default `0.5`)

## Outputs
- `report`: path to the generated report

## Example
```yaml
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/license-compliance
    with:
      path: .
      format: json
```
