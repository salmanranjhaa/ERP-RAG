import os
from dotenv import load_dotenv

load_dotenv()
from llama_index.core.tools import FunctionTool
from neo4j import GraphDatabase
from llama_index.core import Settings
from llama_index.llms.groq import Groq

Settings.llm = Groq(model="llama-3.3-70b-versatile", api_key=os.environ.get("GROQ_API_KEY"))

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "adminpassword"))

neo4j_schema = """
Nodes:
- Person (user_id, name, role, salary)
- Ticket (ticket_id, title, type, priority)
- Department (name)
- Status (name)
- Sprint (name)

Relationships:
- (Person)-[:WORKS_IN]->(Department)
- (Person)-[:REPORTS_TO]->(Person)
- (Person)-[:ASSIGNED_TO]->(Ticket)
- (Person)-[:REPORTED]->(Ticket)
- (Ticket)-[:BLOCKED_BY]->(Ticket)
- (Ticket)-[:CURRENT_STATUS]->(Status)
- (Ticket)-[:ASSIGNED_TO_SPRINT]->(Sprint)
"""

def query_neo4j_graph(query_str: str) -> str:
    prompt = f"Given the following Neo4j schema:\n{neo4j_schema}\n\nWrite a Cypher query to answer: {query_str}\nOnly return the pure cypher query without any markdown tags or prefix."
    cypher_query = Settings.llm.complete(prompt).text.strip().replace("```cypher", "").replace("```", "")
    with driver.session() as session:
        result = session.run(cypher_query)
        records = [dict(record) for record in result]
    return f"Cypher: {cypher_query}\nRecords: {records}"

neo4j_tool = FunctionTool.from_defaults(
    fn=query_neo4j_graph,
    name="neo4j_graph_tool",
    description="Useful for querying complex relationships like chains of command, manager dependencies, or complex ticket blockers (e.g. 'what tickets block X' or 'who is the manager of the person blocking Y')."
)

if __name__ == "__main__":
    res = neo4j_tool("Who manages Alexander Russell?")
    print(res)
