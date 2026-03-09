import os
from dotenv import load_dotenv

load_dotenv()
from llama_index.core.query_engine import CustomQueryEngine
from llama_index.core.tools import QueryEngineTool
from llama_index.llms.groq import Groq
from llama_index.core import Settings
from neo4j import GraphDatabase

Settings.llm = Groq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))
neo4j_driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "adminpassword"))

neo4j_schema = "Nodes: Person, Ticket..."

class Neo4jCustomQueryEngine(CustomQueryEngine):
    schema: str = neo4j_schema
    def custom_query(self, query_str: str):
        prompt = f"Given the following Neo4j schema:\n{self.schema}\n\nWrite a Cypher query to answer: {query_str}\nOnly return the pure cypher query without any markdown tags or prefix."
        cypher_query = Settings.llm.complete(prompt).text.strip().replace("```cypher", "").replace("```", "")
        with neo4j_driver.session() as session:
            result = session.run(cypher_query)
            records = [dict(record) for record in result]
        return f"Cypher: {cypher_query}\nRecords: {records}"

tool = QueryEngineTool.from_defaults(
    query_engine=Neo4jCustomQueryEngine(),
    name="neo4j_graph_tool",
    description="Test"
)

print(tool)
print("Working!")
