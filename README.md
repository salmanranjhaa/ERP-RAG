# ERP-RAG — Enterprise Intelligence Agent

A production-grade, multi-source RAG (Retrieval-Augmented Generation) system for enterprise ERP data. Query across structured databases, unstructured conversational logs, and an organizational graph — all through a single conversational interface with voice support.

[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)](https://fastapi.tiangolo.com)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-Core-purple)](https://llamaindex.ai)
[![Groq](https://img.shields.io/badge/LLM-Groq%20%7C%20Kimi%20K2-orange)](https://groq.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-lightgrey)](LICENSE)

---

## Overview

ERP-RAG is built around **NexaMedTech Solutions** — a simulated mid-size MedTech/Pharma ERP startup with 65 employees, 50+ interconnected tickets, and 120+ Slack messages across 10 channels. The system demonstrates how a modern AI agent can synthesize answers that require cross-referencing relational data, conversational logs, and org-chart relationships simultaneously.

Example queries it can handle:

- *"Who is blocking the FDA compliance ticket and what did the DevOps team say about it in Slack?"*
- *"What are all the tickets assigned to engineers who report to the Backend Manager?"*
- *"Which critical bugs have been open for more than one sprint and who is responsible?"*

The agent intelligently routes each query to the right data source (or multiple sources simultaneously) and synthesizes a coherent answer.

---

## Architecture

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
              ┌──────────────┘      │      │              └──────────────┐
              ▼                     ▼      ▼                             ▼
   ┌──────────────────┐  ┌──────────────┐ ┌──────────────┐  ┌────────────────┐
   │   PostgreSQL     │  │  ChromaDB    │ │    Neo4j     │  │  General LLM  │
   │  (Structured)    │  │  (Vectors)   │ │   (Graph)    │  │  Knowledge    │
   │                  │  │              │ │              │  │  Fallback     │
   │  Users, Tickets  │  │  Slack Msgs  │ │  Org Chart   │  │               │
   │  Ticket Blockers │  │  Embeddings  │ │  Blocker     │  │  General      │
   │                  │  │              │ │  Chains      │  │  questions    │
   └──────────────────┘  └──────────────┘ └──────────────┘  └────────────────┘
```

---

## Features

- **Multi-Source Synthesis** — `LLMMultiSelector` can query multiple databases simultaneously and synthesize a unified answer
- **Voice Interface** — Record audio in-browser; transcribed by Groq Whisper-Large-v3 in under 200ms
- **SQL Analytics** — Natural language to SQL against PostgreSQL (users, tickets, blockers)
- **Vector Search** — Semantic search across 120+ Slack messages in ChromaDB
- **Graph Queries** — LLM-generated Cypher queries against Neo4j for org hierarchy and ticket blocker chains
- **General Knowledge Fallback** — Non-company questions answered directly from LLM knowledge without forcing a DB lookup
- **Rate-Limit Fallback** — Auto-switches between `moonshotai/kimi-k2` and `llama-3.3-70b-versatile` on rate limits
- **Context Condensation** — Multi-turn conversation history condensed into standalone queries before routing
- **Real-Time Reasoning Logs** — Live side panel showing every LLM call, tool selection, and source nodes
- **Fully Dockerized** — One `docker compose up` starts everything

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI Orchestration | LlamaIndex Core |
| LLM | Groq API (Kimi K2 Instruct → Llama 3.3 70B fallback) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` |
| Voice | Groq Whisper-Large-v3 |
| Structured DB | PostgreSQL 15 |
| Vector Store | ChromaDB (persistent local) |
| Graph DB | Neo4j 5.26 |
| Frontend | Vanilla HTML/CSS/JS (Glassmorphism UI) |
| Containerization | Docker Compose |

---

## Project Structure

```
erp-rag/
├── src/
│   ├── agent/
│   │   ├── router.py              # FastAPI app + LlamaIndex routing engine
│   │   └── public/                # Frontend (HTML, CSS, JS)
│   ├── ingestion/
│   │   ├── setup_dbs.py           # Load users/tickets → Postgres, messages → MongoDB
│   │   ├── embed_data.py          # Embed Slack messages → ChromaDB
│   │   └── setup_neo4j.py         # Build org graph + ticket blocker chains → Neo4j
│   └── data_generation/
│       └── generate_mock_data.py  # LLM-generated mock company data
├── data/
│   └── raw/
│       ├── users.json             # 65 NexaMedTech employees
│       ├── tickets.json           # 50+ interconnected Agile tickets
│       └── messages.json          # 120+ Slack messages across 10 channels
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example                   # Environment variable template
```

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- A [Groq API Key](https://console.groq.com) (free tier is sufficient)

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/salmanranjhaa/ERP-RAG.git
cd ERP-RAG

cp .env.example .env
# Open .env and set your GROQ_API_KEY
```

### 2. Start the databases

```bash
docker compose up -d postgres mongodb neo4j pgadmin mongo-express

# Wait ~30 seconds for health checks, then verify
docker compose ps
```

### 3. Run the data ingestion pipeline

```bash
# Load structured data into Postgres and messages into MongoDB
docker compose run --rm app python src/ingestion/setup_dbs.py

# Embed Slack messages into ChromaDB for vector search
docker compose run --rm app python src/ingestion/embed_data.py

# Build the Neo4j org graph and ticket blocker chains
docker compose run --rm app python src/ingestion/setup_neo4j.py
```

### 4. Build and start the app

```bash
docker compose build app
docker compose up -d app
```

### 5. Open the app

Navigate to **http://localhost:8000**

---

## Database Admin UIs

| Service | URL | Purpose |
|---|---|---|
| pgAdmin | `http://localhost:5050` | PostgreSQL management UI |
| Mongo Express | `http://localhost:8081` | MongoDB management UI |
| Neo4j Browser | `http://localhost:7474` | Graph visualization and Cypher queries |

Credentials are configured via your `.env` file. See `.env.example` for defaults.

---

## Configuration

Copy `.env.example` to `.env` and fill in your values:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Vector store path (use /app/chroma_data inside Docker)
CHROMA_PATH=/app/chroma_data

# Database connection strings
# Use Docker service names (postgres, mongodb, neo4j) inside Docker
# Use localhost if running scripts outside of Docker
POSTGRES_URI=postgresql://admin:adminpassword@postgres:5432/erp_database
MONGO_URI=mongodb://admin:adminpassword@mongodb:27017/
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=adminpassword
```

---

## GCP Deployment

The recommended deployment approach for GCP is a single Compute Engine VM running all services via Docker Compose.

**Recommended VM spec:** `e2-standard-2` (2 vCPU, 8GB RAM), Debian 12

```bash
# SSH into your VM
gcloud compute ssh --zone "YOUR_ZONE" "YOUR_INSTANCE_NAME" --project "YOUR_PROJECT_ID"

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
sudo apt-get install -y docker-compose-plugin git

# Clone and configure
git clone https://github.com/salmanranjhaa/ERP-RAG.git
cd ERP-RAG
# Create .env with your credentials

# Start everything
docker compose up -d postgres mongodb neo4j pgadmin mongo-express
docker compose run --rm app python src/ingestion/setup_dbs.py
docker compose run --rm app python src/ingestion/embed_data.py
docker compose run --rm app python src/ingestion/setup_neo4j.py
docker compose build app && docker compose up -d app
```

Open firewall ports on GCP:
```bash
gcloud compute firewall-rules create erp-rag-ports \
  --project="YOUR_PROJECT_ID" \
  --allow="tcp:8000,tcp:5050,tcp:8081,tcp:7474" \
  --source-ranges=0.0.0.0/0
```

---

## API Reference

### `POST /chat`

Main conversational endpoint.

**Request:**
```json
{
  "query": "Who is blocking the compliance ticket and what is the team saying?",
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

Voice query endpoint. Accepts a `.webm` audio blob via multipart form.

```bash
curl -X POST http://localhost:8000/chat/audio \
  -F "audio=@recording.webm" \
  -F "history=[]"
```

---

## The Company Dataset

**NexaMedTech Solutions** — A fictional MedTech/Pharma ERP startup building compliance and automation software for enterprise pharma clients.

| Entity | Count |
|---|---|
| Employees | 65 |
| Departments | 9 (Engineering, QA, DevOps, Sales, HR, Finance, Product, BA, C-Suite) |
| Agile Tickets | 50+ |
| Slack Channels | 10 |
| Slack Messages | 120+ |

---

## Re-Running Data Ingestion

```bash
docker compose run --rm app python src/ingestion/setup_dbs.py
docker compose run --rm app python src/ingestion/embed_data.py
docker compose run --rm app python src/ingestion/setup_neo4j.py
docker compose restart app
```

---

## Useful Commands

```bash
# Check service status
docker compose ps

# View live app logs
docker compose logs -f app

# Monitor resource usage
docker stats

# Restart app after code update
git pull origin main && docker compose build app && docker compose up -d app
```


