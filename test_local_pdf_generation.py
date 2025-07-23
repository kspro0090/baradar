#!/usr/bin/env python3
"""
Test script for local PDF generation
Tests the new approach that doesn't modify Google Drive templates
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Service, ServiceRequest
from document_processor import DocumentProcessor
from google_docs_service import GoogleDocsService

def test_document_processor():
    """Test the document processor with sample data"""
    print("\n=== Testing Document Processor ===\n")
    
    processor = DocumentProcessor()
    
    # Test data
    replacements = {
        'name': 'احمد محمدی',
        'email': 'ahmad@example.com',
        'date': '1402/10/15',
        'department': 'بخش فناوری اطلاعات'
    }
    
    # Test HTML processing
    html_template = """
    <html>
    <body>
        <h1>درخواست خدمت</h1>
        <p>نام: {{name}}</p>
        <p>ایمیل: {{email}}</p>
        <p>تاریخ: {{date}}</p>
        <p>بخش: {{department}}</p>
    </body>
    </html>
    """.encode('utf-8')
    
    try:
        processed_html = processor.process_html_template(html_template, replacements)
        print("✓ HTML template processed successfully")
        
        # Generate PDF from HTML
        test_pdf_path = "test_output.pdf"
        if processor.generate_pdf_from_html(processed_html, test_pdf_path):
            print(f"✓ PDF generated from HTML: {test_pdf_path}")
            print(f"  File size: {os.path.getsize(test_pdf_path):,} bytes")
            os.unlink(test_pdf_path)  # Clean up
        else:
            print("✗ Failed to generate PDF from HTML")
            
    except Exception as e:
        print(f"✗ Error in document processing: {str(e)}")
        return False
    
    return True

def test_google_docs_export():
    """Test Google Docs export functionality"""
    print("\n=== Testing Google Docs Export ===\n")
    
    with app.app_context():
        # Get a service with a template
        service = Service.query.filter(Service.google_doc_id.isnot(None)).first()
        
        if not service:
            print("✗ No service with Google Doc template found")
            return False
        
        print(f"Using service: {service.name}")
        print(f"Template ID: {service.google_doc_id}")
        
        try:
            google_service = GoogleDocsService()
            
            # Test DOCX export
            print("\nTesting DOCX export...")
            docx_data = google_service.export_as_docx(service.google_doc_id)
            print(f"✓ DOCX exported: {len(docx_data):,} bytes")
            
            # Test HTML export
            print("\nTesting HTML export...")
            html_data = google_service.export_as_html(service.google_doc_id)
            print(f"✓ HTML exported: {len(html_data):,} bytes")
            
            # Test PDF export
            print("\nTesting PDF export...")
            pdf_data = google_service.export_as_pdf(service.google_doc_id)
            print(f"✓ PDF exported: {len(pdf_data):,} bytes")
            
            return True
            
        except Exception as e:
            print(f"✗ Error exporting from Google Docs: {str(e)}")
            return False

def test_full_pdf_generation():
    """Test the complete PDF generation flow"""
    print("\n=== Testing Full PDF Generation Flow ===\n")
    
    with app.app_context():
        # Get a pending request
        request = ServiceRequest.query.filter_by(status='pending').first()
        
        if not request:
            print("✗ No pending requests found")
            return False
        
        print(f"Using request: {request.tracking_code}")
        print(f"Service: {request.service.name}")
        
        try:
            from app import generate_pdf_from_request
            
            # Generate PDF
            pdf_filename = generate_pdf_from_request(request)
            pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
            
            if os.path.exists(pdf_path):
                file_size = os.path.getsize(pdf_path)
                print(f"✓ PDF generated successfully: {pdf_filename}")
                print(f"  File size: {file_size:,} bytes")
                print(f"  Location: {pdf_path}")
                return True
            else:
                print("✗ PDF file was not created")
                return False
                
        except Exception as e:
            print(f"✗ Error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run all tests"""
    print("=== Local PDF Generation Test Suite ===\n")
    
    results = []
    
    # Test document processor
    results.append(("Document Processor", test_document_processor()))
    
    # Test Google Docs export
    if os.path.exists('credentials.json'):
        results.append(("Google Docs Export", test_google_docs_export()))
        results.append(("Full PDF Generation", test_full_pdf_generation()))
    else:
        print("\n⚠ Skipping Google Docs tests - credentials.json not found")
    
    # Summary
    print("\n=== Test Summary ===\n")
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
    
    return all_passed

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)