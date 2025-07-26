#!/usr/bin/env python3
"""
Simple migration script to add image-based form support to existing database
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect

def migrate_image_forms():
    """Add new columns for image-based forms to existing services table"""
    
    # Database configuration
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    
    try:
        # Create engine
        engine = create_engine(database_url)
        
        # Check if columns already exist
        inspector = inspect(engine)
        existing_columns = [col['name'] for col in inspector.get_columns('services')]
        
        # Columns to add
        new_columns = [
            'form_type',
            'image_path', 
            'form_design_data',
            'page_size'
        ]
        
        # Add missing columns
        for column in new_columns:
            if column not in existing_columns:
                if column == 'form_type':
                    # Add form_type column with default value
                    engine.execute(text(
                        "ALTER TABLE services ADD COLUMN form_type VARCHAR(20) DEFAULT 'google_doc'"
                    ))
                    print(f"Added column: {column}")
                    
                elif column == 'image_path':
                    # Add image_path column
                    engine.execute(text(
                        "ALTER TABLE services ADD COLUMN image_path VARCHAR(500)"
                    ))
                    print(f"Added column: {column}")
                    
                elif column == 'form_design_data':
                    # Add form_design_data column
                    engine.execute(text(
                        "ALTER TABLE services ADD COLUMN form_design_data TEXT"
                    ))
                    print(f"Added column: {column}")
                    
                elif column == 'page_size':
                    # Add page_size column with default value
                    engine.execute(text(
                        "ALTER TABLE services ADD COLUMN page_size VARCHAR(10) DEFAULT 'A4'"
                    ))
                    print(f"Added column: {column}")
            else:
                print(f"Column {column} already exists")
        
        # Update existing services to have form_type = 'google_doc'
        engine.execute(text(
            "UPDATE services SET form_type = 'google_doc' WHERE form_type IS NULL"
        ))
        print("Updated existing services to use Google Docs form type")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Error during migration: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    migrate_image_forms()