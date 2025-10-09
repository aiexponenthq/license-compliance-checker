# LCC v2.0 Verification Guide

This guide details how to verify the new LCC v2.0 architecture, including the asynchronous job queue, persistence layer, and AI features.

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- OpenAI-compatible LLM endpoint (optional, for AI features)

## 1. Build and Start Services

Use Docker Compose to build and start the entire stack (API, Worker, Postgres, Redis).

```bash
docker-compose up --build -d
```

Check the status of the services:

```bash
docker-compose ps
```

Ensure all services (`api`, `worker`, `postgres`, `redis`) are `Up`.

## 2. Verify API Health

Check the API health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response: `{"status": "ok"}`

## 3. Authentication

The API requires authentication. The default admin credentials are:
- Username: `admin`
- Password: `admin`

Get an access token:

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
echo "Token: $TOKEN"
```

## 4. Run a Scan

Submit a scan job via the API using the token. You can scan a public GitHub repository.

```bash
curl -X POST http://localhost:8000/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World",
    "project_name": "hello-world"
  }'
```

This will return a JSON response with the scan ID and status `queued`.

## 5. Check Scan Status

Monitor the scan progress using the scan ID returned in the previous step.

```bash
SCAN_ID=<your_scan_id>
curl http://localhost:8000/scans/$SCAN_ID \
  -H "Authorization: Bearer $TOKEN"
```

You should see the status change from `queued` -> `running` -> `complete`.

## 6. Verify AI Features (Optional)

To verify AI license detection, ensure you have an LLM endpoint configured.
You can set the following environment variables in `docker-compose.yml` or your `.env` file:

- `LCC_LLM_ENDPOINT`: URL to your LLM API (e.g., `http://host.docker.internal:11434/v1`)
- `LCC_LLM_MODEL`: Model name (e.g., `qwen-2.5-72b-instruct`)
- `LCC_LLM_API_KEY`: API Key (if required)

When scanning a repository with unknown licenses, check the logs of the `worker` service to see AI analysis in action:

```bash
docker-compose logs -f worker
```

## 7. Run Tests

To run the unit tests locally:

```bash
pip install .[test]
pytest
```

## Troubleshooting

- **Database Connection**: If the API fails to connect to Postgres, ensure the `postgres` service is healthy.
- **Redis Connection**: If jobs are not being picked up, check the `redis` service and `worker` logs.
- **Auth Database**: The auth database is stored in `/var/lib/lcc/auth.db` inside the container.
