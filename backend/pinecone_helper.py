# backend/pinecone_helper.py - FIXED VERSION
import os
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY1")
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")

# Initialize Pinecone client
pc_client = Pinecone(api_key=PINECONE_API_KEY)

def init_pinecone():
    """Initialize Pinecone index connection."""
    try:
        index = pc_client.Index(PINECONE_INDEX_NAME)
        print(f"✅ Connected to Pinecone index: {PINECONE_INDEX_NAME}")
        return index
    except Exception as e:
        print(f"❌ Error initializing Pinecone: {e}")
        return None

def generate_sparse_embedding(text, for_query=False):
    """Generate sparse embedding using Pinecone's sparse model."""
    try:
        if not text or not text.strip():
            print("⚠️ Skipped sparse embedding: Empty text")
            return None

        input_type = "query" if for_query else "passage"

        response = pc_client.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=[text],
            parameters={"input_type": input_type, "truncate": "END"}
        )

        if not response or not hasattr(response, "data") or len(response.data) == 0:
            print("❌ Sparse embedding failed: No data in response")
            return None

        # Get the first embedding result
        embedding_data = response.data[0]
        
        # Try different ways to access sparse data
        sparse_indices = None
        sparse_values = None
        
        # Method 1: Direct attribute access
        if hasattr(embedding_data, 'sparse_indices') and hasattr(embedding_data, 'sparse_values'):
            sparse_indices = embedding_data.sparse_indices
            sparse_values = embedding_data.sparse_values
        
        # Method 2: Dictionary-like access
        elif isinstance(embedding_data, dict):
            sparse_indices = embedding_data.get('sparse_indices')
            sparse_values = embedding_data.get('sparse_values')
        
        # Method 3: Check for different attribute names (based on your original output)
        elif hasattr(embedding_data, 'indices') and hasattr(embedding_data, 'values'):
            sparse_indices = embedding_data.indices  
            sparse_values = embedding_data.values

        if sparse_indices is None or sparse_values is None:
            print(f"❌ Could not extract sparse data. Available attributes: {dir(embedding_data)}")
            return None

        # Convert to the format expected by Pinecone
        result = {
            "indices": [int(idx) for idx in sparse_indices],
            "values": [float(val) for val in sparse_values]
        }
        
        print(f"✅ Generated sparse embedding: {len(result['indices'])} features")
        return result

    except Exception as e:
        print(f"❌ Error generating sparse embedding: {e}")
        return None

def upsert_hybrid_vector(index, vector_id, dense_embedding, sparse_embedding, metadata):
    """Upsert dense + sparse embeddings with metadata using Pinecone's hybrid format."""
    try:
        # Prepare the vector data according to Pinecone's hybrid format
        vector_data = {
            "id": vector_id,
            "values": dense_embedding,
            "metadata": metadata
        }
        
        # Add sparse values in the correct format
        if sparse_embedding and isinstance(sparse_embedding, dict):
            if "indices" in sparse_embedding and "values" in sparse_embedding:
                # ✅ CORRECTED: Use the exact format from Pinecone documentation
                vector_data["sparse_values"] = {
                    'indices': sparse_embedding['indices'], 
                    'values': sparse_embedding['values']
                }
                print(f"🔥 Upserting HYBRID vector: {vector_id}")
            else:
                print(f"⚠️ Invalid sparse embedding format, upserting dense-only: {vector_id}")
        else:
            print(f"⚠️ No sparse embedding provided, upserting dense-only: {vector_id}")

        # Upsert the vector using the vectors parameter
        index.upsert(vectors=[vector_data])
        print(f"✅ Hybrid vector upserted successfully: {vector_id}")
        
    except Exception as e:
        print(f"❌ Hybrid Upsert Error for {vector_id}: {e}")
        print(f"Error details: {str(e)}")
        
        # Try dense-only fallback
        try:
            print(f"🔄 Attempting dense-only fallback for {vector_id}")
            index.upsert(vectors=[{
                "id": vector_id,
                "values": dense_embedding,
                "metadata": metadata
            }])
            print(f"✅ Dense-only fallback successful: {vector_id}")
        except Exception as fallback_error:
            print(f"❌ Dense-only fallback also failed: {fallback_error}")

def debug_sparse_embedding(text):
    """Debug function to inspect sparse embedding structure."""
    try:
        response = pc_client.inference.embed(
            model="pinecone-sparse-english-v0",
            inputs=[text],
            parameters={"input_type": "passage", "truncate": "END"}
        )
        
        print("=== SPARSE EMBEDDING DEBUG ===")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        
        if hasattr(response, 'data') and response.data:
            embedding_data = response.data[0]
            print(f"Embedding data type: {type(embedding_data)}")
            print(f"Embedding data: {embedding_data}")
            
            if hasattr(embedding_data, '__dict__'):
                print(f"Available attributes: {list(embedding_data.__dict__.keys())}")
            elif isinstance(embedding_data, dict):
                print(f"Available keys: {list(embedding_data.keys())}")
        
        return response
    except Exception as e:
        print(f"Debug error: {e}")
        return None

# Test function - uncomment to debug
# if __name__ == "__main__":
#     debug_sparse_embedding("Python is a programming language")