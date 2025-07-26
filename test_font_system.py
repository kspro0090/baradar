#!/usr/bin/env python3
"""Test script for the Font Management System"""

from font_manager import FontManager

def test_font_manager():
    print("Testing Font Management System")
    print("=" * 50)
    
    # Initialize with some test fonts
    available_fonts = ['Arial', 'Roboto', 'Times New Roman', 'IRANSans']
    manager = FontManager(available_fonts)
    
    # Test 1: Analyze document with mixed font availability
    print("\nTest 1: Document with mixed font availability")
    print("-" * 40)
    document_fonts = ['Arial', 'B Nazanin', 'IRANSans', 'Calibri']
    
    analysis = manager.analyze_document_fonts(document_fonts)
    report = manager.format_analysis_report(analysis)
    print(report)
    
    # Test 2: Document with all fonts available
    print("\n\nTest 2: Document with all fonts available")
    print("-" * 40)
    document_fonts2 = ['Arial', 'Roboto', 'Times New Roman']
    
    analysis2 = manager.analyze_document_fonts(document_fonts2)
    report2 = manager.format_analysis_report(analysis2)
    print(report2)
    
    # Test 3: Case-insensitive font matching
    print("\n\nTest 3: Case-insensitive font matching")
    print("-" * 40)
    document_fonts3 = ['ARIAL', 'roboto', 'times new roman']
    
    analysis3 = manager.analyze_document_fonts(document_fonts3)
    report3 = manager.format_analysis_report(analysis3)
    print(report3)
    
    print("\n" + "=" * 50)
    print("All tests completed successfully!")

if __name__ == "__main__":
    test_font_manager()