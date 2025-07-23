#!/usr/bin/env python3
"""
Comprehensive test script for the Flask Persian Service Request System
Tests all major functionality including login, service creation, and PDF generation
"""

import os
import sys
import json
from app import app, db
from models import User, Service, FormField, ServiceRequest, Font

def test_imports():
    """Test all required imports"""
    print("1. Testing imports...")
    try:
        import flask
        import flask_login
        import flask_sqlalchemy
        import flask_wtf
        import wtforms
        import docx
        import reportlab
        import arabic_reshaper
        import bidi
        import requests
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {str(e)}")
        return False

def test_database():
    """Test database initialization"""
    print("\n2. Testing database...")
    with app.app_context():
        try:
            db.create_all()
            print("✓ Database tables created")
            return True
        except Exception as e:
            print(f"✗ Database error: {str(e)}")
            return False

def test_admin_user():
    """Test admin user creation and login"""
    print("\n3. Testing admin user...")
    with app.app_context():
        try:
            # Check if admin exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                # Create admin user
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='system_manager'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✓ Admin user created")
            else:
                print("✓ Admin user already exists")
            
            # Test password
            if admin.check_password('admin123'):
                print("✓ Admin password verification successful")
                return True
            else:
                print("✗ Admin password verification failed")
                return False
                
        except Exception as e:
            print(f"✗ Error with admin user: {str(e)}")
            return False

def test_font_setup():
    """Test Persian font setup"""
    print("\n4. Testing font setup...")
    with app.app_context():
        try:
            # Check if any font exists
            font = Font.query.filter_by(is_default=True).first()
            if not font:
                print("⚠ No default font found")
                # Try to add Vazir font
                try:
                    import requests
                    font_path = os.path.join(app.config['FONTS_FOLDER'], 'Vazir-Test.ttf')
                    if not os.path.exists(font_path):
                        print("  Downloading Vazir font...")
                        response = requests.get("https://github.com/rastikerdar/vazir-font/raw/v30.1.0/dist/Vazir-Regular.ttf")
                        with open(font_path, 'wb') as f:
                            f.write(response.content)
                    
                    # Add to database
                    font = Font(
                        name="Vazir Test",
                        filename="Vazir-Test.ttf",
                        is_default=True
                    )
                    db.session.add(font)
                    db.session.commit()
                    print("✓ Vazir font added and set as default")
                except Exception as e:
                    print(f"✗ Could not setup font: {str(e)}")
                    return False
            else:
                print(f"✓ Default font found: {font.name}")
            
            return True
            
        except Exception as e:
            print(f"✗ Font setup error: {str(e)}")
            return False

def test_service_creation():
    """Test service creation with fields"""
    print("\n5. Testing service creation...")
    with app.app_context():
        try:
            # Create a test service
            service = Service(
                name='خدمت تست سیستم',
                description='این یک خدمت تست برای بررسی عملکرد سیستم است',
                created_by=1,
                is_active=True
            )
            db.session.add(service)
            db.session.commit()
            print("✓ Service created")
            
            # Add form fields
            fields = [
                FormField(
                    service_id=service.id,
                    field_name='full_name',
                    field_label='نام و نام خانوادگی',
                    field_type='text',
                    is_required=True,
                    document_placeholder='FULLNAME',
                    field_order=1
                ),
                FormField(
                    service_id=service.id,
                    field_name='description',
                    field_label='توضیحات',
                    field_type='textarea',
                    is_required=False,
                    document_placeholder='DESCRIPTION',
                    field_order=2
                )
            ]
            
            for field in fields:
                db.session.add(field)
            db.session.commit()
            print("✓ Form fields added")
            
            return service.id
            
        except Exception as e:
            print(f"✗ Service creation error: {str(e)}")
            return None

def test_request_submission(service_id):
    """Test service request submission"""
    print("\n6. Testing request submission...")
    with app.app_context():
        try:
            from app import generate_tracking_code
            
            # Create a test request
            request = ServiceRequest(
                service_id=service_id,
                tracking_code=generate_tracking_code(),
                status='pending'
            )
            
            # Set form data
            form_data = {
                'full_name': 'تست کاربر فارسی',
                'description': 'این یک درخواست تست با متن فارسی است. شامل اعداد ۱۲۳۴۵ و علائم نگارشی!'
            }
            request.set_form_data(form_data)
            
            db.session.add(request)
            db.session.commit()
            print(f"✓ Request submitted with tracking code: {request.tracking_code}")
            
            return request.id
            
        except Exception as e:
            print(f"✗ Request submission error: {str(e)}")
            return None

def test_pdf_generation(request_id):
    """Test PDF generation with Persian text"""
    print("\n7. Testing PDF generation...")
    with app.app_context():
        try:
            from app import generate_pdf_from_request
            
            # Get the request
            request = ServiceRequest.query.get(request_id)
            if not request:
                print("✗ Request not found")
                return False
            
            # Approve the request
            request.status = 'approved'
            db.session.commit()
            
            # Generate PDF
            pdf_filename = generate_pdf_from_request(request)
            pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"✓ PDF generated: {pdf_filename} ({file_size:,} bytes)")
                return True
            else:
                print("✗ PDF file not created")
                return False
                
        except Exception as e:
            print(f"✗ PDF generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def test_app_routes():
    """Test that main routes are accessible"""
    print("\n8. Testing app routes...")
    with app.test_client() as client:
        try:
            # Test home page
            response = client.get('/')
            if response.status_code == 200:
                print("✓ Home page accessible")
            else:
                print(f"✗ Home page error: {response.status_code}")
            
            # Test login page
            response = client.get('/login')
            if response.status_code == 200:
                print("✓ Login page accessible")
            else:
                print(f"✗ Login page error: {response.status_code}")
            
            # Test tracking page
            response = client.get('/track')
            if response.status_code == 200:
                print("✓ Tracking page accessible")
            else:
                print(f"✗ Tracking page error: {response.status_code}")
            
            return True
            
        except Exception as e:
            print(f"✗ Route testing error: {str(e)}")
            return False

def cleanup_test_data():
    """Clean up test data"""
    print("\n9. Cleaning up test data...")
    with app.app_context():
        try:
            # Delete test service and related data
            service = Service.query.filter_by(name='خدمت تست سیستم').first()
            if service:
                db.session.delete(service)
                db.session.commit()
                print("✓ Test data cleaned up")
            return True
        except Exception as e:
            print(f"✗ Cleanup error: {str(e)}")
            return False

def main():
    """Run all tests"""
    print("=== Flask Persian Service Request System - Full Test ===\n")
    
    results = []
    
    # Run tests
    results.append(test_imports())
    results.append(test_database())
    results.append(test_admin_user())
    results.append(test_font_setup())
    
    service_id = test_service_creation()
    results.append(service_id is not None)
    
    if service_id:
        request_id = test_request_submission(service_id)
        results.append(request_id is not None)
        
        if request_id:
            results.append(test_pdf_generation(request_id))
    
    results.append(test_app_routes())
    results.append(cleanup_test_data())
    
    # Summary
    print("\n=== Test Summary ===")
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ All tests passed! The system is working correctly.")
        print("\nYou can now:")
        print("1. Run the app: python app.py")
        print("2. Login with: admin / admin123")
        print("3. Create services and test the full workflow")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("\nCommon fixes:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run font setup: python add_sample_font.py")
        print("3. Check file permissions in uploads/ and static/fonts/")

if __name__ == '__main__':
    main()