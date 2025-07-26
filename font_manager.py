#!/usr/bin/env python3
"""
Google Docs Font Manager
Analyzes Google Docs files to identify fonts and check their availability in the system.
"""

import os
import json
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class FontStatus(Enum):
    AVAILABLE = "✅ Available"
    NOT_AVAILABLE = "❌ Not available"


@dataclass
class FontInfo:
    name: str
    status: FontStatus
    message: str = ""


class FontManager:
    """Manages font availability checking for Google Docs documents."""
    
    def __init__(self, available_fonts: List[str]):
        """
        Initialize the FontManager with a list of available system fonts.
        
        Args:
            available_fonts: List of font names available in the system
        """
        # Normalize font names for case-insensitive comparison
        self.available_fonts = {font.lower(): font for font in available_fonts}
        
    def normalize_font_name(self, font_name: str) -> str:
        """Normalize font name for comparison."""
        return font_name.strip().lower()
    
    def check_font_availability(self, font_name: str) -> FontInfo:
        """
        Check if a font is available in the system.
        
        Args:
            font_name: Name of the font to check
            
        Returns:
            FontInfo object with availability status
        """
        normalized_name = self.normalize_font_name(font_name)
        
        if normalized_name in self.available_fonts:
            return FontInfo(
                name=font_name,
                status=FontStatus.AVAILABLE
            )
        else:
            return FontInfo(
                name=font_name,
                status=FontStatus.NOT_AVAILABLE,
                message="Please upload the .ttf or .woff file"
            )
    
    def analyze_document_fonts(self, document_fonts: List[str]) -> Dict[str, FontInfo]:
        """
        Analyze fonts used in a document and check their availability.
        
        Args:
            document_fonts: List of font names used in the document
            
        Returns:
            Dictionary mapping font names to their FontInfo
        """
        # Remove duplicates while preserving order
        unique_fonts = []
        seen = set()
        for font in document_fonts:
            if font not in seen:
                seen.add(font)
                unique_fonts.append(font)
        
        results = {}
        for font in unique_fonts:
            results[font] = self.check_font_availability(font)
            
        return results
    
    def format_analysis_report(self, font_analysis: Dict[str, FontInfo]) -> str:
        """
        Format the font analysis results into a readable report.
        
        Args:
            font_analysis: Dictionary of font analysis results
            
        Returns:
            Formatted report string
        """
        if not font_analysis:
            return "No fonts found in the document."
        
        # Check if all fonts are available
        all_available = all(
            info.status == FontStatus.AVAILABLE 
            for info in font_analysis.values()
        )
        
        # Build the report
        lines = ["Fonts used in the document:"]
        
        for font_name, info in font_analysis.items():
            line = f"- {font_name} {info.status.value}"
            if info.message:
                line += f" ({info.message})"
            lines.append(line)
        
        # Add summary message
        if all_available:
            lines.append("\nAll fonts used in the document are available. Ready to proceed with document processing.")
        else:
            missing_count = sum(
                1 for info in font_analysis.values() 
                if info.status == FontStatus.NOT_AVAILABLE
            )
            lines.append(f"\n{missing_count} font(s) missing. Please upload the required font files before processing.")
        
        return "\n".join(lines)
    
    def process_google_doc(self, doc_id: str, document_fonts: List[str]) -> str:
        """
        Process a Google Doc by analyzing its fonts.
        
        Args:
            doc_id: Google Docs file ID
            document_fonts: List of fonts used in the document
            
        Returns:
            Formatted analysis report
        """
        print(f"Analyzing document: {doc_id}")
        
        # Analyze fonts
        font_analysis = self.analyze_document_fonts(document_fonts)
        
        # Generate report
        report = self.format_analysis_report(font_analysis)
        
        return report


class GoogleDocsParser:
    """
    Placeholder for Google Docs parsing functionality.
    In a real implementation, this would use the Google Docs API.
    """
    
    @staticmethod
    def parse_document_fonts(doc_id: str) -> List[str]:
        """
        Parse fonts from a Google Docs document.
        
        Note: This is a placeholder. In production, this would:
        1. Authenticate with Google Docs API
        2. Fetch document content and styles
        3. Extract all font families used
        
        Args:
            doc_id: Google Docs file ID
            
        Returns:
            List of font names used in the document
        """
        # Placeholder implementation
        # In reality, this would make API calls to Google Docs
        print(f"Note: Google Docs API integration not implemented.")
        print(f"Please provide the list of fonts used in document: {doc_id}")
        
        # Return empty list as placeholder
        return []


def main():
    """Example usage of the FontManager system."""
    
    # Example: System available fonts
    system_fonts = ['Roboto', 'Arial', 'IRANSans', 'Times New Roman', 'Helvetica']
    
    # Initialize font manager
    font_manager = FontManager(system_fonts)
    
    # Example 1: Document with mixed availability
    print("Example 1: Document with some missing fonts")
    print("-" * 50)
    
    doc_id = "1AbCDefgHiJKLmnopQRsTuv"
    document_fonts = ['IRANSans', 'B Nazanin', 'Roboto', 'IRANSans']  # Note: duplicate
    
    report = font_manager.process_google_doc(doc_id, document_fonts)
    print(report)
    
    print("\n" + "=" * 50 + "\n")
    
    # Example 2: Document with all fonts available
    print("Example 2: Document with all fonts available")
    print("-" * 50)
    
    doc_id2 = "2XyZaBcDeFgHiJkLmNoPqRs"
    document_fonts2 = ['Arial', 'Roboto', 'Times New Roman']
    
    report2 = font_manager.process_google_doc(doc_id2, document_fonts2)
    print(report2)
    
    print("\n" + "=" * 50 + "\n")
    
    # Example 3: Interactive mode
    print("Example 3: Interactive mode")
    print("-" * 50)
    
    # Simulate interactive input
    doc_id3 = input("Enter Google Docs ID (or press Enter for demo): ").strip()
    if not doc_id3:
        doc_id3 = "3DemoDocumentID"
    
    # In a real implementation, this would fetch fonts from Google Docs API
    # For now, we'll use a predefined list
    print("\nUsing demo font list: ['Calibri', 'IRANSans', 'Verdana']")
    document_fonts3 = ['Calibri', 'IRANSans', 'Verdana']
    
    report3 = font_manager.process_google_doc(doc_id3, document_fonts3)
    print(report3)


if __name__ == "__main__":
    main()