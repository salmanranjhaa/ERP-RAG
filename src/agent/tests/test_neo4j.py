import os
from dotenv import load_dotenv

load_dotenv()
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core.query_engine import KnowledgeGraphQueryEngine
from llama_index.core import Settings
from llama_index.llms.groq import Groq

# Settings
Settings.llm = Groq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))

graph_store = Neo4jGraphStore(
    username="neo4j",
    password="adminpassword",
    url="neo4j://localhost:7687",
    database="neo4j"
)

# In older versions, KnowledgeGraphQueryEngine took graph_store, in newer it's often PropertyGraphIndex.
# Let's see if KnowledgeGraphQueryEngine works:
try:
    query_engine = KnowledgeGraphQueryEngine(
        storage_context=None,
        graph_store=graph_store,
        llm=Settings.llm,
        verbose=True
    )
    res = query_engine.query("Who is the CEO?")
    print(res)
except Exception as e:
    print("Error with KnowledgeGraphQueryEngine:", e)
