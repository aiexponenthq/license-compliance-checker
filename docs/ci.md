# Continuous Integration Support

## GitHub Actions
- Composite Action: `.github/actions/license-compliance`
- Workflow example: `.github/workflows/lcc-scan.yml`

## GitLab CI
- Template pipeline: `.gitlab-ci.yml` installs LCC, runs the scan, caches pip downloads, and uploads `lcc-report.json` as an artifact. Optional MR notes can be added using `glab`.

## Jenkins
- Pipeline job definition: `.jenkins/Jenkinsfile`
- Freestyle snippet in `.jenkins/README.md`

## Azure DevOps
- YAML pipeline template: `azure-pipelines.yml`

## CircleCI
- Orb definition: `.circleci/orb.yml`
- Example workflow consuming the orb: `.circleci/config.yml`

Each integration assumes `LCC_OPA_URL`, `LCC_OPA_TOKEN`, and `LCC_REDIS_URL` environment variables are populated if you intend to use advanced features (OPA evaluation, Redis caching, async queue).
