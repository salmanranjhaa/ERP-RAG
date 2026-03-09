import os
from pymongo import MongoClient
from dotenv import load_dotenv

from llama_index.core import Document, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.mongodb import MongoDBAtlasVectorSearch
from llama_index.core import StorageContext

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:adminpassword@localhost:27017/")

def embed_messages():
    print("Connecting to MongoDB...")
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.erp_database
    messages_collection = db.messages
    
    # Retrieve all documents
    messages = list(messages_collection.find({}))
    if not messages:
        print("No messages found in MongoDB to embed!")
        return
        
    print(f"Loaded {len(messages)} messages. Preparing documents for LlamaIndex...")
    documents = []
    for msg in messages:
        doc = Document(
            text=msg.get('content', 'No content provided.'),
            metadata={
                "channel": msg.get('channel', 'unknown'),
                "author_id": msg.get('author_id', 'unknown'),
                "timestamp": msg.get('timestamp', 'unknown'),
                "message_id": msg.get('message_id', 'unknown')
            }
        )
        documents.append(doc)

    print("Loading HuggingFace Embedding Model ('all-MiniLM-L6-v2')...")
    embed_model = HuggingFaceEmbedding(model_name="all-MiniLM-L6-v2")
    
    print("Connecting to Vector Store...")
    from llama_index.vector_stores.chroma import ChromaVectorStore
    import chromadb
    
    # We use a purely local Chroma memory/disk instance so you don't need a cloud DB
    CHROMA_PATH = os.getenv("CHROMA_PATH", "../../chroma_data")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    chroma_collection = chroma_client.get_or_create_collection("messages_index")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    print("Embedding documents and saving to Vector Store (this might take a few moments)...")
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context, 
        embed_model=embed_model,
        show_progress=True
    )
    
    print("Successfully embedded and indexed all Slack messages!")

if __name__ == "__main__":
    embed_messages()
