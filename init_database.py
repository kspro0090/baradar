#!/usr/bin/env python3
"""
Initialize database with proper schema including image-based form support
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def init_database():
    """Initialize database with proper schema"""
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Create users table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Created users table")
            
            # Create services table with image form support
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    google_doc_id VARCHAR(255),
                    form_type VARCHAR(20) DEFAULT 'google_doc',
                    image_path VARCHAR(500),
                    form_design_data TEXT,
                    page_size VARCHAR(10) DEFAULT 'A4',
                    created_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES users (id)
                )
            """))
            print("Created services table")
            
            # Create form_fields table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS form_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id INTEGER NOT NULL,
                    field_label VARCHAR(100) NOT NULL,
                    field_name VARCHAR(100) NOT NULL,
                    field_type VARCHAR(20) DEFAULT 'text',
                    is_required BOOLEAN DEFAULT 0,
                    placeholder VARCHAR(200),
                    document_placeholder VARCHAR(200),
                    options TEXT,
                    field_order INTEGER DEFAULT 0,
                    FOREIGN KEY (service_id) REFERENCES services (id)
                )
            """))
            print("Created form_fields table")
            
            # Create service_requests table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS service_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    tracking_code VARCHAR(20) UNIQUE NOT NULL,
                    form_data TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    approved_at DATETIME,
                    approved_by INTEGER,
                    notes TEXT,
                    FOREIGN KEY (service_id) REFERENCES services (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (approved_by) REFERENCES users (id)
                )
            """))
            print("Created service_requests table")
            
            conn.commit()
        
        print("Database initialization completed successfully!")
        
    except Exception as e:
        print(f"Error during database initialization: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    init_database()