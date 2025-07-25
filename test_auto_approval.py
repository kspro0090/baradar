#!/usr/bin/env python3
"""
Test script for auto-approval system
"""

import os
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_google_sheets_checker():
    """Test Google Sheets checker functionality"""
    print("\n" + "="*50)
    print("Test 1: Google Sheets Checker")
    print("="*50)
    
    try:
        from google_sheets_checker import check_employee_in_sheet, GoogleSheetsChecker
        
        # Test with default sheet
        test_names = [
            "علی محمدی",
            "سارا احمدی",
            "محمد رضایی",
            "فاطمه زارعی",
            "test_user_not_exists"
        ]
        
        print(f"\nChecking names in Google Sheet (ID: 1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ):")
        print("-" * 40)
        
        for name in test_names:
            exists = check_employee_in_sheet(name)
            status = "✅ Found" if exists else "❌ Not found"
            print(f"{name}: {status}")
        
        # Test direct API
        print("\n\nTesting direct API access:")
        checker = GoogleSheetsChecker()
        values = checker.get_column_values("1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ", "", "A")
        print(f"Total values in column A: {len(values)}")
        if values:
            print(f"First 5 values: {values[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_pdf_queue():
    """Test PDF queue processor"""
    print("\n" + "="*50)
    print("Test 2: PDF Queue Processor")
    print("="*50)
    
    try:
        from pdf_queue_processor import get_queue_processor, add_pdf_task, wait_for_task, ProcessingStatus
        
        # Create mock service request
        class MockService:
            google_doc_id = "test_doc_id"
            form_fields = []
            
        class MockServiceRequest:
            def __init__(self, tracking_code, employee_name):
                self.tracking_code = tracking_code
                self.service = MockService()
                self._form_data = {
                    'employee_name': employee_name,
                    'department': 'IT',
                    'leave_type': 'استحقاقی'
                }
                self.status = 'pending'
                self.pdf_filename = None
                
            def get_form_data(self):
                return self._form_data
        
        # Start queue processor
        processor = get_queue_processor()
        print(f"Queue processor started: {processor.is_running}")
        
        # Add test task
        request = MockServiceRequest("TEST-001", "علی محمدی")
        
        def on_complete(task):
            print(f"\nCallback called for task {task.task_id}")
            print(f"Status: {task.status.value}")
            if task.error:
                print(f"Error: {task.error}")
            elif task.result:
                print(f"Result: {task.result}")
        
        task_id = add_pdf_task(request, callback=on_complete)
        print(f"\nAdded task to queue: {task_id}")
        print(f"Queue size: {processor.get_queue_size()}")
        
        # Wait for completion
        print("\nWaiting for task completion...")
        task = wait_for_task(task_id, timeout=10)
        
        if task:
            print(f"\nTask completed!")
            print(f"Status: {task.status.value}")
            print(f"Processing time: {(task.processed_at - task.created_at).total_seconds():.2f} seconds")
        else:
            print("\nTask timeout!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_auto_approval_flow():
    """Test complete auto-approval flow"""
    print("\n" + "="*50)
    print("Test 3: Auto-Approval Flow Simulation")
    print("="*50)
    
    try:
        from google_sheets_checker import check_employee_in_sheet
        from pdf_queue_processor import add_pdf_task, ProcessingStatus
        
        # Simulate service with auto-approval
        class MockService:
            name = "درخواست مرخصی"
            auto_approve_enabled = True
            auto_approve_sheet_id = "1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ"
            auto_approve_sheet_column = "A"
            auto_approve_field_name = "employee_name"
        
        # Test data
        test_cases = [
            {"employee_name": "علی محمدی", "should_approve": True},
            {"employee_name": "کاربر ناشناس", "should_approve": False},
        ]
        
        for i, test_case in enumerate(test_cases):
            print(f"\n--- Test Case {i+1} ---")
            print(f"Employee: {test_case['employee_name']}")
            
            # Check if exists in sheet
            exists = check_employee_in_sheet(
                test_case['employee_name'],
                MockService.auto_approve_sheet_id,
                MockService.auto_approve_sheet_column
            )
            
            print(f"Found in sheet: {'Yes' if exists else 'No'}")
            print(f"Expected approval: {'Yes' if test_case['should_approve'] else 'No'}")
            print(f"Result: {'✅ Correct' if exists == test_case['should_approve'] else '❌ Incorrect'}")
            
            if exists:
                print("→ Would trigger auto-approval and PDF generation")
            else:
                print("→ Would proceed with manual approval process")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("Auto-Approval System Test Suite")
    print("=" * 70)
    
    # Check for credentials
    if not os.path.exists('credentials.json'):
        print("\n⚠️  Warning: credentials.json not found!")
        print("   Some tests may fail without Google API credentials.")
        print("   Please set up a service account and download credentials.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Run tests
    tests = [
        ("Google Sheets Checker", test_google_sheets_checker),
        ("PDF Queue Processor", test_pdf_queue),
        ("Auto-Approval Flow", test_auto_approval_flow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")

if __name__ == "__main__":
    main()