# NeuroMeshOSS

NeuroMeshOSS is an open-source, local-first AI Agent Orchestration Platform designed to build, schedule, trace, and execute autonomous multi-agent graph workflows.

Think of it as:
> **Docker + Kubernetes + LangGraph + MCP + n8n + Temporal + OpenTelemetry**
> but significantly simpler, lighter, modular, and developer-friendly.

[![CI Status](https://github.com/sargaprasadrs/NeuroMeshOSS/actions/workflows/ci.yml/badge.svg)(https://github.com/sargaprasadrs/NeuroMeshOSS/actions)
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

- Python 3.12+ and [Poetry](https://python-poetry.org/)
- Node.js 20+ and NPM
- Docker and Docker Compose (optional for local databases)

### 1. Initialize Workspace

Clone the repository and run the setup make target:
```bash
make init
```
This installs backend dependencies, CLI requirements, SDK tools, and frontend libraries.

### 2. Configure Settings

Create your local `.env` configuration file from the template:
```bash
poetry run neuromesh init
```
*(Optionally populate any model provider API keys inside `.env`)*

### 3. Launch Local Infrastructure

Start the local databases, queues, and object storage:
```bash
make dev-infra
```
This starts PostgreSQL, Redis, Qdrant, and MinIO containers.

### 4. Seed the Database

Populate database schemas with the default admin user and the sample "Market Analyzer Agent Flow":
```bash
cd backend && poetry run python scripts/seed.py
```

### 5. Start the Services

Start the Control Plane API:
```bash
poetry run neuromesh serve
```

In a separate terminal, launch the execution worker daemon:
```bash
poetry run neuromesh worker
```

Open [http://localhost:3000](http://localhost:3000) to view the Next.js workspace dashboard.

---

## Testing & Checks

Execute formatting and pytest suites:
```bash
# Run all tests
make test

# Check formatting and types
make lint

# Auto-format codebase
make format
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
