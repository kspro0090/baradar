#!/usr/bin/env python3
"""
Test script for Google Docs PDF Generator
Tests the placeholder replacement and restoration functionality
"""

import os
import sys
import json
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_basic_functionality():
    """Test basic PDF generation with Google Docs"""
    from google_docs_pdf_generator import generate_pdf_from_google_docs
    
    print("Test 1: Basic PDF Generation")
    print("=" * 50)
    
    # Check for credentials
    if not os.path.exists('credentials.json'):
        print("⚠️  credentials.json not found!")
        print("Please create a service account and download credentials.json")
        return False
    
    # Test document ID (you need to replace this with a real document ID)
    document_id = input("Enter Google Docs document ID (or press Enter to skip): ").strip()
    
    if not document_id:
        print("Skipping Google Docs test - no document ID provided")
        return False
    
    # Test replacements
    replacements = {
        'name': 'محمد رضایی',
        'employee_name': 'محمد رضایی',
        'department': 'بخش فناوری اطلاعات',
        'position': 'مدیر پروژه',
        'date': '1402/11/15',
        'tracking_code': f'TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'leave_type': 'استحقاقی',
        'start_date': '1402/11/20',
        'end_date': '1402/11/25',
        'reason': 'امور شخصی و استراحت'
    }
    
    output_file = f"test_google_docs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    print(f"\nDocument ID: {document_id}")
    print(f"Output file: {output_file}")
    print("\nReplacements:")
    for key, value in replacements.items():
        print(f"  {key}: {value}")
    
    print("\nGenerating PDF...")
    
    try:
        success = generate_pdf_from_google_docs(
            document_id,
            replacements,
            output_file
        )
        
        if success:
            print(f"✅ PDF generated successfully!")
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                print(f"   File size: {size:,} bytes")
                print(f"   Location: {output_file}")
            return True
        else:
            print("❌ PDF generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_service_request_integration():
    """Test integration with service request system"""
    print("\n\nTest 2: Service Request Integration")
    print("=" * 50)
    
    from google_docs_pdf_generator import generate_pdf_for_service_request
    
    # Create mock service request
    class MockFormField:
        def __init__(self, field_name, document_placeholder):
            self.field_name = field_name
            self.document_placeholder = document_placeholder
    
    class MockService:
        def __init__(self, google_doc_id):
            self.google_doc_id = google_doc_id
            self.name = "درخواست مرخصی"
            self.form_fields = [
                MockFormField('employee_name', '{{employee_name}}'),
                MockFormField('department', '{{department}}'),
                MockFormField('leave_type', '{{leave_type}}'),
                MockFormField('start_date', '{{start_date}}'),
                MockFormField('end_date', '{{end_date}}'),
                MockFormField('reason', '{{reason}}')
            ]
    
    class MockServiceRequest:
        def __init__(self, google_doc_id):
            self.tracking_code = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.created_at = datetime.now()
            self.service = MockService(google_doc_id)
            self._form_data = {
                'employee_name': 'سارا احمدی',
                'department': 'منابع انسانی',
                'leave_type': 'استعلاجی',
                'start_date': '1402/12/01',
                'end_date': '1402/12/03',
                'reason': 'ویزیت پزشک'
            }
            self.user = type('User', (), {'username': 'sara.ahmadi'})()
        
        def get_form_data(self):
            return self._form_data
    
    # Get document ID
    document_id = input("\nEnter Google Docs document ID for service test (or press Enter to skip): ").strip()
    
    if not document_id:
        print("Skipping service request test - no document ID provided")
        return False
    
    # Create mock request
    service_request = MockServiceRequest(document_id)
    
    print(f"\nTracking code: {service_request.tracking_code}")
    print("Form data:")
    for key, value in service_request.get_form_data().items():
        print(f"  {key}: {value}")
    
    print("\nGenerating PDF...")
    
    try:
        pdf_filename = generate_pdf_for_service_request(service_request)
        
        if pdf_filename:
            print(f"✅ PDF generated successfully: {pdf_filename}")
            pdf_path = os.path.join('pdf_outputs', pdf_filename)
            if os.path.exists(pdf_path):
                size = os.path.getsize(pdf_path)
                print(f"   File size: {size:,} bytes")
                print(f"   Location: {pdf_path}")
            return True
        else:
            print("❌ PDF generation failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_sample_google_doc_content():
    """Show sample content for a Google Docs template"""
    print("\n\nSample Google Docs Template Content")
    print("=" * 50)
    print("""
Copy this content to a Google Docs file for testing:

=====================================
فرم درخواست مرخصی

نام کارمند: {{employee_name}}
بخش: {{department}}
نوع مرخصی: {{leave_type}}

تاریخ شروع: {{start_date}}
تاریخ پایان: {{end_date}}

دلیل درخواست:
{{reason}}

کد پیگیری: {{tracking_code}}
تاریخ ثبت: {{request_date}}
=====================================

Note: Make sure to share the document with your service account email!
""")

def main():
    """Run all tests"""
    print("Google Docs PDF Generator Test Suite")
    print("=" * 70)
    print()
    
    # Check for required libraries
    try:
        import googleapiclient
        print("✅ Google API libraries installed")
    except ImportError:
        print("❌ Google API libraries not installed")
        print("   Install with: pip install google-api-python-client google-auth")
        return
    
    # Check for credentials
    if os.path.exists('credentials.json'):
        print("✅ credentials.json found")
    else:
        print("❌ credentials.json not found")
        print("   Please set up a service account and download credentials")
        print("   See: https://cloud.google.com/docs/authentication/getting-started")
    
    print()
    
    # Run tests
    test_results = []
    
    # Test 1
    result1 = test_basic_functionality()
    test_results.append(("Basic PDF Generation", result1))
    
    # Test 2
    result2 = test_service_request_integration()
    test_results.append(("Service Request Integration", result2))
    
    # Show sample template
    create_sample_google_doc_content()
    
    # Summary
    print("\n\nTest Summary")
    print("=" * 50)
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    # List generated files
    print("\nGenerated Files:")
    for file in os.listdir('.'):
        if file.startswith('test_google_docs_') and file.endswith('.pdf'):
            print(f"  - {file}")
    
    if os.path.exists('pdf_outputs'):
        for file in os.listdir('pdf_outputs'):
            if file.endswith('.pdf'):
                print(f"  - pdf_outputs/{file}")

if __name__ == "__main__":
    main()