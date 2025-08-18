# backend/sqlite_helper.py
import sqlite3
import os

def init_sqlite():
    """
    Initialize SQLite database and create the table if it doesn't exist.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(base_dir, "patent_data.db")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patent_chunks (
            vector_id TEXT PRIMARY KEY,
            patent_number TEXT,
            title TEXT,
            description TEXT,
            abstract TEXT,
            claims_text TEXT,
            detailed_summary TEXT
        )
    """)

    conn.commit()
    print(f"✅ SQLite DB Initialized at {db_path}")
    return conn, cursor

def insert_metadata(cursor, vector_id, patent_number, title, description, abstract, claims_text, detailed_summary):
    """
    Insert metadata for a single chunk into the SQLite DB.
    """
    cursor.execute("""
        INSERT OR REPLACE INTO patent_chunks (
            vector_id, patent_number, title, description, abstract, claims_text, detailed_summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        vector_id,
        patent_number,
        title,
        description,
        abstract,
        claims_text,
        detailed_summary
    ))

def close_sqlite(conn):
    """
    Commit changes and close the SQLite connection.
    """
    conn.commit()
    conn.close()
    print("✅ SQLite DB Saved and Closed.")
