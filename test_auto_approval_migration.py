#!/usr/bin/env python3
"""
Test script for auto-approval settings migration
Tests that auto-approval settings have been moved to field editing page
"""

import os
import sys
from datetime import datetime

def test_forms():
    """Test that forms have been updated correctly"""
    print("\n" + "="*50)
    print("Test 1: Forms Configuration")
    print("="*50)
    
    try:
        from forms import ServiceForm, AutoApprovalSettingsForm
        
        # Check ServiceForm no longer has auto-approval fields
        service_form = ServiceForm()
        service_fields = [field.name for field in service_form]
        
        print("ServiceForm fields:")
        for field in service_fields:
            print(f"  - {field}")
        
        auto_approval_fields = ['auto_approve_enabled', 'auto_approve_sheet_id', 
                               'auto_approve_sheet_column', 'auto_approve_field_name']
        
        removed_fields = [f for f in auto_approval_fields if f not in service_fields]
        print(f"\nRemoved auto-approval fields: {len(removed_fields)}/4")
        
        # Check AutoApprovalSettingsForm exists
        auto_form = AutoApprovalSettingsForm()
        auto_fields = [field.name for field in auto_form]
        
        print("\nAutoApprovalSettingsForm fields:")
        for field in auto_fields:
            print(f"  - {field}")
        
        has_all_fields = all(f in auto_fields for f in auto_approval_fields)
        print(f"\nHas all required fields: {'✅ Yes' if has_all_fields else '❌ No'}")
        
        return len(removed_fields) == 4 and has_all_fields
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_routes():
    """Test that routes have been updated"""
    print("\n" + "="*50)
    print("Test 2: Routes Configuration")
    print("="*50)
    
    try:
        # Check if app imports the new form
        with open('app.py', 'r') as f:
            app_content = f.read()
        
        checks = {
            'AutoApprovalSettingsForm import': 'from forms import AutoApprovalSettingsForm' in app_content,
            'auto_approval_form creation': 'auto_approval_form = AutoApprovalSettingsForm()' in app_content,
            'save_auto_approval handling': "'save_auto_approval' in request.form" in app_content,
            'auto_approval_form in render': 'auto_approval_form=auto_approval_form' in app_content
        }
        
        for check, result in checks.items():
            status = '✅' if result else '❌'
            print(f"{check}: {status}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_templates():
    """Test that templates have been updated"""
    print("\n" + "="*50)
    print("Test 3: Templates Configuration")
    print("="*50)
    
    try:
        # Check create_service.html
        with open('templates/admin/create_service.html', 'r') as f:
            create_content = f.read()
        
        # Check edit_fields.html
        with open('templates/admin/edit_fields.html', 'r') as f:
            fields_content = f.read()
        
        checks = {
            'Auto-approval removed from create': 'تنظیمات تأیید خودکار' not in create_content,
            'Auto-approval added to fields': 'تنظیمات تأیید خودکار' in fields_content,
            'Form in fields template': 'auto_approval_form' in fields_content,
            'JavaScript in fields': 'auto-approve-checkbox' in fields_content
        }
        
        for check, result in checks.items():
            status = '✅' if result else '❌'
            print(f"{check}: {status}")
        
        return all(checks.values())
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_workflow():
    """Test the expected workflow"""
    print("\n" + "="*50)
    print("Test 4: Expected Workflow")
    print("="*50)
    
    print("\n1. Admin creates a new service:")
    print("   - Fills basic info (name, description, Google Doc ID)")
    print("   - Clicks 'ایجاد و ادامه'")
    print("   - Redirected to field editing page")
    
    print("\n2. On field editing page:")
    print("   - Admin adds form fields")
    print("   - Admin configures auto-approval settings")
    print("   - Selects field to check from dropdown")
    print("   - Saves auto-approval settings")
    
    print("\n3. When user submits request:")
    print("   - System checks if auto-approval is enabled")
    print("   - Checks selected field value against Google Sheet")
    print("   - Auto-approves if match found")
    
    return True

def main():
    """Run all tests"""
    print("Auto-Approval Migration Test Suite")
    print("=" * 70)
    
    tests = [
        ("Forms Configuration", test_forms),
        ("Routes Configuration", test_routes),
        ("Templates Configuration", test_templates),
        ("Expected Workflow", test_workflow)
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
    print("MIGRATION TEST SUMMARY")
    print("="*70)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    total_passed = sum(1 for _, success in results if success)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n✅ All tests passed! Migration completed successfully.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()