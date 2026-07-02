# NeuroMeshOSS: Architecture & System Design Document

## 1. High-Level Architecture
NeuroMeshOSS is designed as a **local-first, modular, cloud-optional** Agent Orchestration Platform. It follows the principles of **Hexagonal Architecture (Ports and Adapters)** and **Domain-Driven Design (DDD)**. 

The system is split into two primary layers:
1. **Control Plane (API & Orchestrator):** Manages the definitions of workflows, agents, credentials, and state.
2. **Data & Execution Plane (Workers & Runtime):** Executes the agent nodes, manages tool execution via Model Context Protocol (MCP), runs models, and routes messages.

```
                  +---------------------------------------+
                  |           Client Interfaces           |
                  |     (Web UI / CLI / Client SDK)       |
                  +-------------------+-------------------+
                                      |
                                      | HTTP / WebSockets
                                      v
                  +---------------------------------------+
                  |             API Gateway               |
                  |     (Auth, Rate Limiter, Routing)     |
                  +-------------------+-------------------+
                                      |
                                      | HTTP / gRPC
                                      v
                  +---------------------------------------+
                  |          Control Plane API            |
                  |         (FastAPI Monolith)            |
                  +---------+-------------------+---------+
                            |                   |
               Read/Write   |                   | Publish Job
                            v                   v
                  +---------+---------+  +------+----------------+
                  |  State Store      |  |  Event/Job Queue      |
                  |  (PostgreSQL)     |  |  (Redis Streams)      |
                  +-------------------+  +------+----------------+
                                                |
                                                | Consume Job
                                                v
+-----------------------------------------------+-----------------------------------------------+
|                                     Execution Workers                                         |
|                                                                                               |
|  +-----------------------+    +-----------------------+    +-----------------------+  |
|  |     Agent Runner      |    |      Tool Executor    |    |   Workflow Engine     |  |
|  | (Local / Ollama / API)|    |  (MCP Host / Sandbox) |    |  (DAG / State Machine)|  |
|  +-----------+-----------+    +-----------+-----------+    +-----------+-----------+  |
|              |                            |                            |              |
+--------------|----------------------------|----------------------------|--------------+
               |                            |                            |
               | Embed / Search             | Store Artifacts            | Cache State
               v                            v                            v
      +--------+--------+          +--------+--------+          +--------+--------+
      |  Vector Database|          |  Object Storage |          |   Cache Layer   |
      |    (Qdrant)     |          |    (MinIO)      |          |     (Redis)     |
      +-----------------+          +-----------------+          +-----------------+
```

---

## 2. Component Diagram (ASCII)
Below is the micro-level component interaction within a single deployment node.

```
+-------------------------------------------------------------------------------------------------+
|                                           FRONTEND (Next.js)                                    |
|  +--------------------+      +--------------------+      +--------------------+                 |
|  |  Workflow Builder  |      |   Agent Registry   |      |  Execution Tracer  |                 |
|  +---------+----------+      +---------+----------+      +---------+----------+                 |
+------------|---------------------------|---------------------------|----------------------------+
             |                           |                           | API / WebSockets
             v                           v                           v
+-------------------------------------------------------------------------------------------------+
|                                     CONTROL PLANE (FastAPI)                                     |
|                                                                                               |
|  +-------------------------------------------------------------------------------------------+  |
|  |                                       REST & WS Routing                                   |  |
|  +---------+--------------------+--------------------+--------------------+-----------------+  |
|            |                    |                    |                    |                     |
|            v                    v                    v                    v                     |
|     +------------+       +------------+       +------------+       +------------+               |
|     |  Workflow  |       |   Agent    |       |   Secret   |       |  Telemetry |               |
|     |  Manager   |       |  Registry  |       |   Manager  |       |  Collector |               |
|     +-----+------+       +-----+------+       +-----+------+       +-----+------+               |
|           |                    |                    |                    |                     |
|           +--------------------+---------+----------+--------------------+                     |
|                                          |                                                      |
|                                          v                                                      |
|                             +--------------------------+                                        |
|                             | Database Access Layer    |                                        |
|                             | (SQLAlchemy Core/ORM)    |                                        |
|                             +------------+-------------+                                        |
+------------------------------------------|------------------------------------------------------+
                                           |
                                           v
+-------------------------------------------------------------------------------------------------+
|                                         PERSISTENCE LAYER                                       |
|                                                                                                 |
|   +-----------------------+   +-----------------------+   +---------------------------------+   |
|   |      PostgreSQL       |   |         Redis         |   |             Qdrant              |   |
|   | (State/Metadata/Logs) |   | (Cache & Job Queues)  |   |    (Long-Term Vector Memory)    |   |
|   +-----------------------+   +-----------------------+   +---------------------------------+   |
+-------------------------------------------^-----------------------------------------------------+
                                            |
                                            | Pop Task
                                            v
+-------------------------------------------------------------------------------------------------+
|                                    EXECUTION PLANE (Workers)                                    |
|                                                                                                 |
|   +-----------------------------------------------------------------------------------------+   |
|   |                                     Worker Daemon                                       |   |
|   |   Processes tasks off the queue; executes loops; evaluates workflow state transitions. |   |
|   +-------+-----------------------------+-----------------------------+---------------------+   |
|           |                             |                             |                         |
|           v                             v                             v                         |
|   +-------+---------------+     +-------+---------------+     +-------+---------------+         |
|   |     Agent Loop        |     |      MCP Host         |     |     Model Router      |         |
|   | Runs thought/action   |     | Connects to local /   |     | Matches prompts to    |         |
|   | feedback loops.       |     | remote MCP servers.   |     | optimal model paths.  |         |
|   +-------+---------------+     +-------+---------------+     +-------+---------------+         |
|           |                             |                             |                         |
|           +-----------------------------+-----------------------------+                         |
|                                         |                                                       |
|                                         v                                                       |
|                     +---------------------------------------+                                   |
|                     |        Sandbox / LLM Providers        |                                   |
|                     |   (Ollama / OpenAI / Anthropic)       |                                   |
|                     +---------------------------------------+                                   |
+-------------------------------------------------------------------------------------------------+
```

---

## 3. Folder Structure
The repository is organized as a monorepo to enable local-first compilation and modular builds.

```
neuromesh/
├── .github/
│   └── workflows/              # CI/CD Workflows (lint, test, publish)
├── docker/
│   ├── Dockerfile.backend      # Multi-stage production build for FastAPI/Worker
│   ├── Dockerfile.frontend     # Static/SSR container for Next.js
│   └── docker-compose.yml      # Local development and single-node deploy
├── backend/                    # Python Backend
│   ├── pyproject.toml          # Poetry package config
│   ├── alembic.ini             # DB migrations config
│   ├── alembic/                # Migration scripts
│   ├── scripts/                # Utility & setup scripts
│   └── src/
│       ├── main.py             # FastAPI entrypoint
│       ├── config/             # Pydantic Settings
│       ├── core/               # Enterprise Domain (DDD)
│       │   ├── entities/       # Pure domain models (Agent, Workflow, Run, Step)
│       │   ├── exceptions/     # Domain-specific exceptions
│       │   └── interfaces/     # Repository/Service contracts (Ports)
│       ├── services/           # Application Use Cases
│       │   ├── workflow_engine.py
│       │   ├── agent_runtime.py
│       │   ├── mcp_client.py
│       │   └── secret_vault.py
│       ├── adapters/           # Infrastructure Implementations (Adapters)
│       │   ├── database/       # SQLAlchemy models and repositories
│       │   ├── cache/          # Redis Cache implementation
│       │   ├── queue/          # Redis Streams engine
│       │   ├── vector/         # Qdrant client driver
│       │   └── storage/        # MinIO/S3 file driver
│       ├── api/                # API Routing & Controllers (REST/GraphQL/WS)
│       │   ├── v1/
│       │   │   ├── agents.py
│       │   │   ├── workflows.py
│       │   │   └── telemetry.py
│       │   ├── websockets/     # Realtime state stream handlers
│       │   └── middleware/     # Auth, Rate limiting, OpenTelemetry tracking
│       └── workers/            # Worker processes entrypoint
│           ├── daemon.py       # Loop consuming Redis Streams
│           └── tasks/          # Execution logic per task type
├── frontend/                   # Next.js Dashboard
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── src/
│   │   ├── app/                # Next.js App Router (pages & layouts)
│   │   ├── components/         # Design system (Node UI, Flow UI, Log Viewers)
│   │   ├── hooks/              # WebSocket listeners & React Query hooks
│   │   └── lib/                # API Clients & Typescript contracts
├── cli/                        # Python CLI Tool
│   ├── pyproject.toml
│   └── src/
│       ├── main.py             # Click/Typer entrypoint
│       └── commands/           # Deploy, run, status, register
├── sdk/                        # SDKs for external app integrations
│   ├── python/
│   └── typescript/
└── plugins/                    # Native Plugin Extensions
    ├── sdk.py                  # Plugin development kit
    └── examples/               # Example integrations (Slack, Github, Jira)
```

---

## 4. Service Responsibilities

### Control Plane API (FastAPI)
- **Agent Registry:** Stores agent schemas, parameters, prompts, tools, and required environment configurations.
- **Workflow Orchestrator:** Manages Directed Acyclic Graphs (DAGs) and cyclic state graphs. Validates graph structures before deployment.
- **State Store Repository:** Direct write interface to PostgreSQL for long-term audit logs, definitions, and secrets metadata.
- **WebSocket Gateway:** Publishes real-time workflow state changes to listening browser sessions (Dashboard) or CLI instances.

### Execution Plane Worker
- **Queue Consumer:** Polls Redis Streams using Consumer Groups. Ensures exactly-once/at-least-once message processing.
- **Workflow Engine:** Evaluates graph nodes, determines next execution paths, updates context state, and saves checkpoint frames.
- **Agent Runner:** Resolves prompt templates, compiles active memory contexts, and communicates with LLM providers (Ollama/OpenAI compatible APIs).
- **MCP Client Host:** Orchestrates external tools. Spawns sandboxed subprocesses or handles WebSocket/SSE connections to MCP (Model Context Protocol) servers.
- **Task Evaluator:** Executes custom code snippets or pre-built integrations in isolated sandbox workers.

---

## 5. Data Flow

### Ingestion Flow (Definition to Run)
1. **Definition:** Dashboard POSTs Workflow (JSON graph representation) -> API validates using Pydantic -> Stores in Postgres.
2. **Trigger:** Trigger event (Webhook/Schedule/Manual) -> API creates a `Run` record with state `PENDING` in Postgres.
3. **Queueing:** API pushes a run execution token to the Redis Stream `workflow_jobs`.
4. **Execution:** Worker pops the token -> Instantiates execution context from Postgres -> Begins graph step loop.

```
[Dashboard/CLI] -> (REST API) -> [PostgreSQL (Saved Graph & Run Context)]
                                        |
                                        v
[Redis Stream "workflow_jobs"] <--- (Push Trigger Token)
      |
      v (Worker Consumer Group Pop)
[Execution Worker]
```

### Retrieval Flow (Traces & Metrics)
1. **Logs & Metrics:** As the worker executes tasks, it emits events via OpenTelemetry hooks.
2. **Aggregation:** OpenTelemetry Collector gathers traces and pushes them to Prometheus (metrics) and Tempo/Jaeger (traces).
3. **Real-time:** The worker publishes execution frames to Redis Pub/Sub. The API Gateway subscribes and forwards them via WebSockets to the Dashboard.

```
[Worker Executing Node]
  ├── (OTel SDK) ------> [OTel Collector] ------> [Prometheus / Grafana]
  └── (Redis Pub/Sub) -> [API WebSocket Server] -> [Next.js UI (Trace visualization)]
```

---

## 6. Request Lifecycle

```
[Client]                [API Gateway]            [Control API]            [Redis Queue]            [Worker]
   |                           |                       |                        |                     |
   |-- POST /workflows/run --->|                       |                        |                     |
   |                           |-- Authenticate ------>|                        |                     |
   |                           |-- Rate Limit -------->|                        |                     |
   |                           |                       |-- Validate Graph ----->|                     |
   |                           |                       |-- Create Run (DB) ---->|                     |
   |                           |                       |-- Push Run Task ------>|                     |
   |                           |                       |                        |-- Job Queued ------>|
   |                           |<-- 202 Accepted ------|                        |                     |
   |<-- Run ID (202) ----------|                       |                        |                     |
   |                           |                       |                        |                     |
   |                           |                       |                        |-- Pop Task -------->|
   |                           |                       |                        |                     |-- Execute Nodes
   |                           |                       |                        |                     |-- Update Checkpoint (DB)
   |                           |                       |                        |                     |-- Publish WS State
   |                           |<-- WebSocket Event --------------------------------------------------|
   |<-- Run Update (WS) -------|                       |                        |                     |
```

1. **Client Action:** Client triggers workflow execution.
2. **Gateway Verification:** API Gateway checks client token, tracks rate limit status via Redis counters, and rejects or passes the payload.
3. **Persist State:** Control API accepts JSON, generates a unique UUID `run_id`, writes the initial run structure, execution checkpoint, and status `QUEUED` to PostgreSQL.
4. **Enqueue Job:** API pushes `run_id` and metadata token to Redis Streams.
5. **Acknowledge Client:** API returns HTTP `202 Accepted` immediately along with the `run_id` to prevent socket hanging.
6. **Task Extraction:** Background worker consumes the stream. It loads the run's metadata from PostgreSQL.
7. **Node Pipeline:** The worker executes the active node, routes prompts to LLM (Ollama or API), invokes tools, updates the Postgres checkpoint, writes trace variables, and publishes completion updates.
8. **Real-Time Notification:** Updates published to Redis Pub/Sub are consumed by the API websocket server and pushed down to the UI.

---

## 7. Event Lifecycle
Events are categorized into System Events (system-wide orchestration) and Agent-to-Agent Messages.

```
               [Redis Pub/Sub] <------- Publish Message -------- [Agent A]
                      |
                      v (Event router)
               [Agent Registry]
                      |
        +-------------+-------------+
        | Routing Decision          |
        |                           |
        |---> Direct (Queue) ------>| [Agent B (Redis Stream)]
        |                           |
        |---> Webhook ------------->| [External Server]
        |                           |
        |---> Human-in-the-Loop ---->| [Postgres Blocked State -> WS Notification]
```

### Stage 1: Publish
- When an agent completes its execution step, it publishes an event containing a standard payload schema:
  ```json
  {
    "event_id": "evt_987654321",
    "parent_run_id": "run_12345",
    "source_agent": "agent_researcher",
    "target_channel": "agent_writer",
    "payload": {
      "data": "Compiled summary of quantum computing news."
    },
    "timestamp": "2026-07-02T12:30:00Z"
  }
  ```

### Stage 2: Routing
- The router parses the event from the shared Redis Streams pipeline.
- It consults the Active State Graph in PostgreSQL to see if the recipient requires dynamic model routing or if a human approval step must block execution.

### Stage 3: Dynamic Interventions
- If the routing target is a **Human Approval Node**:
  1. The run execution is paused.
  2. The state is updated to `AWAITING_APPROVAL`.
  3. A notification is dispatched via WebSockets.
  4. The job is marked as "parked" in Redis Streams.
  5. Upon human button click (POST to API), the worker restarts execution, picking up from the saved state checkpoint.

---

## 8. Module Dependency Graph
This diagram showcases compile-time and runtime dependency boundaries. The **Core Domain** has zero external dependencies (strictly enforcing Hexagonal boundaries).

```
          +----------------------------------------------+
          |                 Adapters                     |
          |  (DB, Redis Queue, MinIO, OTel, Qdrant Client)|
          +----------------------+-----------------------+
                                 |
                                 | Implements interfaces of
                                 v
          +----------------------------------------------+
          |                   Core                       |
          |  (Entity Schemas, Abstract Repository, Ports)|
          +----------------------^-----------------------+
                                 |
                                 | Imports definitions from
                                 |
          +----------------------+-----------------------+
          |                 Services                     |
          |  (Workflow Engine, Agent Runner, Sandbox)    |
          +----------------------^-----------------------+
                                 |
                                 | Uses use-cases in
                                 |
          +----------------------+-----------------------+
          |                 API Layer                    |
          |        (FastAPI Controllers & Routes)        |
          +----------------------------------------------+
```

---

## 9. Database Overview
We employ PostgreSQL for relations, complex indexes, and audit logs. Qdrant is used for vector embedding indices.

```
                    +-------------------+
                    |      Users        |
                    +-------------------+
                    | PK id (UUID)      |
                    |    email          |
                    |    password_hash  |
                    +---------+---------+
                              | 1
                              |
                              | 0..*
                    +---------v---------+
                    |    Workflows      |
                    +-------------------+
                    | PK id (UUID)      |
                    | FK user_id        |
                    |    name           |
                    |    definition     | (JSONB: Nodes, Edges)
                    |    is_active      |
                    |    version        |
                    +---------+---------+
                              | 1
                              |
                              | 0..*
                    +---------v---------+
                    |      Runs         |
                    +-------------------+
                    | PK id (UUID)      |
                    | FK workflow_id    |
                    |    status         | (ENUM: Pending, Running, Success, Paused, Error)
                    |    current_state  | (JSONB: Active Variables)
                    |    created_at     |
                    +---------+---------+
                              | 1
                              |
                              | 0..*
                    +---------v---------+
                    |    RunSteps       |
                    +-------------------+
                    | PK id (UUID)      |
                    | FK run_id         |
                    |    node_id        |
                    |    input          | (JSONB)
                    |    output         | (JSONB)
                    |    traces         | (JSONB)
                    |    duration_ms    |
                    +-------------------+
```

### Table Definitions & JSONB Schemas
- **Workflows Table (`definition` column):** Holds the visual editor DAG configurations. Expressed in JSONB:
  ```json
  {
    "nodes": [
      {"id": "node_1", "type": "agent", "data": {"agent_id": "agent_llama_8b"}},
      {"id": "node_2", "type": "tool", "data": {"tool_name": "web_search"}}
    ],
    "edges": [
      {"source": "node_1", "target": "node_2", "condition": "needs_search"}
    ]
  }
  ```
- **Secrets Management:** Secrets are stored in the PostgreSQL database in an encrypted field (using AES-GCM-256 with key rotation). In cloud deployments, the adapters will map this interface to GCP Secret Manager or HashiCorp Vault.

---

## 10. Technology Decisions with Justification

### Queue Engine: Redis Streams vs. RabbitMQ
We selected **Redis Streams** as our primary message broker.

| Feature / Metric | Redis Streams (Selected) | RabbitMQ (Alternative) |
| :--- | :--- | :--- |
| **Operational Complexity** | Very Low. Uses the same Redis instance used for cache. | High. Requires separate Erlang VM, clustering configurations, and node managers. |
| **Local-first Footprint** | ~5MB memory footprint. Native execution. | ~100MB+ memory footprint. Slower startup times. |
| **Delivery Guarantees** | At-least-once. Consumer groups track offsets, ACK, and pending queues. | At-least-once / Exactly-once with cluster sync. |
| **Scalability** | Capable of 100k+ operations/sec on single core. | Excellent throughput, complex routing topologies. |
| **Developer DX** | Extremely simple CLI inspections (`XREADGROUP`, `XLEN`). | Requires AMQP libraries, exchange-queue binding knowledge. |

**Justification:** 
Because NeuroMeshOSS prioritizes a **local-first** developer workflow that runs effortlessly on a laptop (using Ollama and docker-compose), forcing developers to host RabbitMQ adds unnecessary footprint. Since we already require Redis for session state, rate limiting, and short-term caching, Redis Streams provides a robust, native message queue structure with Consumer Groups without introducing secondary service architectures. 

### Database: PostgreSQL vs. MongoDB
We selected **PostgreSQL** with the JSONB datatype.
- **Justification:** Graph states and workflows require ACID compliance. A workflow execution node failure must rollback variables safely to prevent corrupted run states. PostgreSQL provides robust transactional reliability combined with the flexibility of document databases (JSONB) for unstructured dynamic step outputs and agent telemetry payload storage.

### Vector DB: Qdrant vs. pgvector
We selected **Qdrant** as our dedicated vector engine.
- **Justification:** While `pgvector` makes local setups simple, scaling production AI search needs advanced indexing parameters (HNSW), fast filtering based on dynamic metadata namespaces, payload storage optimizations, and real-time visualization of vectors. Qdrant has a low memory footprint (Rust-based) and is highly optimized for production operations.

---

## 11. Scalability Considerations
1. **Stateless API Gateway & Control Plane:** The FastAPI servers carry no state. They can be scaled horizontally behind an ingress controller (Nginx/HAProxy/Envoy) dynamically.
2. **Worker Pool Auto-scaling:** Workers only connect via TCP to Redis and Postgres. We can scale execution workers horizontally based on the queue depth:
   $$\text{Queue Latency} = \frac{\text{Unacknowledged Messages in Stream}}{\text{Number of Active Workers}}$$
   When the queue depth exceeds a threshold, the Kubernetes Horizontal Pod Autoscaler (HPA) triggers new worker containers.
3. **Partitioning database tables:** In high-throughput settings, `RunSteps` and `Telemetry` logs are partitioned by month or tenant ID, preventing primary index degradation.

---

## 12. Security Considerations
- **Agent Sandbox Execution:** Tools and native custom-code scripts can execute malicious payloads. To prevent this, tool executors execute in:
  1. *Local:* Isolated gRPC micro-containers or localized subprocess structures using limited execution permissions.
  2. *Production:* MicroVM sandboxes (e.g., AWS Firecracker or gVisor container runtimes).
- **Model Context Protocol (MCP) isolation:** Every MCP server is initialized as an isolated subprocess with strict environment isolation, preventing directory traversal attacks.
- **Encryption-at-Rest:** System configurations, LLM API keys, and workflow secrets are encrypted in PostgreSQL using Fernet-based AES-256 tokens. Encryption keys are sourced strictly from OS Environment variables (loaded via Docker/K8s Secrets).

---

## 13. Future Roadmap
1. **WASM-based Plugin Sandboxing:** Enable execution of untrusted third-party marketplace plugins inside WebAssembly sandboxes directly inside the Python engine.
2. **Local Embedding / Re-ranking Acceleration:** Integrate direct Rust/C binding runtimes for embedding computation within the worker engine to eliminate the network latency of external endpoints.
3. **Native LangChain/LangGraph Import Utility:** Tooling to ingest existing codebases and automatically map class loops into NeuroMesh visual graph definitions.

---

## 14. Known Risks & Mitigations
- **State Serialization Overhead:** Because graph checkpoints are saved to PostgreSQL as JSONB on every node transition, rapid loops could create heavy write bottlenecks.
  - *Mitigation:* Employ write-behind caching via Redis. Worker commits state to Redis immediately, and a background thread flushes blocks to PostgreSQL asynchronously every 500ms.
- **Local Memory Resource Contention:** Running heavy LLMs locally (e.g. Llama 3 70B via Ollama) along with PostgreSQL, Qdrant, MinIO, Redis, and Python workers will cause resource thrashing on developer laptops.
  - *Mitigation:* Ensure default configurations target low-footprint models (e.g., Phi-3, Llama 3 8B, Qwen 2.5) and provide immediate toggles to route to remote cloud APIs (Groq, Together.ai, OpenAI) seamlessly.

---

## 15. Alternative Architectures Considered
- **Temporal-Only State Machine:** We considered using Temporal for managing workflow cycles. However, Temporal requires high infrastructure complexity (custom schemas, Cassandra/Postgres, Elasticsearch, Temporal Server container clusters). This goes against the "Simpler, Modular, Local-first" principle.
- **Distributed Microservices Engine:** Separating the agent runtime, workflow execution, tool router, and MCP manager into individual microservices. This was rejected because the network overhead and serialization latency between Python services would slow execution, making it complex to run on developer machines.

---

## 16. Why This Design is Superior
This architecture achieves the optimal balance between **operational simplicity** for local development and **production durability**:
- **It is highly cohesive yet loosely coupled:** Hexagonal architecture isolates core business rules from infrastructure choices (e.g., we can swap Qdrant for pgvector, or Redis Streams for RabbitMQ simply by changing config adapters).
- **Fast developer onboarding:** A developer can launch the entire stack using `docker compose up` in less than 60 seconds with no cloud credentials required.
- **No Vendor Lock-in:** The system uses standard, open-source building blocks (Ollama, PostgreSQL, Redis, Qdrant, OpenTelemetry) ensuring it can run on-premise, on a local machine, or inside any cloud Kubernetes engine without code modifications.
