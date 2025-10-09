# Jenkins Integration

1. Install Jenkins and ensure Python 3.11 is available on the agents.
2. Create a pipeline job pointing to this repository and use the provided `Jenkinsfile`.
3. The pipeline installs LCC via pip and runs `lcc scan`, archiving the JSON report as an artifact.

For Freestyle jobs, add an "Execute shell" step with:
```bash
python -m pip install --upgrade pip
pip install .
lcc scan . --format json --output lcc-report.json
```
and configure the post-build action to archive `lcc-report.json`.
