## DESCRIPTION

This is an asynchronous Multi-Agent E-Commerce Logistics platform.

# Autonomous Multi-Agent E-Commerce & Retail Logistics Matrix

This is a full-stack hybrid architecture for autonomous multi-agent orchestration for retail logistics operations. 
The system automates complex customer support tickets, interacts securely with enterprise relational ledgers, runs guardrail 
evaluations to mitigate hallucinations, and preserves long-term state data. It utilizes a Next.js full-stack frontend acting as a BFF
(Backend for Frontend) proxy to a Python FastAPI microservice orchestration matrix. Uses LangGraph for cyclical state
self-correction, LangChain for structural schema data tooling, and Dockerized PostgreSQL with pgvector for transactional
memory checkpointing and semantic search. Optimized for 100% private local execution using Ollama.

## 🏗️ System Architecture & Data Flow

[ Next.js Client (UI) ] ──( SSE Stream )──> [ Next.js BFF Secure Proxy Layer ]
│ (Appends X-API-Key)
▼
[ PostgresSaver Checkpoint ] <──( State )─── [ FastAPI / LangGraph Engine ]
(Long-term Session Memory)                         │
┌───────────┴───────────┐
▼                       ▼
[ Relational Tables ]    [ Local Ollama Model ]
(SQL Database Core)         (Llama 3.2 via Core)


## ⚡ Core Technical Accomplishments & Skills Showcased

### 1. Stateful Cyclical Graph Engineering (LangGraph)
*   **Cyclical Node Structures:** Implemented complex control loops allowing the graph to route execution context dynamically at runtime instead of relying on fragile linear chains.
*   **Automated Guardrail Verification:** Programmed an autonomous Critic/Inspector node that evaluates drafted agent responses before completion. If verification criteria fail, the system leverages graph cycles to route states back to generating nodes for self-correction.

### 2. Microservice Layer & Unified Security (FastAPI + BFF Pattern)
*   **Backend-for-Frontend (BFF) Architecture:** Deployed a secure routing proxy layer within Next.js to conceal microservice infrastructure and manage server-to-server validation.
*   **Token-Verified Streaming Endpoints:** Engineered a high-performance, asynchronous FastAPI pipeline that reads LangGraph node deltas and streams real-time JSON frames using Server-Sent Events (SSE).

### 3. Persistent Transactional Checkpointing (PostgreSQL & pgvector)
*   **Asynchronous Graph Checkpoint Stores:** Leveraged `AsyncPostgresSaver` pools to capture and serialize live graph memory states directly to PostgreSQL at each node increment.
*   **Multi-Turn Thread Isolation:** Engineered multi-turn conversation memory, allowing independent user sessions to pause execution, store transaction states, and seamlessly resume thread context using isolated `thread_id` headers.

### 4. Enterprise-Grade Local Inference Optimization (Ollama)
*   **Local-First Architecture:** Tailored the framework to run completely self-hosted and open-source using `llama3.2:3b` reasoning models via local Ollama ports, maintaining data privacy while eliminating reliance on costly cloud APIs.

## 🛠️ The Tech Stack Core

*   **Frontend Web App:** Next.js 15 (App Router), React, TypeScript, Tailwind CSS, Shadcn/UI
*   **AI Agent Core Framework:** LangGraph, LangChain Core, Python 3.12+ (Managed via Rust-based `uv`)
*   **Inference Management:** Ollama Client (Model Engine: `llama3.2:3b`)
*   **Database & Memory Infrastructure:** PostgreSQL 16 (Pre-bundled inside Docker Compose with native `pgvector` capability)
*   **Data Validation & Transport:** Pydantic v2, Object-Relational Mappers (SQLAlchemy), `AsyncPostgresSaver`
