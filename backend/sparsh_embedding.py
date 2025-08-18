from pinecone import ServerlessSpec
import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("PINECONE_API_KEY1")
pc = Pinecone(api_key=api_key)


# Convert the chunk_text into sparse vectors
sparse_embeddings = pc.inference.embed(
    model="pinecone-sparse-english-v0",
    inputs=["Python is Dynamic Langauge", "Physics is a Science"],
    parameters={"input_type": "passage", "truncate": "END"}
)

#val = sparse_embeddings['sparse_values']
print(sparse_embeddings)