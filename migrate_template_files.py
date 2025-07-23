#!/usr/bin/env python3
"""
Migration script to add TemplateFile model and update ServiceRequest model
"""

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.exc import OperationalError

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from models import db, Service, ServiceRequest, TemplateFile
from app import app

def migrate_database():
    """Add TemplateFile table and update ServiceRequest table"""
    
    print("Starting database migration for template files...")
    
    with app.app_context():
        try:
            # Create TemplateFile table
            print("Creating TemplateFile table...")
            db.create_all()
            
            # Check if template_file_id column exists in service_requests table
            engine = db.get_engine()
            inspector = db.inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('service_requests')]
            
            if 'template_file_id' not in columns:
                print("Adding template_file_id column to service_requests table...")
                with engine.connect() as conn:
                    conn.execute('ALTER TABLE service_requests ADD COLUMN template_file_id INTEGER')
                    conn.execute('ALTER TABLE service_requests ADD FOREIGN KEY (template_file_id) REFERENCES template_files(id)')
                    conn.commit()
            
            # Migrate existing services to have at least one template file
            print("Checking existing services for template files...")
            services = Service.query.all()
            
            for service in services:
                if service.google_doc_id and service.template_files.count() == 0:
                    print(f"Adding default template for service: {service.name}")
                    template = TemplateFile(
                        service_id=service.id,
                        file_id=service.google_doc_id,
                        file_name=f"Default template for {service.name}",
                        used=False
                    )
                    db.session.add(template)
            
            db.session.commit()
            print("Migration completed successfully!")
            
            # Print summary
            print("\nMigration Summary:")
            print(f"Total services: {Service.query.count()}")
            print(f"Total template files: {TemplateFile.query.count()}")
            print(f"Services with templates: {Service.query.join(TemplateFile).distinct().count()}")
            
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate_database()