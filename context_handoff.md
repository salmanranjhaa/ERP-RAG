# Context Handoff: NexaMedTech ERP RAG Agent

## What We Have Built So Far
We are building a highly advanced, multi-source RAG Agent system designed for an Enterprise ERP context. The system is fully operational locally.

**Architecture:**
- **Backend:** Python + FastAPI (`src/agent/router.py`).
- **AI Engine:** LlamaIndex using **Groq** (`llama-3.3-70b-versatile` running at 200+ tokens/s).
- **Frontend:** A beautiful Glassmorphism Vanilla HTML/CSS/JS dashboard (`src/agent/public/`) served natively off the root FastAPI endpoint.
- **Voice Interactivity:** The frontend uses HTML5 `MediaRecorder` to capture audio blobs, sends them to a `/chat/audio` API, and uses Groq's **Whisper-Large-v3** for under-200ms voice transcription perfectly integrated into the chat.
- **Data Sources (Dockerized):**
  1. **PostgreSQL Database:** Holds strict relational data (Users, Tickets, Ticket Blockers). Polled via `NLSQLTableQueryEngine`.
  2. **ChromaDB Local Vector Store:** Holds unstructured Slack conversational logs (previously passed from MongoDB). Polled via standard `VectorStoreIndex`.
- **The Routing Logic:** We use an `LLMMultiSelector` Router that allows Llama 3 to intelligently ping *both* Postgres and ChromaDB simultaneously to synthesize answers that require both deep relational hierarchies and emotional/conversational context.

## The Current Blocker (Why We Shifted Strategy)
The system fundamentally works, but the AI's responses are weak because our initial mock data was hand-coded and tiny (only 7 users, 5 tickets, 9 Slack messages). Postgres correctly reported tables as empty when asked complex relational questions, causing the RAG to fail to showcase its true reasoning capabilities.

To fix this, we decided to use the LLM to recursively generate its own chaotic, highly realistic, interconnected dataset.

## The Organization: "NexaMedTech Solutions"
I have just written a new `generate_mock_data.py` script that hits the Groq API to hallucinate a complete 65-person company. Here is the exact organizational structure and chaos we defined:

**The Company:** A Mid-size MedTech/Pharma ERP Start-up building automation software for enterprises like J&J, Pfizer, Novartis, and Roche (handling things like FDA 21 CFR Part 11 compliance, HL7 FHIR pipelines, and AI anomaly detection).

**The 65-Person Org Chart:**
- **C-Suite & Execs:** CEO, CTO, CPO, CFO, VP Sales, HR Director, BA Director.
- **Middle Management:** Engineering Managers (Backend/Frontend), DevOps Lead, QA Manager, Sales Managers.
- **The Grunts:** Business Analysts (BAs), Product Managers (PMs), Developers (Backend/Frontend/Mobile), QA Engineers/Testers, DevOps/Infrastructure Engineers, Account Executives (AEs), Customer Success (CS) Managers, HR, Finance.

**The Chaos (Full Agile/Ticket Lifecycle):**
The dataset generates 50+ massively interconnected tickets and 120+ Slack messages across 10 channels (`#dev-ops-alerts`, `#compliance-watch`, `#hr-confidential`, etc.).
The tickets follow realistic, painful enterprise lifecycles:
- **Bugs:** CS opens ticket -> QA confirms -> BA takes ownership -> Dev assigned -> Dev fixes -> QA tests -> Bug Reopened (fails) -> Dev redoes -> QA passes -> BA validates -> QA Deployment Approval -> User Accceptance -> Prod Deployment.
- **Features:** PM creates -> BA documents -> Dev builds -> QA validates -> BA signs off -> Prod.

## Immediate Next Steps for the New Chat
The new `generate_mock_data.py` script has been written, but we have not executed the pipeline yet. 

Please perform the following steps to bring the system online with the new data:
1. **Generate the Data:** Run `python src/data_generation/generate_mock_data.py`. Ensure Groq successfully outputs and saves `users.json`, `tickets.json`, and `messages.json` to the `data/raw/` directory without JSON parsing errors.
2. **Setup Relational DB:** Run `python src/ingestion/setup_dbs.py` to wipe the old data and push the new 65 users and 50 tickets into Postgres, and the 120 messages into MongoDB.
3. **Embed Vector DB:** Run `python src/ingestion/embed_data.py` to re-embed the massive new Slack log dataset into the local ChromaDB vector store.
4. **Boot the Server & Test:** Boot `python src/agent/router.py`. Open `http://localhost:8000/` and try asking hyper-complex conversational questions using the Voice Microphone that require the `LLMMultiSelector` to cross-reference a pharma compliance bug in Postgres with a DevOps argument in Slack.
