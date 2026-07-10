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

AEM orchestrates diverse AI agents, manages persistent memory, dynamically routes LLM requests based on cost/latency/quality metrics, caches semantic responses, and integrates natively with enterprise systems like GitHub, Jira, and Slack—all while providing full telemetry and observability out of the box.

---

## ✨ Full Capabilities & Features

### 🤖 1. Multi-Agent Orchestration (LangGraph)
AEM is built on a directed acyclic graph (DAG) architecture for multi-agent workflows, enabling advanced reasoning and distributed execution.
- **Supervisor Agent:** Acts as the entry point, interpreting the user's intent and routing tasks dynamically to specialized sub-agents.
- **Planning Agent:** Decomposes complex user requests into step-by-step executable sub-tasks, ensuring parallel processing where possible.
- **Knowledge Agent:** Handles sophisticated document ingestion, metadata extraction, and precise RAG querying.
- **Analytics Agent:** Processes raw data, codebase metrics, and structured information to derive enterprise intelligence.
- **CEO Agent:** Synthesizes the final output from multiple agent sub-tasks into a cohesive, executive-level summary.
- **Reflection Engine:** Built-in self-correction logic that validates agent outputs against constraints and automatically replans upon failure.

### 🧠 2. Intelligent LLM Gateway & Dynamic Routing
A true production-grade LLM router that acts as an abstraction layer between agents and foundation models.
- **Supported Providers:** Amazon Bedrock, Anthropic, OpenRouter, Google Gemini, and OpenAI.
- **Dynamic Scoring & Routing:** Evaluates providers in real-time based on `latency`, `cost`, `quality`, and `health`. It routes complex tasks to high-reasoning models and simpler tasks to faster, cheaper models.
- **Failover & Resilience:** Automatic retry logic with exponential backoff. Seamless failover to backup models if a provider is rate-limited or offline.
- **Provider Policies:** Admins can force preferred providers (e.g., exclusively Bedrock) via `.env` overrides to ensure compliance and control costs.

### 🔍 3. Hybrid Retrieval-Augmented Generation (RAG)
Advanced document ingestion and search capabilities powered by Qdrant and advanced embedding models.
- **Hybrid Search Engine:** Combines dense vector search (Semantic intent) with sparse vector search (BM25/Keyword) for maximum recall and accuracy.
- **Cross-Encoder Reranking:** Re-ranks initial search results using a cross-encoder model to surface the most contextually relevant chunks before passing them to the LLM.
- **Enterprise Scale Ingestion:** Handles complex multi-page PDF ingestion, intelligent semantic chunking, and metadata tagging to preserve document hierarchy.

### ⚡ 4. Semantic Caching
Dramatically reduces LLM API costs and execution latency by intercepting duplicate or highly similar queries.
- **Redis-Backed Vector Cache:** Stores previous queries and their exact responses.
- **Semantic Matching:** If a new query is semantically similar to a cached query (e.g., above a 0.95 similarity threshold), AEM returns the cached response instantly without invoking the LLM.

### 🔌 5. Enterprise Connectors & Tooling
AEM agents are fully autonomous and empowered to take action across your enterprise systems through a robust integration framework.
- **GitHub Integration:** Natively connects to GitHub to index repositories, search code, analyze issues/PRs, and even review code.
- **Jira & Slack Support:** Built-in connector interfaces designed to query ticket statuses, update issue trackers, and broadcast alerts to Slack channels.
- **Live Connector Health:** The UI automatically polls all integrations in the background, displaying real-time connection status (Healthy, Degraded, Disconnected).
- **Extensible Architecture:** Adding internal API connectors takes minutes using the abstract Connector Base Class.

### 📊 6. Full Observability & Interactive UI
A comprehensive Streamlit frontend provides total visibility into the system's inner workings.
- **Chat Interface:** Interact with the multi-agent system with real-time streaming, chat history, and conversation persistence.
- **Execution Tracing:** View exact traces of which agents ran, how long they took, and what sub-tasks failed or succeeded in a beautiful expanding UI.
- **Metrics Dashboard:** View real-time token usage, latency per turn, cost estimation, and model selection decisions.
- **Source Citations:** Automatically displays exactly which documents or systems the agent used to formulate its response.

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

- **Backend:** Python 3.11, FastAPI, LangGraph, Pydantic V2, SQLAlchemy, Uvicorn.
- **Frontend:** Streamlit.
- **Infrastructure:** Docker, Docker Compose, UV Package Manager.
- **Databases:** 
  - **PostgreSQL:** Transactional state, conversational memory, workflow checkpoints.
  - **Redis:** Semantic caching, task brokering, and rate-limiting.
  - **Qdrant:** High-performance vector database for Hybrid RAG.
- **AI/ML:** HuggingFace `sentence-transformers`, BGE Cross-Encoders, AWS Bedrock, OpenAI, Anthropic.

---

## 💻 Installation & Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (if running locally without Docker)
- UV Package Manager
- API Keys (AWS Bedrock, Gemini, OpenRouter, etc.)

### 1. Clone & Configure
```bash
git clone https://github.com/vaibhavdubey06/autonomous-enterprise-manager.git
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

*Alternatively, run services locally:*
```bash
uv sync
uv run uvicorn main:app --app-dir apps/backend --reload --port 8000
uv run streamlit run apps/frontend/app.py
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
│   │   │   ├── core/        # Config, Dependencies, Setup
│   │   │   ├── services/    # LLM Router, Semantic Cache, RAG, GitHub integration
│   │   │   └── api/         # FastAPI REST Routers
│   │   └── .env             # Backend Environment Variables
│   └── frontend/
│       ├── app.py           # Streamlit Entrypoint
│       ├── components/      # UI Components (Sidebar, Chat, Upload)
│       └── pages/           # Streamlit Pages (Integrations, Analytics, Operations)
├── tests/                   # Extensive Unit and E2E Testing Suite
├── .github/                 # CI/CD Workflows for automated deployments and testing
├── docker-compose.yml       # Full stack container orchestration
└── README.md
```

---

## 🤝 Contributing
We welcome contributions! Please open an issue to discuss major architectural changes before submitting a Pull Request. Be sure to run `uv run pytest tests/` before submitting to ensure your changes pass the quality gates.

## 📜 License
This project is licensed under the MIT License.
