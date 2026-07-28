# NeuroMeshOSS

NeuroMeshOSS is an open-source, local-first AI Agent Orchestration Platform designed to build, schedule, trace, and execute autonomous multi-agent graph workflows.

Think of it as:
> **Docker + Kubernetes + LangGraph + MCP + n8n + Temporal + OpenTelemetry**
> but significantly simpler, lighter, modular, and developer-friendly.

[![CI Status](https://github.com/sargaprasadrs/NeuroMeshOSS/actions/workflows/ci.yml/badge.svg)](https://github.com/sargaprasadrs/NeuroMeshOSS/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)

---

## Core Characteristics

* **Modular Architecture:** Bounded domain entities decoupled from core infrastructures via ports & adapters (Hexagonal Architecture).
* **Local-First, Cloud-Optional:** Native integration with local models (Ollama) and lightweight local queues (Redis Streams), designed to scale up to Kubernetes.
* **Model Context Protocol (MCP) Support:** Open standards client host resolving tool environments dynamically.
* **Telemetry by Design:** Native trace outputs instrumented with OpenTelemetry APIs.

---

## Repository Structure

The monorepo is organized as follows:

```
neuromesh/
├── .github/                    # GitHub actions CI pipeline & community templates
├── docker/                     # Docker configurations (FastAPI and Next.js)
├── backend/                    # Python FastAPI control plane & worker daemon
│   ├── src/
│   │   ├── core/               # DDD Core Entities & Port interfaces
│   │   ├── adapters/           # Databases, queues, and telemetry drivers
│   │   ├── services/           # Application use-case layers
│   │   └── api/                # REST endpoints and WebSocket gates
│   └── tests/                  # Pytest unit and integration check suite
├── cli/                        # Click/Typer command line utility
├── sdk/                        # Python and TypeScript integration SDK libraries
├── frontend/                   # Next.js workspace dashboard UI
├── Makefile                    # Dev builds coordination task runner
└── docker-compose.yml          # Local Postgres, Redis, Qdrant, and MinIO stack
```

---

## Getting Started

### Prerequisites

- **Python 3.11+** and [Poetry](https://python-poetry.org/) (v2.0+)
- **Node.js 20+** and npm
- **Docker Desktop** with Docker Compose v2 (optional, for local databases)
- **Windows:** The project supports Windows via `start-app.bat`

### Quick Start (Windows)

Double-click `start-app.bat` or run it from the terminal:
```batch
start-app.bat
```

### Manual Setup (Cross-Platform)

#### 1. Initialize Workspace

Install all dependencies (backend, CLI, SDK, frontend):
```bash
make init
```

Or install individually:
```bash
cd backend && poetry install
cd cli && poetry install
cd sdk/python && poetry install
cd frontend && npm install
```

#### 2. Configure Environment

Copy the template and adjust as needed:
```bash
cp .env.example .env
```

Key settings to review in `.env`:
| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://neuromesh:...@localhost:5432/neuromesh_db` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis for queue + cache |
| `JWT_SECRET_KEY` | auto-generated in production | JWT signing secret (min 32 chars) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:3000` | Frontend URLs allowed for CORS |

#### 3. Launch Infrastructure

Start PostgreSQL, Redis, Qdrant, and MinIO:
```bash
docker compose up -d
```

Verify all containers are healthy:
```bash
docker ps
```
Expected output shows 4 containers: `neuromesh-postgres`, `neuromesh-redis`, `neuromesh-qdrant`, `neuromesh-minio`.

> **Troubleshooting:** If Docker Desktop isn't running, launch it from the Start Menu first and wait 30-60 seconds for the daemon to initialize.

#### 4. Seed the Database

Create tables and populate with default data:
```bash
cd backend && poetry run python scripts/seed.py
```

This creates:
- **Default admin user:** `admin@neuromesh.com` / `admin_secure_password_123`
- **Sample workflow:** "Market Analyzer Agent Flow" (4-node DAG)

The script auto-creates database tables if they don't exist, so no manual migration step is needed.

#### 5. Start the Backend API

```bash
cd backend
poetry run uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify the API is running:
```bash
curl http://127.0.0.1:8000/healthz/live
# → {"status":"alive"}

curl http://127.0.0.1:8000/healthz/ready
# → {"status":"ready","database":"up","queue":"up"}
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) for the interactive Swagger documentation.

#### 6. Start the Execution Worker (Optional)

In a separate terminal, run the worker daemon that processes workflow jobs from Redis:
```bash
cd backend
poetry run python src/workers/daemon.py
```

#### 7. Start the Frontend Dashboard

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

---

## Quick Health Check

Once all services are running, verify everything:

| Service | URL | Expected Response |
|---|---|---|
| Backend API | `http://localhost:8000/healthz/live` | `{"status":"alive"}` |
| Swagger Docs | `http://localhost:8000/docs` | Swagger UI |
| Frontend | `http://localhost:3000` | Dashboard UI |
| PostgreSQL | `docker exec neuromesh-postgres pg_isready -U neuromesh` | `accepting connections` |
| Redis | `docker exec neuromesh-redis redis-cli ping` | `PONG` |

---

## Testing & Checks

```bash
# Run all backend tests
make test
# Or individually:
cd backend && poetry run pytest

# Run specific test file
cd backend && poetry run pytest tests/test_workflow_engine.py -v

# Check formatting and types
make lint

# Auto-format codebase
make format
```

---

## Known Fixes & Gotchas

The following issues were discovered and fixed during initial setup:

### ✅ OpenTelemetry Middleware Ordering
**Issue:** `FastAPIInstrumentor.instrument_app()` tried to add middleware in the `lifespan` event (after app start), causing `RuntimeError: Cannot add middleware after an application has started`.

**Fix:** Moved `setup_telemetry(app)` from the `lifespan` function to `create_app()` before returning the app.

### ✅ Seed Script Table Creation
**Issue:** The `scripts/seed.py` tried to query the `users` table which didn't exist yet, causing `UndefinedTableError`.

**Fix:** Added `Base.metadata.create_all()` at the start of the seed script to auto-create tables.

### ✅ Seed Script Module Path
**Issue:** Running `python scripts/seed.py` directly resulted in `ModuleNotFoundError: No module named 'src'`.

**Fix:** Added `sys.path.insert(0, ...)` to the seed script for direct execution. Alternatively, use `PYTHONPATH=. poetry run python scripts/seed.py`.

### ⚠️ Docker Compose `version` Attribute
**Issue:** Docker Compose v2 shows a deprecation warning about the obsolete `version: '3.8'` attribute.

**Status:** The attribute has been removed (it's ignored by Compose v2 anyway).

### ⚠️ Pydantic V2 Deprecation Warnings
**Issue:** Core entity classes use the old Pydantic V1 `class Config` syntax (triggering deprecation warnings).

**Status:** These are non-blocking warnings. Migrate to `model_config = ConfigDict(...)` when convenient.

---

## Project Structure

```
neuromesh/
├── backend/           # Python FastAPI control plane & worker
│   ├── src/
│   │   ├── core/      # Domain entities & port interfaces
│   │   ├── adapters/  # DB, queue, telemetry implementations
│   │   ├── services/  # Workflow engine, auth, MCP client
│   │   ├── api/       # REST endpoints & WebSocket gates
│   │   └── workers/   # Background daemon processes
│   └── tests/         # Pytest test suite
├── frontend/          # Next.js dashboard UI
├── cli/               # Python CLI tool
├── sdk/               # Python & TypeScript SDKs
├── plugins/           # Native plugin extensions
└── docker/            # Docker build configurations
```

---

## Production Security Hardening

To safeguard deployment configurations, NeuroMeshOSS implements built-in defenses by default:
* **Path Traversal Shielding:** Filesystem tool providers block relative escapes (using `os.path.commonpath`). File reads are bound within active workspace folders.
* **SSRF Mitigation:** The Model Context Protocol (MCP) HTTP client blocks private loopback or metadata subnets (e.g. `127.0.0.1`, `169.254.169.254`), preventing unauthorized intranet probing.
* **Password Hashing:** User passwords are encrypted with bcrypt and validate standard length complexity (minimum 8 characters).

---

## Running Diagnostics

If you encounter issues during local-first setup, use the diagnostic command:
```bash
poetry run neuromesh doctor
```
This runs connection checks against PostgreSQL, Redis streams, and checks for active Ollama and MCP configurations.

---

## Documentation & Community

Full design documents and guides are available at:
* **System Architecture & Decision Log:** [ARCHITECTURE.md](file:///C:/Users/LOQ/Desktop/NeuroMeshOSS/ARCHITECTURE.md)
* **Contributing Guidelines:** [CONTRIBUTING.md](file:///C:/Users/LOQ/Desktop/NeuroMeshOSS/CONTRIBUTING.md)
* **Security & Vulnerabilities:** [SECURITY.md](file:///C:/Users/LOQ/Desktop/NeuroMeshOSS/SECURITY.md)

---

## License

NeuroMeshOSS is licensed under the [MIT License](LICENSE).
