#!/usr/bin/env python3
"""
Image-based PDF Generator Module
Handles PDF generation from images with text overlays for form fields
"""

import os
import json
from typing import Dict, List, Optional, Tuple
from io import BytesIO
import logging
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4, A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch, cm
import arabic_reshaper
from bidi.algorithm import get_display

# Setup logging
logger = logging.getLogger(__name__)

class ImagePDFGenerator:
    """Handles PDF generation from images with text overlays"""
    
    def __init__(self, fonts_dir: str = "fonts"):
        """
        Initialize the image PDF generator with font directory
        
        Args:
            fonts_dir: Directory containing font files
        """
        self.fonts_dir = fonts_dir
        self.registered_fonts = {}
        self.default_font = 'arial.ttf'  # Fallback font
        
        # Register fonts on initialization
        self._register_fonts()
        
    def _register_fonts(self):
        """Register fonts for PIL"""
        font_files = {
            'Arial': 'arial.ttf',
            'Times New Roman': 'times.ttf',
            'Courier New': 'cour.ttf',
            'Tahoma': 'tahoma.ttf',
            'B Nazanin': 'BNazanin.ttf',
            'B Titr': 'BTitr.ttf',
            'Vazirmatn': 'Vazirmatn-Regular.ttf',
            'Vazirmatn-Bold': 'Vazirmatn-Bold.ttf'
        }
        
        # Try to register fonts
        for font_name, font_file in font_files.items():
            font_path = os.path.join(self.fonts_dir, font_file)
            if os.path.exists(font_path):
                try:
                    # Test if font can be loaded
                    test_font = ImageFont.truetype(font_path, 12)
                    self.registered_fonts[font_name] = font_path
                    logger.info(f"Registered font: {font_name} from {font_path}")
                except Exception as e:
                    logger.warning(f"Failed to register font {font_name}: {str(e)}")
            else:
                logger.debug(f"Font file not found: {font_path}")
    
    def _get_font_path(self, font_name: str) -> str:
        """
        Get font path for given font name
        
        Args:
            font_name: Name of the font
            
        Returns:
            Path to font file or default font
        """
        return self.registered_fonts.get(font_name, self.registered_fonts.get('Arial', self.default_font))
    
    def _process_rtl_text(self, text: str) -> str:
        """
        Process RTL text for proper display
        
        Args:
            text: Original text
            
        Returns:
            Processed RTL text
        """
        if not text:
            return text
        
        # Reshape Arabic/Persian text
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply bidirectional algorithm
        bidi_text = get_display(reshaped_text)
        return bidi_text
    
    def _get_page_size(self, page_size: str) -> Tuple[float, float]:
        """
        Get page dimensions based on page size
        
        Args:
            page_size: Page size string ('A4', 'A5', 'original')
            
        Returns:
            Tuple of (width, height) in points
        """
        if page_size == 'A4':
            return A4
        elif page_size == 'A5':
            return A5
        else:
            # Default to A4
            return A4
    
    def generate_pdf_from_image(self, 
                               image_path: str,
                               output_path: str,
                               form_data: Dict[str, str],
                               design_data: Dict,
                               page_size: str = 'A4') -> bool:
        """
        Generate PDF from image with text overlays
        
        Args:
            image_path: Path to the base image
            output_path: Path for output PDF
            form_data: Dictionary of form field values
            design_data: Design data containing textbox positions and properties
            page_size: Page size ('A4', 'A5', 'original')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the base image
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return False
            
            base_image = Image.open(image_path)
            
            # Get page dimensions
            page_width, page_height = self._get_page_size(page_size)
            
            # Scale image to fit page if needed
            if page_size != 'original':
                # Convert points to pixels (assuming 72 DPI)
                target_width = int(page_width)
                target_height = int(page_height)
                
                # Calculate scaling to fit image within page bounds
                img_ratio = base_image.width / base_image.height
                page_ratio = target_width / target_height
                
                if img_ratio > page_ratio:
                    # Image is wider, scale by width
                    new_width = target_width
                    new_height = int(target_width / img_ratio)
                else:
                    # Image is taller, scale by height
                    new_height = target_height
                    new_width = int(target_height * img_ratio)
                
                base_image = base_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create PDF
            c = canvas.Canvas(output_path, pagesize=(page_width, page_height))
            
            # Add image to PDF
            c.drawImage(image_path, 0, 0, width=base_image.width, height=base_image.height)
            
            # Process textboxes from design data
            if 'textboxes' in design_data:
                for textbox in design_data['textboxes']:
                    self._add_textbox_to_pdf(c, textbox, form_data, base_image.size)
            
            c.save()
            logger.info(f"PDF generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF from image: {str(e)}")
            return False
    
    def _add_textbox_to_pdf(self, canvas_obj, textbox: Dict, form_data: Dict[str, str], image_size: Tuple[int, int]):
        """
        Add textbox to PDF canvas
        
        Args:
            canvas_obj: ReportLab canvas object
            textbox: Textbox data from design
            form_data: Form field values
            image_size: Size of the base image
        """
        try:
            # Get field value
            field_name = textbox.get('field', '')
            field_value = form_data.get(field_name, textbox.get('label', ''))
            
            if not field_value:
                return
            
            # Process RTL text
            processed_text = self._process_rtl_text(field_value)
            
            # Get font properties
            font_name = textbox.get('font', 'Arial')
            font_size = textbox.get('size', 12)
            font_color = textbox.get('color', '#000000')
            
            # Convert color from hex to RGB
            color_hex = font_color.lstrip('#')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            
            # Set font
            font_path = self._get_font_path(font_name)
            canvas_obj.setFont(font_name, font_size)
            
            # Set color
            canvas_obj.setFillColorRGB(color_rgb[0]/255, color_rgb[1]/255, color_rgb[2]/255)
            
            # Get position
            x = textbox.get('x', 0)
            y = textbox.get('y', 0)
            
            # Convert coordinates if needed (from canvas coordinates to PDF coordinates)
            # Note: PDF coordinates start from bottom-left, canvas from top-left
            pdf_y = image_size[1] - y - textbox.get('height', 0)
            
            # Add text to PDF
            canvas_obj.drawString(x, pdf_y, processed_text)
            
        except Exception as e:
            logger.error(f"Error adding textbox to PDF: {str(e)}")
    
    def generate_pdf_from_image_pil(self, 
                                   image_path: str,
                                   output_path: str,
                                   form_data: Dict[str, str],
                                   design_data: Dict,
                                   page_size: str = 'A4') -> bool:
        """
        Generate PDF from image using PIL for better text rendering
        
        Args:
            image_path: Path to the base image
            output_path: Path for output PDF
            form_data: Dictionary of form field values
            design_data: Design data containing textbox positions and properties
            page_size: Page size ('A4', 'A5', 'original')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Load the base image
            if not os.path.exists(image_path):
                logger.error(f"Image file not found: {image_path}")
                return False
            
            base_image = Image.open(image_path).convert('RGB')
            
            # Get page dimensions
            page_width, page_height = self._get_page_size(page_size)
            
            # Scale image to fit page if needed
            if page_size != 'original':
                # Convert points to pixels (assuming 72 DPI)
                target_width = int(page_width)
                target_height = int(page_height)
                
                # Calculate scaling to fit image within page bounds
                img_ratio = base_image.width / base_image.height
                page_ratio = target_width / target_height
                
                if img_ratio > page_ratio:
                    # Image is wider, scale by width
                    new_width = target_width
                    new_height = int(target_width / img_ratio)
                else:
                    # Image is taller, scale by height
                    new_height = target_height
                    new_width = int(target_height * img_ratio)
                
                base_image = base_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Create a copy for drawing
            output_image = base_image.copy()
            draw = ImageDraw.Draw(output_image)
            
            # Process textboxes from design data
            if 'textboxes' in design_data:
                for textbox in design_data['textboxes']:
                    self._add_textbox_to_image(draw, textbox, form_data, output_image.size)
            
            # Convert to PDF
            output_image.save(output_path, 'PDF', resolution=100.0)
            logger.info(f"PDF generated successfully: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF from image: {str(e)}")
            return False
    
    def _add_textbox_to_image(self, draw, textbox: Dict, form_data: Dict[str, str], image_size: Tuple[int, int]):
        """
        Add textbox to image using PIL
        
        Args:
            draw: PIL ImageDraw object
            textbox: Textbox data from design
            form_data: Form field values
            image_size: Size of the base image
        """
        try:
            # Get field value
            field_name = textbox.get('field', '')
            field_value = form_data.get(field_name, textbox.get('label', ''))
            
            if not field_value:
                return
            
            # Process RTL text
            processed_text = self._process_rtl_text(field_value)
            
            # Get font properties
            font_name = textbox.get('font', 'Arial')
            font_size = textbox.get('size', 12)
            font_color = textbox.get('color', '#000000')
            
            # Convert color from hex to RGB
            color_hex = font_color.lstrip('#')
            color_rgb = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
            
            # Load font
            font_path = self._get_font_path(font_name)
            try:
                font = ImageFont.truetype(font_path, font_size)
            except:
                # Fallback to default font
                font = ImageFont.load_default()
            
            # Get position
            x = textbox.get('x', 0)
            y = textbox.get('y', 0)
            
            # Add text to image
            draw.text((x, y), processed_text, fill=color_rgb, font=font)
            
        except Exception as e:
            logger.error(f"Error adding textbox to image: {str(e)}")

# Convenience function
def generate_pdf_from_image(image_path: str,
                           output_path: str,
                           form_data: Dict[str, str],
                           design_data: Dict,
                           page_size: str = 'A4',
                           fonts_dir: str = "fonts") -> bool:
    """
    Convenience function to generate PDF from image
    
    Args:
        image_path: Path to the base image
        output_path: Path for output PDF
        form_data: Dictionary of form field values
        design_data: Design data containing textbox positions and properties
        page_size: Page size ('A4', 'A5', 'original')
        fonts_dir: Directory containing font files
        
    Returns:
        True if successful, False otherwise
    """
    generator = ImagePDFGenerator(fonts_dir)
    return generator.generate_pdf_from_image_pil(image_path, output_path, form_data, design_data, page_size)