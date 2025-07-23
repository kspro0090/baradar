#!/usr/bin/env python3
"""Test script to verify Flask application functionality"""

import os
import sys
from app import app, db, User
from models import Service, FormField, ServiceRequest, Font

def test_database_connection():
    """Test database connection and table creation"""
    print("Testing database connection...")
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created successfully")
            return True
        except Exception as e:
            print(f"✗ Database error: {str(e)}")
            return False

def test_admin_user():
    """Test if admin user exists or can be created"""
    print("\nTesting admin user...")
    with app.app_context():
        try:
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print("✓ Admin user already exists")
                # Test password
                if admin.check_password('admin123'):
                    print("✓ Admin password is correct")
                else:
                    print("✗ Admin password is incorrect")
            else:
                print("✗ Admin user not found")
                print("  Run: flask --app app.py init-db")
            return True
        except Exception as e:
            print(f"✗ Error checking admin user: {str(e)}")
            return False

def test_directories():
    """Test if required directories exist"""
    print("\nTesting directories...")
    directories = [
        'uploads/docx_templates',
        'uploads/user_requests',
        'pdf_outputs',
        'static/fonts'
    ]
    
    all_exist = True
    for directory in directories:
        if os.path.exists(directory):
            print(f"✓ Directory exists: {directory}")
        else:
            print(f"✗ Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test if all required packages can be imported"""
    print("\nTesting package imports...")
    packages = [
        'flask',
        'flask_login',
        'flask_sqlalchemy',
        'flask_wtf',
        'wtforms',
        'docx',
        'reportlab',
        'arabic_reshaper',
        'bidi'
    ]
    
    all_imported = True
    for package in packages:
        try:
            __import__(package)
            print(f"✓ {package} imported successfully")
        except ImportError:
            print(f"✗ Failed to import {package}")
            all_imported = False
    
    return all_imported

def main():
    """Run all tests"""
    print("=== Flask Persian Service Request System Test ===\n")
    
    tests = [
        test_imports,
        test_database_connection,
        test_admin_user,
        test_directories
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n=== Test Summary ===")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed! The application should work correctly.")
        print("\nTo run the application:")
        print("  python app.py")
        print("\nDefault admin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")

if __name__ == '__main__':
    main()