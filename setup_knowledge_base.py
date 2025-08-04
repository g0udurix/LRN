#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Setup Script for the Knowledge Base Database.

This script creates a SQLite database with a normalized, relational schema
designed to store and manage various types of legislative and operational documents.
"""

import sqlite3
import argparse
import os

def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database and enables foreign keys."""
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        print(f"Successfully connected to database at: {db_path}")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}", flush=True)
        raise

def create_schema(conn: sqlite3.Connection):
    """
    Creates all the necessary tables for the knowledge base.
    The schema is designed to be idempotent (can be run multiple times safely).
    """
    cursor = conn.cursor()
    print("Creating database schema...")

    # --- Core Tables ---

    # Jurisdictions: The source of authority for each document (hierarchical).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Jurisdictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,  -- e.g., 'Province', 'Pays', 'Ville', 'Organisme de normalisation'
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES Jurisdictions(id)
    )""")
    print("  - Table 'Jurisdictions' created or already exists.")

    # InformationAssets: The central table for any document or information source.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS InformationAssets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_type TEXT NOT NULL, -- e.g., 'Loi', 'Règlement', 'Courriel', 'Guide', 'Note technique'
        title TEXT NOT NULL,
        official_number TEXT,
        jurisdiction_id INTEGER,
        author TEXT,
        publication_date TEXT,
        source_url TEXT,
        consultation_date TEXT,
        is_archived BOOLEAN DEFAULT 0,
        FOREIGN KEY (jurisdiction_id) REFERENCES Jurisdictions(id)
    )""")
    print("  - Table 'InformationAssets' created or already exists.")

    # ContentBlocks: The granular, versioned content of each asset.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ContentBlocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        parent_id INTEGER,          -- Self-referencing for hierarchy (section -> article -> alinéa)
        display_order INTEGER,
        block_type TEXT NOT NULL,   -- e.g., 'Texte', 'Image', 'Fichier attaché'
        text_content TEXT,
        file_path TEXT,             -- Local path to the archived file (image, pdf, etc.)
        original_id_str TEXT,       -- The ID from the source document for traceability
        FOREIGN KEY (asset_id) REFERENCES InformationAssets(id),
        FOREIGN KEY (parent_id) REFERENCES ContentBlocks(id)
    )""")
    print("  - Table 'ContentBlocks' created or already exists.")

    # --- Annotation and Classification Tables ---

    # Audiences: Defines the target audiences for documents.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Audiences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audience_name TEXT NOT NULL UNIQUE
    )""")
    print("  - Table 'Audiences' created or already exists.")
    
    # AssetAudiences: Links assets to their target audiences (many-to-many).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS AssetAudiences (
        asset_id INTEGER NOT NULL,
        audience_id INTEGER NOT NULL,
        PRIMARY KEY (asset_id, audience_id),
        FOREIGN KEY (asset_id) REFERENCES InformationAssets(id),
        FOREIGN KEY (audience_id) REFERENCES Audiences(id)
    )""")
    print("  - Table 'AssetAudiences' created or already exists.")

    # Tags: Defines keywords for granular classification.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tag_name TEXT NOT NULL UNIQUE
    )""")
    print("  - Table 'Tags' created or already exists.")

    # BlockTags: Links tags to specific content blocks (many-to-many).
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS BlockTags (
        content_block_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY (content_block_id, tag_id),
        FOREIGN KEY (content_block_id) REFERENCES ContentBlocks(id),
        FOREIGN KEY (tag_id) REFERENCES Tags(id)
    )""")
    print("  - Table 'BlockTags' created or already exists.")

    # Annotations: User-generated comments, suggestions, and flags on content blocks.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Annotations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_block_id INTEGER NOT NULL,
        user_id INTEGER, -- Placeholder for a future Users table
        annotation_type TEXT NOT NULL, -- 'Commentaire', 'Suggestion de modification', 'Drapeau'
        content TEXT NOT NULL,
        status TEXT, -- 'Actif', 'Résolu', 'En attente'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (content_block_id) REFERENCES ContentBlocks(id)
    )""")
    print("  - Table 'Annotations' created or already exists.")

    # SemanticLinks: The core table for creating relationships between content blocks.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS SemanticLinks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_content_id INTEGER NOT NULL,
        target_content_id INTEGER NOT NULL,
        relationship_type TEXT NOT NULL, -- e.g., 'Identique à', 'Contredit', 'Précise', 'Inspiré de'
        analysis_notes TEXT,
        user_id INTEGER, -- Placeholder
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (source_content_id) REFERENCES ContentBlocks(id),
        FOREIGN KEY (target_content_id) REFERENCES ContentBlocks(id)
    )""")
    print("  - Table 'SemanticLinks' created or already exists.")

    conn.commit()
    print("Schema creation complete.")

def main():
    """Main function to run the database setup script."""
    parser = argparse.ArgumentParser(description="Create the Knowledge Base SQLite database and schema.")
    parser.add_argument(
        "--db-path",
        default="knowledge_base.db",
        help="Path to the SQLite database file (default: knowledge_base.db)"
    )
    args = parser.parse_args()

    # Ensure the directory for the database exists
    db_dir = os.path.dirname(os.path.abspath(args.db_path))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    try:
        conn = get_db_connection(args.db_path)
        create_schema(conn)
        conn.close()
        print("\nDatabase setup was successful.")
        print(f"You can now find your database at: {os.path.abspath(args.db_path)}")
    except sqlite3.Error as e:
        print(f"\nAn error occurred during database setup: {e}", flush=True)
        # Clean up the potentially corrupted db file if something went wrong
        if 'conn' in locals() and conn:
            conn.close()
        # os.remove(args.db_path)
        # print(f"Removed potentially corrupted database file at {args.db_path}")

if __name__ == "__main__":
    main()
