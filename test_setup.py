#!/usr/bin/env python
"""Test script to verify the Flask service request system setup"""

import sys

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    try:
        import flask
        print("✓ Flask")
        
        import flask_login
        print("✓ Flask-Login")
        
        import flask_sqlalchemy
        print("✓ Flask-SQLAlchemy")
        
        import flask_wtf
        print("✓ Flask-WTF")
        
        import docx
        print("✓ python-docx")
        
        import reportlab
        print("✓ ReportLab")
        
        import arabic_reshaper
        print("✓ arabic-reshaper")
        
        import bidi
        print("✓ python-bidi")
        
        print("\nAll imports successful!")
        return True
        
    except ImportError as e:
        print(f"\n✗ Import error: {e}")
        print("\nPlease install requirements: pip install -r requirements.txt")
        return False

def test_app():
    """Test if the Flask app can be created"""
    print("\nTesting Flask app creation...")
    try:
        from app import app, db
        print("✓ App created successfully")
        
        with app.app_context():
            # Test database creation
            db.create_all()
            print("✓ Database tables created")
            
            # Test models
            from models import User, Service, FormField, ServiceRequest, Font
            print("✓ Models loaded successfully")
            
        return True
        
    except Exception as e:
        print(f"\n✗ App error: {e}")
        return False

def main():
    print("Service Request System - Setup Test")
    print("=" * 40)
    
    if not test_imports():
        sys.exit(1)
    
    if not test_app():
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("✓ All tests passed!")
    print("\nYou can now run the app with: python app.py")
    print("Default login: admin / admin123")
    print("Access at: http://localhost:5000")

if __name__ == "__main__":
    main()