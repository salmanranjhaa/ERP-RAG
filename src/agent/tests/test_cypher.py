import os
from dotenv import load_dotenv
load_dotenv()
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import KnowledgeGraphIndex, Settings
from llama_index.llms.groq import Groq

Settings.llm = Groq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))

graph_store = Neo4jGraphStore(
    username="neo4j",
    password="adminpassword",
    url="bolt://localhost:7687",
    database="neo4j"
)

from llama_index.core.query_engine import KnowledgeGraphQueryEngine

try:
    query_engine = KnowledgeGraphQueryEngine(
        storage_context=None,
        graph_store=graph_store,
        llm=Settings.llm,
        generate_cypher=True,  # Crucial! This tells it to generate Cypher instead of just returning cached triples.
        verbose=True
    )
    res = query_engine.query("Who is Alexander Russell's manager?")
    print(res)
except Exception as e:
    print(e)
