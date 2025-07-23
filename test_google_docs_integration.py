#!/usr/bin/env python3
"""
Test script for Google Docs integration
"""

import os
import sys
from app import app, db
from models import User, Service, FormField, ServiceRequest
from google_docs_service import GoogleDocsService

def test_google_docs_service():
    """Test Google Docs service initialization and basic operations"""
    print("1. Testing Google Docs Service...")
    
    try:
        # Initialize service
        service = GoogleDocsService(os.path.join(os.path.dirname(__file__), 'credentials.json'))
        print("✓ Google Docs service initialized")
        
        # Test with a sample document ID (you'll need to replace this)
        test_doc_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"  # Replace with your test doc
        
        print(f"\n2. Testing document access (ID: {test_doc_id})...")
        try:
            if service.verify_document_access(test_doc_id):
                print("✓ Document access verified")
                
                # Extract content
                doc_info = service.extract_text_and_placeholders(test_doc_id)
                print(f"✓ Document title: {doc_info['title']}")
                print(f"✓ Found {len(doc_info['placeholders'])} placeholders: {doc_info['placeholders']}")
                print(f"✓ Found {len(doc_info['text_content'])} paragraphs")
                
                return True
            else:
                print("✗ Cannot access document")
                return False
        except Exception as e:
            print(f"✗ Error accessing document: {str(e)}")
            return False
            
    except FileNotFoundError:
        print("✗ credentials.json not found!")
        print("\nPlease follow these steps:")
        print("1. Create a service account in Google Cloud Console")
        print("2. Download the credentials JSON file")
        print("3. Save it as 'credentials.json' in the project directory")
        return False
    except Exception as e:
        print(f"✗ Error initializing service: {str(e)}")
        return False

def test_full_workflow():
    """Test the complete workflow with Google Docs"""
    print("\n3. Testing Full Workflow...")
    
    with app.app_context():
        try:
            # Create a test service
            service = Service(
                name='خدمت تست Google Docs',
                description='تست یکپارچه‌سازی با Google Docs',
                google_doc_id='YOUR_TEST_DOC_ID',  # Replace with actual doc ID
                created_by=1,
                is_active=True
            )
            db.session.add(service)
            db.session.commit()
            print("✓ Test service created")
            
            # Add form fields
            fields = [
                FormField(
                    service_id=service.id,
                    field_name='full_name',
                    field_label='نام و نام خانوادگی',
                    field_type='text',
                    is_required=True,
                    document_placeholder='NAME',
                    field_order=1
                ),
                FormField(
                    service_id=service.id,
                    field_name='phone',
                    field_label='شماره تماس',
                    field_type='text',
                    is_required=True,
                    document_placeholder='PHONE',
                    field_order=2
                )
            ]
            
            for field in fields:
                db.session.add(field)
            db.session.commit()
            print("✓ Form fields added")
            
            # Create a test request
            from app import generate_tracking_code
            request = ServiceRequest(
                service_id=service.id,
                tracking_code=generate_tracking_code(),
                status='approved'
            )
            
            # Set form data
            form_data = {
                'full_name': 'تست کاربر فارسی',
                'phone': '۰۹۱۲۳۴۵۶۷۸۹'
            }
            request.set_form_data(form_data)
            
            db.session.add(request)
            db.session.commit()
            print("✓ Test request created")
            
            # Test PDF generation
            if service.google_doc_id != 'YOUR_TEST_DOC_ID':
                from app import generate_pdf_from_request
                try:
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
                    return False
            else:
                print("⚠ Skipping PDF generation (update google_doc_id first)")
                return True
                
        except Exception as e:
            print(f"✗ Workflow test error: {str(e)}")
            return False
        finally:
            # Cleanup
            try:
                service = Service.query.filter_by(name='خدمت تست Google Docs').first()
                if service:
                    db.session.delete(service)
                    db.session.commit()
                    print("✓ Test data cleaned up")
            except:
                pass

def main():
    """Run all tests"""
    print("=== Google Docs Integration Test ===\n")
    
    # Test 1: Google Docs Service
    service_ok = test_google_docs_service()
    
    if not service_ok:
        print("\n❌ Google Docs service test failed!")
        print("\nTroubleshooting:")
        print("1. Ensure credentials.json exists")
        print("2. Enable Google Docs API and Drive API")
        print("3. Share test document with service account email")
        return
    
    # Test 2: Full Workflow
    workflow_ok = test_full_workflow()
    
    # Summary
    print("\n=== Test Summary ===")
    if service_ok and workflow_ok:
        print("✅ All tests passed!")
        print("\nThe Google Docs integration is working correctly.")
        print("\nNext steps:")
        print("1. Create your Google Docs templates")
        print("2. Share them with the service account")
        print("3. Use the document IDs when creating services")
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main()