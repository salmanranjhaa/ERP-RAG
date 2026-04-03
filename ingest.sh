#!/bin/bash
# ============================================================
# ERP-RAG: Full Data Ingestion Script
# Run this on the GCP VM AFTER docker compose is up and healthy
# ============================================================

set -e  # Exit on any error

echo "============================================"
echo "  ERP-RAG Data Ingestion Pipeline"
echo "============================================"

# --- Config (edit GROQ_API_KEY below) ---
export GROQ_API_KEY="${GROQ_API_KEY:?ERROR: Set GROQ_API_KEY env var before running}"
export POSTGRES_URI="postgresql://admin:adminpassword@localhost:5432/erp_database"
export MONGO_URI="mongodb://admin:adminpassword@localhost:27017/"
export CHROMA_PATH="/home/$USER/ERP-RAG/chroma_data"
export NEO4J_URI="bolt://localhost:7687"

echo ""
echo "[1/3] Loading users, tickets into Postgres + messages into MongoDB..."
python3 src/ingestion/setup_dbs.py

echo ""
echo "[2/3] Embedding Slack messages into ChromaDB..."
python3 src/ingestion/embed_data.py

echo ""
echo "[3/3] Building Neo4j Org Graph..."
python3 src/ingestion/setup_neo4j.py

echo ""
echo "============================================"
echo "  Ingestion Complete!"
echo "  ChromaDB data at: $CHROMA_PATH"
echo "============================================"
