# Task List - LCC v2.0 Upgrade

## Phase 1: Foundation & Dependencies
- [x] Update `pyproject.toml` with new dependencies (`sqlalchemy`, `alembic`, `asyncpg`, `arq`, `gitpython`, `openai`) <!-- id: 0 -->
- [x] Update `environment.yml` to match `pyproject.toml` <!-- id: 1 -->
- [x] Create `src/lcc/database` package structure <!-- id: 2 -->
- [x] Create `src/lcc/worker` package structure <!-- id: 3 -->

## Phase 2: Persistence Layer (PostgreSQL + SQLAlchemy)
- [x] Implement `src/lcc/database/session.py` (Async Session Factory) <!-- id: 4 -->
- [x] Implement `src/lcc/database/models.py` (Scan, Component, etc.) <!-- id: 5 -->
- [x] Initialize Alembic and create initial migration <!-- id: 6 -->
- [x] Create `ScanRepository` implementation using SQLAlchemy <!-- id: 7 -->
- [x] Write unit tests for Database Models & Repository <!-- id: 8 -->

## Phase 3: Asynchronous Job Queue (Arq + Redis)
- [x] Implement `src/lcc/worker/tasks.py` (Scan Logic Wrapper) <!-- id: 9 -->
- [x] Implement `src/lcc/worker/worker.py` (Worker Entrypoint) <!-- id: 10 -->
- [x] Refactor `src/lcc/api/server.py` to enqueue jobs <!-- id: 11 -->
- [x] Implement Job Status Endpoint (`GET /scans/{id}`) <!-- id: 12 -->
- [x] Write unit tests for Worker Tasks <!-- id: 13 -->

## Phase 4: Security Hardening
- [x] Refactor `clone_github_repo` to use `GitPython` <!-- id: 14 -->
- [x] Implement secure temp directory context manager <!-- id: 15 -->
- [x] Write unit tests for Git operations <!-- id: 16 -->

## Phase 5: AI-Native Features (LLM Integration)
- [x] Implement `src/lcc/ai/llm_client.py` (OpenAI/Local Client) <!-- id: 17 -->
- [x] Implement `src/lcc/ai/license_analyzer.py` (Prompt Engineering) <!-- id: 18 -->
- [x] Integrate LLM Analyzer into `Scanner` fallback logic <!-- id: 19 -->
- [x] Write unit tests for LLM Client & Analyzer <!-- id: 20 -->

## Phase 6: Docker & Deployment
- [x] Update `Dockerfile` (Multi-stage, new entrypoints) <!-- id: 21 -->
- [x] Update `docker-compose.yml` (Redis, Postgres, Worker) <!-- id: 22 -->
- [x] Verify full stack startup and scan flow <!-- id: 23 -->
