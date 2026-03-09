from src.agent.router import initialize_engines, router_query_engine
import asyncio

initialize_engines()
print("Initialized!")
try:
    res = router_query_engine.query("What is blocking TKT-015 in Postgres and what is DevOps saying about it on Slack?")
    print("Response:", res)
except Exception as e:
    print("Error:", e)
