#!/usr/bin/env python3
"""
Migration script to add auto-approval fields to Service model
"""

from app import app, db
from sqlalchemy import text

def upgrade():
    """Add auto-approval fields to services table"""
    with app.app_context():
        try:
            # Add auto_approve_enabled column
            db.session.execute(text('''
                ALTER TABLE services 
                ADD COLUMN auto_approve_enabled BOOLEAN DEFAULT FALSE
            '''))
            
            # Add auto_approve_sheet_id column
            db.session.execute(text('''
                ALTER TABLE services 
                ADD COLUMN auto_approve_sheet_id VARCHAR(255) DEFAULT '1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ'
            '''))
            
            # Add auto_approve_sheet_column column
            db.session.execute(text('''
                ALTER TABLE services 
                ADD COLUMN auto_approve_sheet_column VARCHAR(10) DEFAULT 'A'
            '''))
            
            # Add auto_approve_field_name column
            db.session.execute(text('''
                ALTER TABLE services 
                ADD COLUMN auto_approve_field_name VARCHAR(100)
            '''))
            
            db.session.commit()
            print("✅ Auto-approval fields added successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error adding fields: {str(e)}")
            print("   Fields may already exist.")

def downgrade():
    """Remove auto-approval fields from services table"""
    with app.app_context():
        try:
            db.session.execute(text('ALTER TABLE services DROP COLUMN auto_approve_enabled'))
            db.session.execute(text('ALTER TABLE services DROP COLUMN auto_approve_sheet_id'))
            db.session.execute(text('ALTER TABLE services DROP COLUMN auto_approve_sheet_column'))
            db.session.execute(text('ALTER TABLE services DROP COLUMN auto_approve_field_name'))
            db.session.commit()
            print("✅ Auto-approval fields removed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error removing fields: {str(e)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'downgrade':
        downgrade()
    else:
        upgrade()