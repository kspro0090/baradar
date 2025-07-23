"""
Document Processing Service
Handles local document processing, placeholder replacement, and PDF generation
"""

import os
import io
import re
import tempfile
from docx import Document
from docx.shared import Pt, RGBColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
import arabic_reshaper
from bidi.algorithm import get_display
from bs4 import BeautifulSoup
import base64


class DocumentProcessor:
    """Process documents locally without modifying the original"""
    
    def __init__(self):
        # Register Persian fonts for PDF generation
        self._register_fonts()
        
    def _register_fonts(self):
        """Register Persian fonts for ReportLab"""
        font_paths = {
            'Vazir': 'static/fonts/Vazir.ttf',
            'Vazir-Bold': 'static/fonts/Vazir-Bold.ttf',
            'IRANSans': 'static/fonts/IRANSansWeb.ttf',
            'IRANSans-Bold': 'static/fonts/IRANSansWeb_Bold.ttf'
        }
        
        for font_name, font_path in font_paths.items():
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                except:
                    pass
    
    def process_docx_template(self, docx_data, replacements):
        """Process DOCX template and replace placeholders"""
        # Create a temporary file to work with
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(docx_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Open the document
            doc = Document(tmp_file_path)
            
            # Replace placeholders in paragraphs
            for paragraph in doc.paragraphs:
                for placeholder, value in replacements.items():
                    placeholder_pattern = f'{{{{{placeholder}}}}}'
                    if placeholder_pattern in paragraph.text:
                        # Replace in each run to preserve formatting
                        for run in paragraph.runs:
                            if placeholder_pattern in run.text:
                                run.text = run.text.replace(placeholder_pattern, value)
            
            # Replace placeholders in tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            for placeholder, value in replacements.items():
                                placeholder_pattern = f'{{{{{placeholder}}}}}'
                                if placeholder_pattern in paragraph.text:
                                    for run in paragraph.runs:
                                        if placeholder_pattern in run.text:
                                            run.text = run.text.replace(placeholder_pattern, value)
            
            # Save the modified document
            output_path = tmp_file_path.replace('.docx', '_filled.docx')
            doc.save(output_path)
            
            # Read the filled document
            with open(output_path, 'rb') as f:
                filled_data = f.read()
            
            # Clean up
            os.unlink(output_path)
            
            return filled_data
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)
    
    def process_html_template(self, html_data, replacements):
        """Process HTML template and replace placeholders"""
        html_content = html_data.decode('utf-8')
        
        # Replace placeholders
        for placeholder, value in replacements.items():
            placeholder_pattern = f'{{{{{placeholder}}}}}'
            html_content = html_content.replace(placeholder_pattern, value)
        
        return html_content.encode('utf-8')
    
    def _prepare_persian_text(self, text):
        """Prepare Persian text for proper RTL display in PDF"""
        if not text:
            return ""
        # Reshape Arabic/Persian text
        reshaped_text = arabic_reshaper.reshape(text)
        # Apply RTL algorithm
        bidi_text = get_display(reshaped_text)
        return bidi_text
    
    def generate_pdf_from_html(self, html_data, output_path):
        """Generate PDF from HTML content with Persian support"""
        try:
            # Parse HTML
            soup = BeautifulSoup(html_data, 'html.parser')
            
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Persian style
            persian_style = ParagraphStyle(
                'Persian',
                parent=styles['Normal'],
                fontName='Vazir',
                fontSize=12,
                leading=20,
                alignment=TA_RIGHT,
                wordWrap='RTL',
                direction='RTL'
            )
            
            # Process HTML content
            for element in soup.body.children if soup.body else []:
                if element.name == 'p':
                    text = element.get_text(strip=True)
                    if text:
                        # Prepare Persian text
                        persian_text = self._prepare_persian_text(text)
                        para = Paragraph(persian_text, persian_style)
                        elements.append(para)
                        elements.append(Spacer(1, 12))
                
                elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    text = element.get_text(strip=True)
                    if text:
                        # Create heading style
                        heading_style = ParagraphStyle(
                            f'Heading{element.name[1]}',
                            parent=persian_style,
                            fontSize=20 - int(element.name[1]) * 2,
                            fontName='Vazir-Bold',
                            spaceAfter=12
                        )
                        persian_text = self._prepare_persian_text(text)
                        para = Paragraph(persian_text, heading_style)
                        elements.append(para)
                        elements.append(Spacer(1, 12))
                
                elif element.name == 'table':
                    # Process tables
                    table_data = []
                    for row in element.find_all('tr'):
                        row_data = []
                        for cell in row.find_all(['td', 'th']):
                            text = cell.get_text(strip=True)
                            persian_text = self._prepare_persian_text(text)
                            row_data.append(Paragraph(persian_text, persian_style))
                        if row_data:
                            table_data.append(row_data)
                    
                    if table_data:
                        t = Table(table_data)
                        t.setStyle(TableStyle([
                            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                            ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
                            ('FONTSIZE', (0, 0), (-1, 0), 12),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)
                        ]))
                        elements.append(t)
                        elements.append(Spacer(1, 12))
            
            # Build PDF
            doc.build(elements)
            return True
            
        except Exception as e:
            print(f"Error generating PDF from HTML: {str(e)}")
            return False
    
    def generate_pdf_from_docx(self, docx_data, output_path):
        """Generate PDF from DOCX content with Persian support"""
        # Create a temporary file for the DOCX
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            tmp_file.write(docx_data)
            tmp_file_path = tmp_file.name
        
        try:
            # Open the document
            doc = Document(tmp_file_path)
            
            # Create PDF document
            pdf_doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for the 'Flowable' objects
            elements = []
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Persian style
            persian_style = ParagraphStyle(
                'Persian',
                parent=styles['Normal'],
                fontName='Vazir',
                fontSize=12,
                leading=20,
                alignment=TA_RIGHT,
                wordWrap='RTL',
                direction='RTL'
            )
            
            # Process paragraphs
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    # Prepare Persian text
                    persian_text = self._prepare_persian_text(text)
                    
                    # Check if it's a heading based on style
                    if paragraph.style.name.startswith('Heading'):
                        heading_style = ParagraphStyle(
                            'PersianHeading',
                            parent=persian_style,
                            fontSize=16,
                            fontName='Vazir-Bold',
                            spaceAfter=12
                        )
                        para = Paragraph(persian_text, heading_style)
                    else:
                        para = Paragraph(persian_text, persian_style)
                    
                    elements.append(para)
                    elements.append(Spacer(1, 12))
            
            # Process tables
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        persian_text = self._prepare_persian_text(cell_text)
                        row_data.append(Paragraph(persian_text, persian_style))
                    table_data.append(row_data)
                
                if table_data:
                    t = Table(table_data)
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Vazir'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(t)
                    elements.append(Spacer(1, 12))
            
            # Build PDF
            pdf_doc.build(elements)
            return True
            
        except Exception as e:
            print(f"Error generating PDF from DOCX: {str(e)}")
            return False
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_file_path):
                os.unlink(tmp_file_path)