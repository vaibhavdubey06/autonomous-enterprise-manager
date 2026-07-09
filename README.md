<div align="center">
  <h1>Autonomous Enterprise Manager (AEM)</h1>
  <p><strong>The Production-Grade Enterprise AI Operating System</strong></p>
  <p>
    <a href="#overview">Overview</a> •
    <a href="#core-capabilities">Core Capabilities</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#tech-stack">Tech Stack</a> •
    <a href="#installation--quick-start">Installation</a>
  </p>
</div>

---

## 🚀 Overview

The **Autonomous Enterprise Manager (AEM)** is a resilient, scalable, and fully observable Enterprise AI Operating System. Moving beyond isolated chat scripts, AEM provides a highly concurrent multi-agent architecture designed to execute complex, long-running workflows securely.

AEM orchestrates diverse AI agents, manages persistent memory, dynamically routes LLM requests based on cost/latency/quality metrics, caches semantic responses, and integrates natively with enterprise systems like GitHub—all while providing full telemetry and observability out of the box.

---

## ✨ Core Capabilities

### 1. Multi-Agent Orchestration (LangGraph)
AEM is built on a directed acyclic graph (DAG) architecture for multi-agent workflows. 
- **Supervisor Agent:** Acts as the entry point, routing tasks dynamically.
- **Planning Agent:** Decomposes complex user requests into executable sub-tasks.
- **Knowledge Agent:** Handles document ingestion and RAG querying.
- **Analytics Agent:** Processes data, code, and structured information.
- **CEO Agent:** Synthesizes the final output from multiple agent sub-tasks.
- **Reflection Engine:** Built-in self-correction logic that validates outputs and replans upon failure.

### 2. Intelligent LLM Gateway & Routing
A production-grade LLM router that dynamically selects the best provider for each task.
- **Supported Providers:** AWS Bedrock, Anthropic, OpenRouter, Google Gemini, OpenAI.
- **Dynamic Scoring:** Evaluates providers in real-time based on `latency`, `cost`, `quality`, and `health`.
- **Failover & Resilience:** Automatic retry logic and seamless failover to backup models if a provider is rate-limited or offline.
- **Provider Policies:** Force preferred providers (e.g., Bedrock) via `.env` overrides.

### 3. Hybrid Retrieval-Augmented Generation (RAG)
Advanced document ingestion and search capabilities powered by Qdrant.
- **Hybrid Search:** Combines dense vector search (Semantic) with sparse vector search (BM25/Keyword) for maximum recall.
- **Cross-Encoder Reranking:** Re-ranks initial search results using a cross-encoder model to surface the most contextually relevant chunks.
- **Enterprise Scale:** Handles complex multi-page PDF ingestion and intelligent chunking.

### 4. Semantic Caching
Dramatically reduces LLM API costs and latency.
- **Redis-Backed:** Stores previous queries and responses.
- **Semantic Matching:** If a new query is semantically similar to a cached query (e.g., above a 0.95 similarity threshold), AEM returns the cached response instantly without invoking the LLM.

### 5. Enterprise Connectors & Tooling
AEM agents are empowered to take action across enterprise systems.
- **GitHub Integration:** Natively connects to GitHub to index repositories, search code, and analyze issues/PRs.
- **Extensible Architecture:** Designed to easily add Jira, Slack, and internal API connectors.

### 6. Full Observability & UI
A comprehensive Streamlit frontend provides total visibility into the system.
- **Chat Interface:** Interact with the multi-agent system with real-time streaming.
- **Execution Tracing:** View exact traces of which agents ran, how long they took, and what sub-tasks failed or succeeded.
- **Integration Health:** Real-time dashboard showing the status of backend connections and third-party APIs.

---

## 🏗️ Architecture

```text
                        +---------------------------------------+
                        |        Streamlit User Interface       |
                        |    (Chat, Observability, Dashboard)   |
                        +---------------------------------------+
                                           |
                                   [ REST API ]
                                           |
                        +---------------------------------------+
                        |          Enterprise Runtime           |
                        |   (FastAPI, Checkpointing, State)     |
                        +---------------------------------------+
                                           |
                        +---------------------------------------+
                        |          Supervisor Graph             |
                        |      (LangGraph State Machine)        |
                        +---------------------------------------+
                          /                |                 \ 
      +--------------------+      +--------------------+      +--------------------+
      |  Decision Engine   |      |  LLM Gateway       |      | Reflection Engine  |
      | (Planner/Subtasks) |      | (Dynamic Router)   |      | (Validation/Eval)  |
      +--------------------+      +--------------------+      +--------------------+
               |                           |                           |
        +--------------+           +--------------+             +--------------+
        |  PostgreSQL  |           |Semantic Cache|             |  Connectors  |
        |  (Memory)    |           |   (Redis)    |             |   (GitHub)   |
        +--------------+           +--------------+             +--------------+
               |                           
        +--------------+           
        | Hybrid RAG   |           
        |  (Qdrant)    |           
        +--------------+           
```

---

## 🛠️ Tech Stack

- **Backend:** Python 3.11, FastAPI, LangGraph, Pydantic, SQLAlchemy.
- **Frontend:** Streamlit.
- **Infrastructure:** Docker, Docker Compose.
- **Databases:** 
  - **PostgreSQL:** Transactional state, conversational memory, collaboration sessions.
  - **Redis:** Semantic caching and message brokering.
  - **Qdrant:** High-performance vector database for Hybrid RAG.
- **AI/ML:** HuggingFace `sentence-transformers`, BGE Cross-Encoders, AWS Bedrock.

---

## 💻 Installation & Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- API Keys (AWS Bedrock, Gemini, OpenRouter, etc.)

### 1. Clone & Configure
```bash
git clone https://github.com/your-org/autonomous-enterprise-manager.git
cd autonomous-enterprise-manager
cp apps/backend/.env.example apps/backend/.env
```
*Edit `apps/backend/.env` with your API keys and preferred LLM provider.*

### 2. Start Infrastructure
Launch the necessary databases (Postgres, Redis, Qdrant):
```bash
docker compose up -d aem-postgres aem-redis aem-qdrant
```

### 3. Start Application Services
Launch the FastAPI backend and Streamlit frontend:
```bash
docker compose up -d aem-backend aem-frontend
```

### 4. Access the Application
- **Frontend UI:** [http://localhost:8501](http://localhost:8501)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📂 Repository Structure

```text
autonomous-enterprise-manager/
├── apps/
│   ├── backend/
│   │   ├── app/
│   │   │   ├── agents/      # LangGraph Agents (Supervisor, Planner, Knowledge, etc.)
│   │   │   ├── core/        # Config, Dependencies
│   │   │   ├── services/    # LLM Router, Semantic Cache, RAG, GitHub integration
│   │   │   └── api/         # FastAPI Routers
│   │   └── .env             # Backend Environment Variables
│   └── frontend/
│       ├── app.py           # Streamlit Entrypoint
│       ├── components/      # UI Components (Sidebar, Chat, Upload)
│       └── pages/           # Streamlit Pages (Integrations, GitHub, etc.)
├── docker-compose.yml       # Full stack container orchestration
└── README.md
```

---

## 🤝 Contributing
We welcome contributions! Please open an issue to discuss major architectural changes before submitting a Pull Request.

## 📜 License
This project is licensed under the MIT License.
