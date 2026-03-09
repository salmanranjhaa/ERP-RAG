import os
from dotenv import load_dotenv

load_dotenv()
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core import PropertyGraphIndex
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

try:
    index = PropertyGraphIndex.from_existing(
        property_graph_store=graph_store,
        llm=Settings.llm
    )
    query_engine = index.as_query_engine(include_text=False)
    
    res = query_engine.query("Who manages Alexander Russell?")
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
