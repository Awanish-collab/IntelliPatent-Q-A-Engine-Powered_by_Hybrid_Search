# backend/create_pinecone_index.py
import os
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Using Gemini embeddings → dimension = 1536
DIMENSION = 1536
METRIC = "dotproduct"  # Best for hybrid search

print("PINECONE_API_KEY:", PINECONE_API_KEY)
def create_index():
    pc = Pinecone(api_key=PINECONE_API_KEY)

    # Check if index already exists
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]
    if PINECONE_INDEX_NAME in existing_indexes:
        print(f"ℹ️ Index '{PINECONE_INDEX_NAME}' already exists. Skipping creation.")
        return

    # Optional metadata config (future filtering)
    metadata_config = {
        "indexed": ["patent_number", "title"]
    }

    pc.create_index(
        name=PINECONE_INDEX_NAME,
        dimension=DIMENSION,
        metric=METRIC,
        spec=ServerlessSpec(
            cloud="aws",
            region="us-east-1"
        )
    )


    print(f"✅ Created Pinecone Hybrid Index: {PINECONE_INDEX_NAME}")

if __name__ == "__main__":
    create_index()
