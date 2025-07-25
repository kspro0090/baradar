#!/usr/bin/env python3
"""
Document Processor Module
Integrates PDF generation with the existing system
"""

import os
import logging
from typing import Dict, Optional
from pdf_generator import PersianPDFGenerator

# Setup logging
logger = logging.getLogger(__name__)

# Global PDF generator instance
_pdf_generator = None

def get_pdf_generator(fonts_dir: str = "fonts") -> PersianPDFGenerator:
    """Get or create PDF generator instance"""
    global _pdf_generator
    if _pdf_generator is None:
        _pdf_generator = PersianPDFGenerator(fonts_dir=fonts_dir)
    return _pdf_generator

def generate_pdf_from_docx_template(
    template_path: str,
    output_path: str,
    replacements: Dict[str, str],
    fonts_dir: str = "fonts"
) -> bool:
    """
    Generate PDF from DOCX template with Persian font support
    
    This function is compatible with the existing system and handles:
    - Font registration (including Vazir)
    - RTL text processing
    - Placeholder replacements
    - Error handling
    
    Args:
        template_path: Path to DOCX template
        output_path: Path for output PDF
        replacements: Dictionary of placeholders to replace
        fonts_dir: Directory containing font files
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get PDF generator
        generator = get_pdf_generator(fonts_dir)
        
        # Generate PDF
        success = generator.generate_pdf_from_docx(
            template_path,
            output_path,
            replacements
        )
        
        if success:
            logger.info(f"PDF generated successfully: {output_path}")
        else:
            logger.error(f"Failed to generate PDF: {output_path}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error in generate_pdf_from_docx_template: {str(e)}")
        return False

def process_service_request_to_pdf(
    service_request,
    template_path: str,
    output_dir: str = "pdf_outputs",
    fonts_dir: str = "fonts"
) -> Optional[str]:
    """
    Process a service request and generate PDF
    
    Args:
        service_request: Service request object (from database)
        template_path: Path to DOCX template
        output_dir: Directory for output PDFs
        fonts_dir: Directory containing fonts
        
    Returns:
        Path to generated PDF or None if failed
    """
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Get form data from service request
        form_data = service_request.get_form_data() if hasattr(service_request, 'get_form_data') else {}
        
        # Prepare replacements
        replacements = {}
        
        # Add form data to replacements
        for key, value in form_data.items():
            placeholder = f"{{{{{key}}}}}"  # Convert to {{key}} format
            replacements[placeholder] = str(value)
        
        # Add service request metadata
        if hasattr(service_request, 'tracking_code'):
            replacements['{{tracking_code}}'] = service_request.tracking_code
        if hasattr(service_request, 'created_at'):
            replacements['{{request_date}}'] = service_request.created_at.strftime('%Y/%m/%d')
        if hasattr(service_request, 'user') and service_request.user:
            replacements['{{requester_name}}'] = service_request.user.username
        
        # Generate output filename
        tracking_code = getattr(service_request, 'tracking_code', 'unknown')
        output_filename = f"request_{tracking_code}.pdf"
        output_path = os.path.join(output_dir, output_filename)
        
        # Generate PDF
        success = generate_pdf_from_docx_template(
            template_path,
            output_path,
            replacements,
            fonts_dir
        )
        
        return output_path if success else None
        
    except Exception as e:
        logger.error(f"Error processing service request to PDF: {str(e)}")
        return None

def validate_font_availability(required_fonts: list, fonts_dir: str = "fonts") -> Dict[str, bool]:
    """
    Check if required fonts are available
    
    Args:
        required_fonts: List of font names to check
        fonts_dir: Directory containing fonts
        
    Returns:
        Dictionary mapping font names to availability status
    """
    generator = get_pdf_generator(fonts_dir)
    availability = {}
    
    for font in required_fonts:
        mapped_font = generator._map_font_name(font)
        # Check if font is registered or can be mapped
        is_available = (
            mapped_font in generator.registered_fonts.values() or
            mapped_font == generator.default_font
        )
        availability[font] = is_available
        
    return availability

# Compatibility function for existing code
def generate_pdf_from_request(service_request, template_path: str = None) -> Optional[str]:
    """
    Generate PDF from service request (backward compatible)
    
    Args:
        service_request: Service request object
        template_path: Optional template path (will use from service if not provided)
        
    Returns:
        Filename of generated PDF or None if failed
    """
    try:
        # Get template path
        if not template_path and hasattr(service_request, 'service'):
            service = service_request.service
            if hasattr(service, 'docx_template_path') and service.docx_template_path:
                template_path = service.docx_template_path
            else:
                logger.error("No template path available for service")
                return None
        
        if not template_path or not os.path.exists(template_path):
            logger.error(f"Template not found: {template_path}")
            return None
        
        # Process to PDF
        output_path = process_service_request_to_pdf(
            service_request,
            template_path
        )
        
        if output_path:
            # Return just the filename for compatibility
            return os.path.basename(output_path)
        
        return None
        
    except Exception as e:
        logger.error(f"Error in generate_pdf_from_request: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the document processor
    print("Document Processor Test")
    print("=" * 50)
    
    # Check font availability
    test_fonts = ['Vazir', 'B Nazanin', 'Arial', 'IRANSans']
    availability = validate_font_availability(test_fonts)
    
    print("Font Availability:")
    for font, available in availability.items():
        status = "✓" if available else "✗"
        print(f"  {status} {font}")
    
    print("\nDocument processor is ready!")