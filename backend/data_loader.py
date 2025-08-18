# backend/data_loader.py
import os
import json
import uuid
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from pinecone_helper import (
    init_pinecone,
    generate_sparse_embedding,
    upsert_hybrid_vector
)
from sqlite_helper import init_sqlite, insert_metadata, close_sqlite
from gemini_helper import generate_dense_embedding, generate_summary

load_dotenv()

def load_patent_files(folder_path):
    """Return a list of JSON file paths from the given folder."""
    return [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith(".json")
    ]

def split_text_into_chunks(text, chunk_size=2500, chunk_overlap=150):
    """Split text into overlapping chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def extract_english_field(entries, field_name):
    """Extract English version of a specific field."""
    for entry in entries:
        if entry.get("lang") == "EN":
            return entry.get(field_name, "")
    return ""

def process_and_upsert_patents():
    """Main function to process all patent files and upsert into Pinecone + SQLite."""
    index = init_pinecone()
    file_paths = load_patent_files("patent_jsons")
    print(f"📊 Total Patent Files Found: {len(file_paths)}")

    conn, cursor = init_sqlite()
    total_chunks = 0

    for file_idx, file_path in enumerate(file_paths):
        file_name = os.path.basename(file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                patent = json.load(f)
                print(f"\n🟢 Processing File {file_idx + 1}: {file_name}\n")
        except Exception as e:
            print(f"❌ Failed to load {file_name}: {e}")
            continue

        # Extract fields
        patent_number = patent.get("patent_number", f"patent_{file_idx}")
        title = extract_english_field(patent.get("titles", []), "text")
        abstract = extract_english_field(patent.get("abstracts", []), "paragraph_markup")
        description = extract_english_field(patent.get("descriptions", []), "paragraph_markup")

        claims_data = patent.get("claims", [{}])[0].get("claims", [])
        claims_text = " ".join(
            [c.get("paragraph_markup", "") for c in claims_data if c.get("lang") == "EN"]
        )

        combined_text = f"{abstract} {claims_text}".strip()

        if not combined_text:
            print(f"⚠️ Skipping {patent_number}: No Abstract/Claims found.")
            continue

        # Generate summary
        detailed_summary = generate_summary(combined_text)

        # Split into chunks
        chunks = split_text_into_chunks(combined_text)
        print(f"📄 {patent_number}: {len(chunks)} chunks created.")

        for chunk_idx, chunk in enumerate(chunks):
            vector_id = f"{patent_number}_chunk_{chunk_idx}_{str(uuid.uuid4())[:8]}"

            # Dense embedding from Gemini
            dense_embedding = generate_dense_embedding(chunk)
            if dense_embedding is None:
                continue

            # Sparse embedding from Pinecone
            sparse_embedding = generate_sparse_embedding(chunk)
            if sparse_embedding is None:
                continue

            # Metadata (only key fields for search context)
            metadata = {
                "patent_number": patent_number,
                "title": title
            }

            # Upsert into Pinecone
            upsert_hybrid_vector(index, vector_id, dense_embedding, sparse_embedding, metadata)

            # Store full metadata in SQLite
            insert_metadata(
                cursor,
                vector_id,
                patent_number,
                title,
                description,
                abstract,
                claims_text,
                detailed_summary
            )

            print(f"🟢 Vector & Metadata Ready: {vector_id}")
            total_chunks += 1

    # Save & close SQLite connection
    close_sqlite(conn)
    print(f"📊 Total Chunks Processed: {total_chunks}")


if __name__ == "__main__":
    process_and_upsert_patents()
