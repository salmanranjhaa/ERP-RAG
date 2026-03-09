from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# Database and Indexing
from sqlalchemy import create_engine
from pymongo import MongoClient
from llama_index.core import SQLDatabase, VectorStoreIndex
from llama_index.core.query_engine import NLSQLTableQueryEngine, RouterQueryEngine
from llama_index.core.selectors import LLMSingleSelector
from llama_index.core.tools import QueryEngineTool
from llama_index.core.agent import ReActAgent

# Models
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch

# Load env variables
load_dotenv()

app = FastAPI(title="ERP RAG Agent Router", description="Conversational RAG using Groq and LlamaIndex")

# Serve frontend directly from backend
public_dir = os.path.join(os.path.dirname(__file__), "public")
os.makedirs(public_dir, exist_ok=True)

# Database constants
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://admin:adminpassword@localhost:5432/erp_database")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:adminpassword@localhost:27017/")

# Global variables for the engine
router_query_engine = None

def initialize_engines():
    global router_query_engine
    
    print("Initializing Models (Groq + HuggingFace)...")
    # Set up models
    # We use moonshotai/kimi-k2-instruct-0905, which is heavily optimized for function/tool calling & routing
    # We use llama-3.3-70b-versatile, which is natively supported and blazing fast on Groq.
    # Note: Kimi K2 isn't hosted by the official Groq API (it's Moonshot AI).
    llm = Groq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))
    embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    
    # Global settings
    Settings.llm = llm
    Settings.embed_model = embed_model
    
    # 1. Postgres Setup (Structured Data)
    print("Connecting to Postgres...")
    pg_engine = create_engine(POSTGRES_URI)
    sql_database = SQLDatabase(pg_engine, include_tables=["users", "tickets", "ticket_blockers"])
    
    sql_query_engine = NLSQLTableQueryEngine(
        sql_database=sql_database,
        tables=["users", "tickets", "ticket_blockers"],
        llm=llm
    )
    
    # 2. Chroma Setup (Unstructured Data)
    print("Connecting to Chroma (Local Vector Store)...")
    from llama_index.vector_stores.chroma import ChromaVectorStore
    import chromadb
    
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    chroma_collection = chroma_client.get_or_create_collection("messages_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # Recreate index over Chroma
    chroma_index = VectorStoreIndex.from_vector_store(vector_store)
    mongo_query_engine = chroma_index.as_query_engine(similarity_top_k=5)

    # 3. Build the Agentic Router (Upgraded to Multi-Step Synthesis)
    print("Building Multi-Source Synthesis Agent...")
    
    sql_tool = QueryEngineTool.from_defaults(
        query_engine=sql_query_engine,
        name="sql_analytics_tool",
        description=(
            "Useful for getting strict quantitative data and ticket relationships. "
            "Use this to query EXACT ticket hierarchies (blocked_by), assignee logic, salaries, access_levels, and roles."
        )
    )
    
    mongo_tool = QueryEngineTool.from_defaults(
        query_engine=mongo_query_engine,
        name="unstructured_chat_tool",
        description=(
            "Useful for discovering narrative context, human reasoning, and conversational history across Slack channels. "
            "Use this for 'why' questions, reading arguments between engineers, finding out WHO is waiting on WHAT beyond what SQL says."
        )
    )
    
    # LLMMultiSelector allows the router to read the question, determine it needs BOTH SQL and Vector context,
    # pull them both simultaneously, and synthesize an expert final answer.
    from llama_index.core.selectors import LLMMultiSelector
    router_query_engine = RouterQueryEngine(
        selector=LLMMultiSelector.from_defaults(llm=llm),
        query_engine_tools=[sql_tool, mongo_tool],
    )
    print("Initialization Complete!")

@app.on_event("startup")
def on_startup():
    initialize_engines()

class ChatRequest(BaseModel):
    query: str
    user_id: str = None # For future RBAC integration

import json
from llama_index.core.callbacks import CallbackManager, LlamaDebugHandler, CBEventType

# Log store for the current request
class PayloadLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, step, payload):
        self.logs.append({"step": step, "payload": payload})

payload_logger = PayloadLogger()

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    global router_query_engine
    if not router_query_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    logs = []
    try:
        # Multi-Source Synthesis
        # We simulate the payload logging since LlamaIndex makes multi-calls
        logs.append({
            "step": "Llama 3.3 Input",
            "payload": {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": request.query}],
                "temperature": 0.1
            }
        })
        
        result = router_query_engine.query(request.query)
        
        # Get which tools it used safely
        meta = getattr(result, "metadata", None) or {}
        selections = meta.get("selector_result", [])
        
        if hasattr(selections, "selections"):
            source = str([s.reason for s in selections.selections])
        else:
            source = str(selections)
            
        logs.append({
            "step": "Llama 3.3 Output",
            "payload": {
                "response": str(result),
                "source_nodes": [str(n.node.get_content()[:200]) + "..." for n in result.source_nodes] if hasattr(result, "source_nodes") else []
            }
        })
            
    except Exception as e:
        print(f"Exception triggered: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "query": request.query,
        "response": str(result),
        "source": source,
        "detailed_logs": logs
    }

@app.post("/chat/audio")
async def chat_audio_endpoint(audio: UploadFile = File(...)):
    global router_query_engine
    if not router_query_engine:
        raise HTTPException(status_code=500, detail="Engine not initialized")
    
    import tempfile
    from groq import Groq as NativeGroqClient
    
    logs = []
    
    # Save the audio blob temporarily to disk
    audio_data = await audio.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        tmp.write(audio_data)
        tmp_path = tmp.name

    try:
        # 1. Transcribe the audio using Groq's insanely fast Whisper Large v3
        logs.append({
            "step": "Whisper v3 Input",
            "payload": {
                "model": "whisper-large-v3",
                "file_size": len(audio_data),
                "format": "webm"
            }
        })
        
        client = NativeGroqClient(api_key=os.environ.get("GROQ_API_KEY"))
        with open(tmp_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
              file=(os.path.basename(tmp_path), file.read()),
              model="whisper-large-v3",
              response_format="text"
            )
            
        transcribed_text = transcription
        logs.append({
            "step": "Whisper v3 Output",
            "payload": {
                "text": transcribed_text
            }
        })
        
        # 2. Pass the transcribed text into the Synthesis RAG Router
        logs.append({
            "step": "Llama 3.3 Input",
            "payload": {
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": transcribed_text}]
            }
        })
        
        result = router_query_engine.query(transcribed_text)
        
        # 3. Get Source Reasonings safely
        meta = getattr(result, "metadata", None) or {}
        selections = meta.get("selector_result", [])
        
        if hasattr(selections, "selections"):
            source = str([s.reason for s in selections.selections])
        else:
            source = str(selections)
            
        logs.append({
            "step": "Llama 3.3 Output",
            "payload": {
                "response": str(result),
                "source": source
            }
        })
            
        return {
            "query": transcribed_text,
            "response": str(result),
            "source": source,
            "detailed_logs": logs
        }
    except Exception as e:
        print(f"Exception triggered in audio endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)

# Serve frontend directly from backend via Root (MUST be at bottom to avoid intercepting APIs)
app.mount("/", StaticFiles(directory=public_dir, html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    # Important: Ensure python-multipart and groq are installed in your environment!
    uvicorn.run(app, host="0.0.0.0", port=8000)
