#!/usr/bin/env python3
"""
Migration script to update database schema for Google Docs integration
"""

import os
import sys
from sqlalchemy import create_engine, text
from config import Config

def migrate_database():
    """Migrate database schema to support Google Docs"""
    
    # Create engine
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    print("Starting database migration...")
    
    try:
        with engine.connect() as conn:
            # Check if google_doc_id column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='services' AND column_name='google_doc_id'
            """))
            
            if result.rowcount == 0:
                print("Adding google_doc_id column to services table...")
                conn.execute(text("""
                    ALTER TABLE services 
                    ADD COLUMN google_doc_id VARCHAR(255)
                """))
                conn.commit()
                print("✓ Added google_doc_id column")
            else:
                print("✓ google_doc_id column already exists")
            
            # Check if we need to migrate data
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM services 
                WHERE template_filename IS NOT NULL 
                AND google_doc_id IS NULL
            """))
            
            count = result.fetchone()[0]
            if count > 0:
                print(f"\n⚠️  Found {count} services with local templates")
                print("You'll need to:")
                print("1. Create Google Docs for each template")
                print("2. Update the google_doc_id field manually")
                print("\nExample SQL:")
                print("UPDATE services SET google_doc_id = 'YOUR_DOC_ID' WHERE id = SERVICE_ID;")
            
            # Drop fonts table if exists
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_name='fonts'
            """))
            
            if result.rowcount > 0:
                print("\n⚠️  Fonts table found")
                response = input("Remove fonts table? (y/n): ")
                if response.lower() == 'y':
                    conn.execute(text("DROP TABLE fonts"))
                    conn.commit()
                    print("✓ Removed fonts table")
            
            print("\n✅ Migration completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        return False
    
    return True

def main():
    """Main function"""
    print("=== Google Docs Migration Script ===\n")
    
    if not os.path.exists('service_requests.db'):
        print("No database found. Nothing to migrate.")
        return
    
    print("This script will update your database schema for Google Docs integration.")
    print("\n⚠️  Please backup your database before continuing!")
    
    response = input("\nContinue with migration? (y/n): ")
    if response.lower() != 'y':
        print("Migration cancelled.")
        return
    
    if migrate_database():
        print("\nNext steps:")
        print("1. Create Google Docs templates for your services")
        print("2. Share them with your service account")
        print("3. Update the google_doc_id field for each service")
        print("4. Test the system with the new integration")

if __name__ == '__main__':
    main()