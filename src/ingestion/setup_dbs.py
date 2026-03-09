import os
import json
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, MetaData
from sqlalchemy.orm import declarative_base, sessionmaker
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")

# Configuration
POSTGRES_URI = os.getenv("POSTGRES_URI", "postgresql://admin:adminpassword@localhost:5432/erp_database")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:adminpassword@localhost:27017/")

# --- Postgres Setup ---
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    user_id = Column(String, primary_key=True)
    name = Column(String)
    department = Column(String)
    role = Column(String)
    access_level = Column(Integer)
    salary = Column(Integer)
    manager_id = Column(String, nullable=True)

class Ticket(Base):
    __tablename__ = 'tickets'
    ticket_id = Column(String, primary_key=True)
    title = Column(String)
    description = Column(String)
    type = Column(String)
    status = Column(String)
    priority = Column(String)
    customer_account = Column(String, nullable=True)
    sprint = Column(String, nullable=True)
    assignee_id = Column(String, ForeignKey('users.user_id'), nullable=True)
    reporter_id = Column(String, ForeignKey('users.user_id'), nullable=True)

# Many-to-many association table for ticket blockers
ticket_blockers = Table(
    'ticket_blockers', Base.metadata,
    Column('ticket_id', String, ForeignKey('tickets.ticket_id')),
    Column('blocked_by_id', String, ForeignKey('tickets.ticket_id'))
)

def setup_postgres():
    print(f"Connecting to Postgres at {POSTGRES_URI}...")
    engine = create_engine(POSTGRES_URI)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    print("Loading users into Postgres...")
    with open(os.path.join(DATA_DIR, 'users.json'), 'r') as f:
        users_data = json.load(f)
    
    users = []
    for u in users_data:
        users.append(User(**u))
    session.add_all(users)
    session.commit()

    print("Loading tickets into Postgres...")
    with open(os.path.join(DATA_DIR, 'tickets.json'), 'r') as f:
        tickets_data = json.load(f)
    
    tickets_to_add = []
    blockers_to_add = []
    for t in tickets_data:
        ticket_kwargs = {k: v for k, v in t.items() if k != 'blocked_by'}
        tickets_to_add.append(Ticket(**ticket_kwargs))
        for blocker in t.get('blocked_by', []):
            blockers_to_add.append({'ticket_id': t['ticket_id'], 'blocked_by_id': blocker})
            
    session.add_all(tickets_to_add)
    session.commit()

    if blockers_to_add:
        session.execute(ticket_blockers.insert(), blockers_to_add)
        session.commit()

    print(f"Inserted {len(users_data)} users and {len(tickets_data)} tickets into Postgres.")

# --- MongoDB Setup ---
def setup_mongodb():
    print(f"Connecting to MongoDB at {MONGO_URI}...")
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
    except ServerSelectionTimeoutError:
        print("Could not connect to MongoDB. Is the docker container running?")
        return

    db = client.erp_database
    messages_collection = db.messages
    
    messages_collection.drop()

    print("Loading messages into MongoDB...")
    with open(os.path.join(DATA_DIR, 'messages.json'), 'r') as f:
        messages_data = json.load(f)

    if messages_data:
        # Filter out anything that isn't a dict to prevent MongoDB errors
        valid_messages = [m for m in messages_data if isinstance(m, dict)]
        if valid_messages:
            messages_collection.insert_many(valid_messages)

    # Add text index on content for basic full-text search before vector embeddings
    messages_collection.create_index([("content", "text")])
    messages_collection.create_index("channel")

    print(f"Inserted {len(messages_data)} documents into MongoDB.")


def main():
    try:
        setup_postgres()
    except Exception as e:
        print(f"Error setting up Postgres: {e}")
        
    try:
        setup_mongodb()
    except Exception as e:
        print(f"Error setting up MongoDB: {e}")

if __name__ == "__main__":
    main()
