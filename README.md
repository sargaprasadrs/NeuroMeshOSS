# NeuroMeshOSS

NeuroMeshOSS is an open-source, local-first AI Agent Orchestration Platform designed to build, schedule, trace, and execute autonomous multi-agent graph workflows.

Think of it as:
> **Docker + Kubernetes + LangGraph + MCP + n8n + Temporal + OpenTelemetry**
> but significantly simpler, lighter, modular, and developer-friendly.

---

## Key Core Principles

- **Modular Architecture:** Fully replaceable ports & adapters (Hexagonal Architecture).
- **Local-First, Cloud-Optional:** Out-of-the-box support for Ollama, PostgreSQL, Qdrant, and Redis Streams, but built to scale to Kubernetes, AWS/GCP, and commercial LLM APIs.
- **Model Context Protocol (MCP) Support:** Native client host support to connect models directly to tool environments.
- **Zero Vendor Lock-In:** Build with open standards and run anywhere.

---

## Architecture & System Design

The full architecture design, directory structures, service boundaries, technology evaluations, and data lifecycles can be found in the [ARCHITECTURE.md](file:///C:/Users/LOQ/Desktop/NeuroMeshOSS/ARCHITECTURE.md) file.
