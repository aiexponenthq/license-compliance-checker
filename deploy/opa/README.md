# OPA Deployment (Phase 2)

This folder contains assets for running Open Policy Agent alongside the License Compliance Checker during Phase 2.

## Prerequisites

1. Build the policy bundle:
   ```bash
   scripts/build_policy_bundle.py --output dist/policy.bundle.tar.gz
   ```
2. Ensure Docker is available (Compose v2+).

## Running locally

```bash
cd deploy/opa
DOCKER_BUILDKIT=0 docker compose up --build
```

OPA is exposed at `http://localhost:8181`. The CLI automatically consumes it when `LCC_OPA_URL` is set (see README for details).

## Configuration

- `opa-config.yaml` configures bundle retrieval, decision logging, and status endpoints.
- `docker-compose.yml` launches a small Caddy-based bundle server plus the OPA server.
- `Caddyfile` serves the bundle from `dist/` created by the build script.

## Cleanup

```bash
docker compose down -v
```

