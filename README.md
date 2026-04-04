# 🧠 ERP-RAG — Enterprise Intelligence Agent

> **A production-grade, multi-source RAG (Retrieval-Augmented Generation) system for enterprise ERP data.** Query across structured databases, unstructured Slack logs, and an organizational graph — all through a single conversational interface with voice support.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-Core-purple)](https://llamaindex.ai)
[![Groq](https://img.shields.io/badge/LLM-Groq%20%7C%20Kimi%20K2-orange)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## 📸 Overview

ERP-RAG is built around **NexaMedTech Solutions** — a simulated mid-size MedTech/Pharma ERP startup with 65 employees, 50+ interconnected tickets, and 120+ Slack messages across 10 channels. The system demonstrates how a modern AI agent can synthesize answers that require cross-referencing relational data, conversational logs, and org-chart relationships simultaneously.

### What it does

Ask complex questions like:
- *"Who is blocking the FDA compliance ticket and what did the DevOps team say about it in Slack?"*
- *"What are all the tickets assigned to engineers who report to the Backend Manager?"*
- *"Which critical bugs have been open for more than one sprint and who is responsible?"*

The agent intelligently routes each query to the right data source (or multiple sources simultaneously) and synthesizes a coherent answer.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (Port 8000)                  │
│                                                                   │
│  ┌─────────────┐    ┌──────────────────────────────────────┐    │
│  │  Frontend   │    │        LlamaIndex Router Engine       │    │
│  │ HTML/CSS/JS │───▶│  LLMMultiSelector (Groq Kimi K2)     │    │
│  │  (Voice UI) │    └──────┬──────┬──────┬──────────────┬──┘    │
│  └─────────────┘           │      │      │              │        │
└───────────────────────────────────────────────────────────────── ┘
                             │      │      │              │
              ┌──────────────┘      │      │              └────────────┐
              ▼                     ▼      ▼                           ▼
   ┌──────────────────┐  ┌──────────────┐ ┌──────────────┐  ┌─────────────────┐
   │   PostgreSQL     │  │  ChromaDB    │ │    Neo4j     │  │  General LLM    │
   │  (Structured)    │  │  (Vectors)   │ │   (Graph)    │  │   Knowledge     │
   │                  │  │              │ │              │  │   Fallback      │
   │  Users, Tickets  │  │  Slack Msgs  │ │  Org Chart   │  │  (Non-company   │
   │  Ticket Blockers │  │  Embeddings  │ │  Blocker     │  │   questions)    │
   │                  │  │              │ │  Chains      │  │                 │
   └──────────────────┘  └──────────────┘ └──────────────┘  └─────────────────┘
```

---

## ✨ Features

- **🔀 Multi-Source Synthesis** — `LLMMultiSelector` can query multiple databases simultaneously and synthesize a unified answer
- **🗣️ Voice Interface** — Record audio in-browser; transcribed by Groq Whisper-Large-v3 in under 200ms
- **📊 SQL Analytics** — Natural language → SQL against PostgreSQL (users, tickets, blockers)
- **🔍 Vector Search** — Semantic search across 120+ Slack messages in ChromaDB
- **🕸️ Graph Queries** — LLM-generated Cypher queries against Neo4j for org hierarchy and ticket blocker chains
- **🧠 General Knowledge Fallback** — Non-company questions answered directly from LLM knowledge
- **⚡ Rate-Limit Fallback** — Auto-switches between `moonshotai/kimi-k2` and `llama-3.3-70b-versatile` on rate limits
- **💬 Context Condensation** — Multi-turn conversation history condensed into standalone queries
- **🔍 Real-Time Reasoning Logs** — Live side panel showing every LLM call, tool selection, and source nodes
- **🐳 Fully Dockerized** — One `docker compose up` starts everything

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **AI Orchestration** | LlamaIndex Core |
| **LLM** | Groq API (Kimi K2 Instruct → Llama 3.3 70B fallback) |
| **Embeddings** | HuggingFace `all-MiniLM-L6-v2` |
| **Voice** | Groq Whisper-Large-v3 |
| **Structured DB** | PostgreSQL 15 |
| **Vector Store** | ChromaDB (persistent local) |
| **Graph DB** | Neo4j 5.26 |
| **Frontend** | Vanilla HTML/CSS/JS (Glassmorphism UI) |
| **Containerization** | Docker Compose |
| **Infra** | GCP Compute Engine (europe-west12) |

---

## 📁 Project Structure

```
erp-rag/
├── src/
│   ├── agent/
│   │   ├── router.py           # FastAPI app + LlamaIndex routing engine
│   │   └── public/             # Frontend (HTML, CSS, JS)
│   │       ├── index.html
│   │       ├── style.css
│   │       └── app.js
│   ├── ingestion/
│   │   ├── setup_dbs.py        # Load users/tickets → Postgres, messages → MongoDB
│   │   ├── embed_data.py       # Embed Slack messages → ChromaDB
│   │   └── setup_neo4j.py      # Build org graph + ticket blocker chains → Neo4j
│   └── data_generation/
│       └── generate_mock_data.py  # LLM-generated mock company data
├── data/
│   └── raw/
│       ├── users.json          # 65 NexaMedTech employees
│       ├── tickets.json        # 50+ interconnected Agile tickets
│       └── messages.json       # 120+ Slack messages across 10 channels
├── Dockerfile                  # FastAPI app container
├── docker-compose.yml          # Full stack: app + 5 database services
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
└── ingest.sh                   # Helper script for data ingestion
```

---

## 🚀 Quick Start (Local)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- A [Groq API Key](https://console.groq.com) (free tier works)

### 1. Clone & configure
```bash
git clone https://github.com/salmanranjhaa/ERP-RAG.git
cd ERP-RAG

# Create your .env file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 2. Start all databases
```bash
docker compose up -d postgres mongodb neo4j pgadmin mongo-express
# Wait ~30 seconds for health checks to pass
docker compose ps
```

### 3. Run the data ingestion pipeline
```bash
# Load Postgres + MongoDB
docker compose run --rm app python src/ingestion/setup_dbs.py

# Embed Slack messages into ChromaDB
docker compose run --rm app python src/ingestion/embed_data.py

# Build Neo4j org graph
docker compose run --rm app python src/ingestion/setup_neo4j.py
```

### 4. Build & start the app
```bash
docker compose build app
docker compose up -d app
```

### 5. Open the app
Navigate to **http://localhost:8000**

---

## ☁️ GCP Deployment

The production deployment runs on a single GCP Compute Engine VM with everything containerized.

**Infrastructure:**
- **VM**: `e2-standard-2` (2 vCPU, 8GB RAM), `europe-west12-c`
- **Zone**: europe-west12 (Turin, Italy)
- **OS**: Debian 12

**Live URLs (Production):**

| Service | URL | Credentials |
|---|---|---|
| 🤖 **ERP-RAG App** | `http://34.17.94.98:8000` | — |
| 🗄️ pgAdmin | `http://34.17.94.98:5050` | `admin@erprag.com` / `adminpassword` |
| 🍃 Mongo Express | `http://34.17.94.98:8081` | `admin` / `adminpassword` |
| 🔵 Neo4j Browser | `http://34.17.94.98:7474` | `neo4j` / `adminpassword` |

**SSH access:**
```bash
gcloud compute ssh --zone "europe-west12-c" "instance-20260403-142701" --project "iri-gemini"
```

**Useful VM commands:**
```bash
cd ~/projects/erp-rag

# Check all service status
docker compose ps

# View live app logs
docker compose logs -f app

# Restart the app after a code update
git pull origin main && docker compose build app && docker compose up -d app

# Monitor resource usage
docker stats
```

---

## ⚙️ Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Vector Store (set to /app/chroma_data for Docker)
CHROMA_PATH=/app/chroma_data

# Database URIs (use service names inside Docker, localhost outside)
POSTGRES_URI=postgresql://admin:adminpassword@postgres:5432/erp_database
MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=adminpassword
```

---

## 🗄️ Database Services

| Service | Port | Purpose |
|---|---|---|
| PostgreSQL 15 | `5432` | Structured data (users, tickets, blockers) |
| pgAdmin 4 | `5050` | Postgres web UI |
| MongoDB 6 | `27017` | Raw Slack message storage |
| Mongo Express | `8081` | MongoDB web UI |
| Neo4j 5.26 | `7474` / `7687` | Org graph + ticket blocker chains |

---

## 📡 API Reference

### `POST /chat`
Main conversational endpoint.

```json
{
  "query": "Who is blocking the compliance ticket and what's the team saying?",
  "history": [
    {"role": "user", "content": "tell me about the org structure"},
    {"role": "assistant", "content": "NexaMedTech runs a flat four-tier structure..."}
  ]
}
```

**Response:**
```json
{
  "query": "...",
  "response": "...",
  "source": "['Used SQL for ticket data', 'Used vector search for Slack context']",
  "detailed_logs": [...]
}
```

### `POST /chat/audio`
Voice query endpoint. Accepts a `.webm` audio blob.

```bash
curl -X POST http://localhost:8000/chat/audio \
  -F "audio=@recording.webm" \
  -F "history=[]"
```

### `GET /`
Serves the Glassmorphism frontend dashboard.

---

## 🏢 The Company Dataset

**NexaMedTech Solutions** — A fictional MedTech/Pharma ERP startup building automation software for J&J, Pfizer, Novartis, and Roche.

| Entity | Count |
|---|---|
| Employees | 65 |
| Departments | 9 (Engineering, QA, DevOps, Sales, HR, Finance, Product, BA, C-Suite) |
| Agile Tickets | 50+ |
| Slack Channels | 10 (`#dev-ops-alerts`, `#compliance-watch`, `#hr-confidential`, etc.) |
| Slack Messages | 120+ |

**Ticket lifecycle modelled:**
- Bugs: CS open → QA confirm → BA own → Dev fix → QA test → Reopen → Refix → Deploy
- Features: PM create → BA document → Dev build → QA validate → BA sign-off → Prod

---

## 🔧 Re-Running Data Ingestion

If you need to re-populate the databases:

```bash
# Full pipeline
docker compose run --rm app python src/ingestion/setup_dbs.py  # Postgres + MongoDB
docker compose run --rm app python src/ingestion/embed_data.py  # ChromaDB vectors
docker compose run --rm app python src/ingestion/setup_neo4j.py  # Neo4j graph

# Then restart the app to reload
docker compose restart app
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push and open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built with ❤️ using LlamaIndex, Groq, FastAPI, and Docker.*
