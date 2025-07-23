#!/usr/bin/env python3
"""
Test script for PDF generation with Persian text
This script tests the PDF generation functionality with sample Persian data
"""

import os
import sys
from datetime import datetime
from app import app, db, generate_pdf_from_request
from models import User, Service, FormField, ServiceRequest, Font

def create_test_data():
    """Create test data for PDF generation"""
    with app.app_context():
        # Ensure database is initialized
        db.create_all()
        
        # Check if we have a default font
        default_font = Font.query.filter_by(is_default=True).first()
        if not default_font:
            print("⚠️  No default font found. Please run: python3 add_sample_font.py")
            return None
        else:
            print(f"✓ Using font: {default_font.name}")
        
        # Create or get test service
        service = Service.query.filter_by(name='خدمت تست PDF').first()
        if not service:
            service = Service(
                name='خدمت تست PDF',
                description='این یک خدمت تست برای بررسی تولید PDF فارسی است',
                created_by=1,
                is_active=True
            )
            db.session.add(service)
            db.session.commit()
            print("✓ Created test service")
        
        # Create form fields if they don't exist
        if service.form_fields.count() == 0:
            fields = [
                {
                    'field_name': 'full_name',
                    'field_label': 'نام و نام خانوادگی',
                    'field_type': 'text',
                    'document_placeholder': 'FULLNAME',
                    'field_order': 1
                },
                {
                    'field_name': 'national_code',
                    'field_label': 'کد ملی',
                    'field_type': 'text',
                    'document_placeholder': 'NATIONALCODE',
                    'field_order': 2
                },
                {
                    'field_name': 'phone',
                    'field_label': 'شماره تماس',
                    'field_type': 'text',
                    'document_placeholder': 'PHONE',
                    'field_order': 3
                },
                {
                    'field_name': 'address',
                    'field_label': 'آدرس',
                    'field_type': 'textarea',
                    'document_placeholder': 'ADDRESS',
                    'field_order': 4
                },
                {
                    'field_name': 'description',
                    'field_label': 'توضیحات',
                    'field_type': 'textarea',
                    'document_placeholder': 'DESCRIPTION',
                    'field_order': 5
                }
            ]
            
            for field_data in fields:
                field = FormField(service_id=service.id, **field_data)
                db.session.add(field)
            
            db.session.commit()
            print("✓ Created form fields")
        
        # Create a test request
        test_request = ServiceRequest(
            service_id=service.id,
            tracking_code='TEST123456',
            status='approved'
        )
        
        # Set Persian form data
        form_data = {
            'full_name': 'محمد رضا احمدی',
            'national_code': '۱۲۳۴۵۶۷۸۹۰',
            'phone': '۰۹۱۲۳۴۵۶۷۸۹',
            'address': 'تهران، خیابان ولیعصر، پلاک ۱۲۳، واحد ۴',
            'description': 'این یک متن تست فارسی است که شامل حروف فارسی، اعداد فارسی و انگلیسی می‌باشد. همچنین علائم نگارشی مثل ؟ ! ، ؛ : و پرانتز (تست) را شامل می‌شود.'
        }
        
        test_request.set_form_data(form_data)
        db.session.add(test_request)
        db.session.commit()
        
        print("✓ Created test request")
        return test_request

def test_pdf_generation():
    """Test PDF generation"""
    print("\n=== Testing PDF Generation ===\n")
    
    # Create test data
    test_request = create_test_data()
    if not test_request:
        return False
    
    # Generate PDF
    try:
        print("\nGenerating PDF...")
        pdf_filename = generate_pdf_from_request(test_request)
        pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
        
        if os.path.exists(pdf_path):
            file_size = os.path.getsize(pdf_path)
            print(f"✓ PDF generated successfully: {pdf_filename}")
            print(f"  File size: {file_size:,} bytes")
            print(f"  Location: {pdf_path}")
            
            # Cleanup test data
            with app.app_context():
                db.session.delete(test_request)
                db.session.commit()
            
            return True
        else:
            print("✗ PDF file was not created")
            return False
            
    except Exception as e:
        print(f"✗ Error generating PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_font_files():
    """Check if font files exist and are accessible"""
    print("\n=== Checking Font Files ===\n")
    
    with app.app_context():
        fonts = Font.query.all()
        if not fonts:
            print("⚠️  No fonts found in database")
            return False
        
        all_good = True
        for font in fonts:
            font_path = os.path.join(app.config['FONTS_FOLDER'], font.filename)
            if os.path.exists(font_path):
                file_size = os.path.getsize(font_path)
                status = "✓"
                if font.is_default:
                    status += " (DEFAULT)"
                print(f"{status} {font.name}: {font.filename} ({file_size:,} bytes)")
            else:
                print(f"✗ {font.name}: {font.filename} - FILE NOT FOUND")
                all_good = False
        
        return all_good

def main():
    """Main test function"""
    print("=== Persian PDF Generation Test ===\n")
    
    # Check font files
    fonts_ok = check_font_files()
    if not fonts_ok:
        print("\n⚠️  Font issues detected. Please ensure fonts are properly uploaded.")
        print("Run: python3 add_sample_font.py")
    
    # Test PDF generation
    pdf_ok = test_pdf_generation()
    
    print("\n=== Test Summary ===")
    print(f"Font files: {'✓ OK' if fonts_ok else '✗ Issues found'}")
    print(f"PDF generation: {'✓ OK' if pdf_ok else '✗ Failed'}")
    
    if fonts_ok and pdf_ok:
        print("\n✓ All tests passed! Persian PDF generation is working correctly.")
    else:
        print("\n✗ Some tests failed. Please check the errors above.")

if __name__ == '__main__':
    main()