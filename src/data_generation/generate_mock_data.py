"""
LLM-Powered Mock Data Generator for NexaMedTech ERP
Uses Groq's Llama-3.3-70b to generate a fully interconnected, realistic
enterprise dataset for a ~65-person pharma/medtech ERP software company.

Run this script ONCE to generate data/raw/*.json files.
Then run setup_dbs.py and embed_data.py to populate the databases.
"""

import os
import json
import uuid
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/raw'))
os.makedirs(DATA_DIR, exist_ok=True)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def llm(prompt: str, system: str = "You are a precise data generator. Return only valid JSON. No markdown, no explanation, no ```json fences. Just the raw JSON object or array.", retries: int = 3) -> dict | list:
    """Call Groq LLM and parse JSON response."""
    for attempt in range(retries):
        try:
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85,
                max_tokens=8000,
            )
            raw = resp.choices[0].message.content.strip()
            # Find the first [ or { and last ] or }
            start_idx = raw.find('[')
            start_obj = raw.find('{')
            
            if start_idx == -1 and start_obj == -1:
                raise ValueError("No JSON found in response.")
            
            if start_idx == -1: start = start_obj
            elif start_obj == -1: start = start_idx
            else: start = min(start_idx, start_obj)
            
            if start == start_idx:
                end = raw.rfind(']')
            else:
                end = raw.rfind('}')
                
            if start != -1 and end != -1:
                raw = raw[start:end+1]
                
            res = json.loads(raw)
            if isinstance(res, dict):
                # Sometimes the LLM returns a single object instead of an array
                if "users" in res and isinstance(res["users"], list):
                    return res["users"]
                if "tickets" in res and isinstance(res["tickets"], list):
                    return res["tickets"]
                if "messages" in res and isinstance(res["messages"], list):
                    return res["messages"]
                return [res]
            import time
            time.sleep(5)  # Throttle normally to prevent TPM spikes
            return res
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                import time
                print("     [Rate Limit Hit] Sleeping for 30 seconds before retry...")
                time.sleep(30)
            if attempt < retries - 1:
                print(f"     [Retry {attempt+1}/{retries}] Failed. Retrying... ({e})")
            else:
                raise e


# ─────────────────────────────────────────────
# STEP 1: Generate the Org Chart
# ─────────────────────────────────────────────
def generate_users() -> list[dict]:
    print("  [1/4] Asking Groq to generate 65-person org chart...")
    users = llm("""
Generate a realistic org chart for "NexaMedTech Solutions" — a 65-person ERP software startup  
that sells pharma and medtech automation software to enterprises like Johnson & Johnson, Pfizer, Novartis, and Roche.

Return a JSON ARRAY of exactly 65 user objects. Each user must have:
- user_id: string like "U001", "U002"... up to "U065"
- name: realistic full name (first + last)
- department: one of ["Executive", "Product", "Engineering", "QA", "Infrastructure", "Business Analysis", "Sales", "Customer Success", "HR", "Finance"]
- role: a realistic and specific job title
- access_level: integer 1-4 (4=C-suite, 3=Director/Lead, 2=Senior, 1=Junior)
- salary: integer (realistic USD based on role)
- manager_id: user_id of their direct manager (null for CEO)

The company structure should include:
- 1 CEO, 1 CTO, 1 CPO, 1 CFO, 1 VP Sales, 1 HR Director
- 2 Engineering Managers (Backend, Frontend/Mobile)
- 1 DevOps Lead, 1 Infrastructure Lead, 1 DB Administrator
- 1 QA Manager, 3 QA Engineers / Testers
- 1 BA Director, 4 Business Analysts
- 2 Product Managers, 2 Product Owners
- 8 Backend Engineers, 5 Frontend Engineers, 2 Mobile Engineers
- 3 DevOps Engineers, 2 Infrastructure Engineers
- 4 Sales Managers, 4 Account Executives (assigned to J&J, Pfizer, Novartis, Roche)
- 4 Customer Success Managers
- 3 HR staff, 2 Finance Analysts
- Any remaining roles to reach 65 total

Managers must be consistent — employees must reference a valid user_id as their manager.
The CEO's manager_id must be null.
""")
    print(f"     Generated {len(users)} users.")
    return users


# ─────────────────────────────────────────────
# STEP 2: Generate Tickets with full lifecycle
# ─────────────────────────────────────────────
def generate_tickets(users: list[dict]) -> list[dict]:
    print("  [2/4] Iteratively generating 50 tickets (5 batches of 10) to avoid rate limits and explain context...")
    
    # Use a truncated roster for prompt brevity
    roster = [{"user_id": u["user_id"], "name": u["name"], "role": u["role"]} for u in users[:25]]
    all_tickets = []
    
    for i in range(5):
        print(f"     => Generating batch {i+1} of 5 (10 tickets)...")
        existing_ids = [t["ticket_id"] for t in all_tickets]
        prompt = f"""
We are iteratively generating tickets for an ERP system. 
You have already generated these tickets: {json.dumps(existing_ids)}

Now generate EXACTLY 10 New ticket objects. Each ticket must have:
- ticket_id: Start from exactly TKT-{(i*10)+1:03d} to TKT-{(i*10)+10:03d}
- title: specific, realistic title (mention pharma systems like FDA 21 CFR Part 11, HL7 FHIR, HIPAA, AI anomalies)
- description: 2-3 sentence detailed description
- type: one of ["bug", "feature", "compliance", "infrastructure", "deployment"]
- status: one of ["Open", "In Progress", "Blocked", "In QA", "In BA Review", "Awaiting Deployment", "Deployed", "Closed"]
- priority: one of ["Critical", "High", "Medium", "Low"]
- assignee_id: valid user_id from this roster: {json.dumps(roster)}
- reporter_id: valid user_id from the roster
- blocked_by: JSON array of ticket_ids this is blocked by. Use ONLY tickets from {json.dumps(existing_ids)}. Leave empty if none.
- customer_account: one of ["Johnson & Johnson", "Pfizer", "Novartis", "Roche", "Internal"]
- sprint: "Sprint 2025-Q1-3"

Return a JSON ARRAY of 10 objects.
"""
        batch = llm(prompt)
        if isinstance(batch, list):
            all_tickets.extend(batch)
        else:
            print("     [Error] Batch did not return list. Skipping.")
        
    print(f"     Generated {len(all_tickets)} tickets total.")
    return all_tickets


# ─────────────────────────────────────────────
# STEP 3: Generate Slack Messages
# ─────────────────────────────────────────────
def generate_messages(users: list[dict], tickets: list[dict]) -> list[dict]:
    print("  [3/4] Iteratively generating Slack messages channel by channel...")
    roster = [{"user_id": u["user_id"], "name": u["name"]} for u in users[:25]]
    ticket_summary = [{"ticket_id": t["ticket_id"], "title": t["title"], "status": t["status"]} for t in tickets[:20]]
    
    channels = [
        "#general", "#engineering", "#dev-ops-alerts", "#qa-team", "#sales-wins", 
        "#product-updates", "#hr-confidential", "#customer-success", "#compliance-watch", "#standup"
    ]
    
    all_messages = []
    msg_id = 1000
    
    for ch in channels:
        print(f"     => Generating 12 messages for channel {ch}...")
        prompt = f"""
We are generating realistic internal Slack messages for the {ch} channel at NexaMedTech Solutions.
We do this channel by channel to maintain a contextual thread.

User roster: {json.dumps(roster)}
Active tickets: {json.dumps(ticket_summary)}

Return a JSON ARRAY of exactly 12 message objects.
- message_id: start from MSG-{msg_id} and increment
- channel: exactly "{ch}"
- author_id: a valid user_id from the roster
- content: realistic Slack message (1-4 sentences). Must reference coworkers, tickets, or pharma customers (Pfizer, J&J, Novartis).
- timestamp: ISO datetime string between 2026-02-01T08:00:00 and 2026-03-08T18:00:00

Make it a coherent thread or set of updates for this specific channel. Keep tone realistic, frustrated, or celebratory based on the channel context.
"""
        batch = llm(prompt)
        if isinstance(batch, list):
            all_messages.extend(batch)
            msg_id += len(batch)
        else:
            print(f"     [Error] Channel {ch} did not return a list. Skipping.")
            
    print(f"     Generated {len(all_messages)} total messages.")
    return all_messages


# ─────────────────────────────────────────────
# STEP 4: Save to JSON files
# ─────────────────────────────────────────────
def save_data(users, tickets, messages):
    print("  [4/4] Saving generated data to data/raw/ ...")
    with open(os.path.join(DATA_DIR, 'users.json'), 'w') as f:
        json.dump(users, f, indent=2)
    with open(os.path.join(DATA_DIR, 'tickets.json'), 'w') as f:
        json.dump(tickets, f, indent=2)
    with open(os.path.join(DATA_DIR, 'messages.json'), 'w') as f:
        json.dump(messages, f, indent=2)
    print(f"     Saved {len(users)} users, {len(tickets)} tickets, {len(messages)} messages.")


if __name__ == "__main__":
    print("\n🚀 NexaMedTech LLM Data Generator starting...")
    print("   This calls Groq 3 times and may take 30-60 seconds total.\n")
    try:
        users = generate_users()
        tickets = generate_tickets(users)
        messages = generate_messages(users, tickets)
        save_data(users, tickets, messages)
        print("\n✅ Done! Now run:")
        print("   1. .\\venv\\Scripts\\python src\\ingestion\\setup_dbs.py")
        print("   2. .\\venv\\Scripts\\python src\\ingestion\\embed_data.py")
        print("   3. .\\venv\\Scripts\\python src\\agent\\router.py\n")
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parse error: {e}")
        print("   Groq returned malformed JSON. Try running again.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
