#!/usr/bin/env python3
"""
Simple test for PDF generation with ReportLab
"""

import os
from datetime import datetime
from pdf_generator_no_copy import generate_pdf_fallback

def create_simple_request():
    """Create a simple mock request"""
    
    class MockFormField:
        def __init__(self, field_name, field_label, document_placeholder):
            self.field_name = field_name
            self.field_label = field_label
            self.document_placeholder = document_placeholder
    
    class MockService:
        def __init__(self):
            self.name = "درخواست مرخصی"
            self.form_fields = [
                MockFormField('employee_name', 'نام کارمند', '{{employee_name}}'),
                MockFormField('department', 'بخش', '{{department}}'),
                MockFormField('leave_type', 'نوع مرخصی', '{{leave_type}}'),
                MockFormField('start_date', 'تاریخ شروع', '{{start_date}}'),
                MockFormField('end_date', 'تاریخ پایان', '{{end_date}}'),
            ]
    
    class MockServiceRequest:
        def __init__(self):
            self.tracking_code = f"REQ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            self.created_at = datetime.now()
            self.service = MockService()
            self._form_data = {
                'employee_name': 'احمد رضایی',
                'department': 'منابع انسانی',
                'leave_type': 'استعلاجی',
                'start_date': '1402/11/10',
                'end_date': '1402/11/12',
            }
        
        def get_form_data(self):
            return self._form_data
    
    return MockServiceRequest()

def test_simple_pdf():
    """Test simple PDF generation"""
    print("Simple PDF Generation Test")
    print("=" * 50)
    
    # Create request
    request = create_simple_request()
    print(f"Tracking code: {request.tracking_code}")
    
    # Generate PDF
    try:
        pdf_filename = generate_pdf_fallback(request)
        
        if pdf_filename:
            print(f"✓ PDF generated: {pdf_filename}")
            
            # Check file
            pdf_path = os.path.join('pdf_outputs', pdf_filename)
            if os.path.exists(pdf_path):
                size = os.path.getsize(pdf_path)
                print(f"  File size: {size:,} bytes")
                print(f"  Location: {pdf_path}")
            else:
                print("  Warning: File not found at expected location")
        else:
            print("✗ PDF generation failed")
            
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    test_simple_pdf()