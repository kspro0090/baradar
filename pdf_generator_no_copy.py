#!/usr/bin/env python3
"""
PDF Generator without Google Docs Copy
Generates PDF by temporarily modifying the original document and restoring it
"""

import os
import time
import logging
from typing import Dict, Optional, List, Tuple
import io

# Try to import Google API libraries
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    HttpError = Exception  # Fallback for type hints

logger = logging.getLogger(__name__)

class NoCopyPDFGenerator:
    """Generate PDF from Google Docs without creating copies"""
    
    def __init__(self, credentials_path: str):
        """Initialize with Google service account credentials"""
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries not available. Please install google-api-python-client")
            
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive'
            ]
        )
        self.docs_service = build('docs', 'v1', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        
    def get_document_content(self, document_id: str) -> dict:
        """Get the current content of a Google Doc"""
        try:
            document = self.docs_service.documents().get(documentId=document_id).execute()
            return document
        except HttpError as e:
            logger.error(f"Error getting document: {str(e)}")
            raise
    
    def extract_placeholders(self, document: dict) -> List[str]:
        """Extract all placeholders from document"""
        placeholders = set()
        content = document.get('body', {}).get('content', [])
        
        def extract_from_element(element):
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        text = elem['textRun'].get('content', '')
                        # Find all {{placeholder}} patterns
                        import re
                        matches = re.findall(r'\{\{([^}]+)\}\}', text)
                        placeholders.update(matches)
            elif 'table' in element:
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for content_elem in cell.get('content', []):
                            extract_from_element(content_elem)
        
        for element in content:
            extract_from_element(element)
        
        return list(placeholders)
    
    def create_batch_update_request(self, replacements: Dict[str, str]) -> List[dict]:
        """Create batch update requests for replacing text"""
        requests = []
        
        # Sort replacements by length (longest first) to avoid partial replacements
        sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        
        for placeholder, value in sorted_replacements:
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': placeholder,
                        'matchCase': True
                    },
                    'replaceText': value
                }
            })
        
        return requests
    
    def batch_update_document(self, document_id: str, requests: List[dict]) -> dict:
        """Execute batch update on document"""
        try:
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            return result
        except HttpError as e:
            logger.error(f"Error updating document: {str(e)}")
            raise
    
    def export_as_pdf(self, document_id: str) -> bytes:
        """Export document as PDF"""
        try:
            request = self.drive_service.files().export_media(
                fileId=document_id,
                mimeType='application/pdf'
            )
            
            file = io.BytesIO()
            downloader = request.execute()
            
            if isinstance(downloader, bytes):
                return downloader
            else:
                # Handle MediaIoBaseDownload if needed
                import googleapiclient.http
                downloader = googleapiclient.http.MediaIoBaseDownload(file, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                
                file.seek(0)
                return file.read()
                
        except HttpError as e:
            logger.error(f"Error exporting PDF: {str(e)}")
            raise
    
    def generate_pdf_without_copy(self, 
                                 document_id: str,
                                 replacements: Dict[str, str],
                                 output_path: str) -> bool:
        """
        Generate PDF by temporarily modifying document and restoring it
        
        Args:
            document_id: Google Docs document ID
            replacements: Dictionary of placeholders to values
            output_path: Path to save the PDF
            
        Returns:
            True if successful, False otherwise
        """
        original_placeholders = {}
        
        try:
            # Step 1: Get current document state
            logger.info(f"Getting document content for {document_id}")
            document = self.get_document_content(document_id)
            
            # Step 2: Extract current placeholders
            current_placeholders = self.extract_placeholders(document)
            logger.info(f"Found placeholders: {current_placeholders}")
            
            # Step 3: Create forward replacements (placeholder -> value)
            forward_requests = self.create_batch_update_request(replacements)
            
            # Step 4: Apply replacements
            logger.info("Applying replacements to document")
            self.batch_update_document(document_id, forward_requests)
            
            # Small delay to ensure changes are applied
            time.sleep(1)
            
            # Step 5: Export as PDF
            logger.info("Exporting document as PDF")
            pdf_data = self.export_as_pdf(document_id)
            
            # Step 6: Save PDF
            with open(output_path, 'wb') as f:
                f.write(pdf_data)
            logger.info(f"PDF saved to {output_path}")
            
            # Step 7: Create reverse replacements (value -> placeholder)
            reverse_replacements = {v: k for k, v in replacements.items()}
            reverse_requests = self.create_batch_update_request(reverse_replacements)
            
            # Step 8: Restore original placeholders
            logger.info("Restoring original placeholders")
            self.batch_update_document(document_id, reverse_requests)
            
            return True
            
        except Exception as e:
            logger.error(f"Error in generate_pdf_without_copy: {str(e)}")
            
            # Try to restore document on error
            try:
                if replacements:
                    reverse_replacements = {v: k for k, v in replacements.items()}
                    reverse_requests = self.create_batch_update_request(reverse_replacements)
                    self.batch_update_document(document_id, reverse_requests)
                    logger.info("Document restored after error")
            except:
                logger.error("Failed to restore document after error")
            
            return False


def generate_pdf_from_request_no_copy(service_request, credentials_path: str = 'credentials.json'):
    """
    Generate PDF from service request without copying Google Docs
    
    Args:
        service_request: Service request object
        credentials_path: Path to Google service account credentials
        
    Returns:
        PDF filename if successful, None otherwise
    """
    try:
        service = service_request.service
        form_data = service_request.get_form_data()
        
        if not service.google_doc_id:
            raise Exception("No Google Doc template configured for this service")
        
        # Initialize generator
        generator = NoCopyPDFGenerator(credentials_path)
        
        # Prepare replacements
        replacements = {}
        for field in service.form_fields:
            if field.document_placeholder:
                value = str(form_data.get(field.field_name, ''))
                replacements[field.document_placeholder] = value
        
        # Add metadata replacements
        replacements['{{tracking_code}}'] = service_request.tracking_code
        replacements['{{request_date}}'] = service_request.created_at.strftime('%Y/%m/%d')
        if service_request.user:
            replacements['{{requester_name}}'] = service_request.user.username
        
        # Generate output path
        pdf_filename = f"output_{service_request.tracking_code}.pdf"
        pdf_path = os.path.join('pdf_outputs', pdf_filename)
        
        # Ensure output directory exists
        os.makedirs('pdf_outputs', exist_ok=True)
        
        # Generate PDF
        success = generator.generate_pdf_without_copy(
            service.google_doc_id,
            replacements,
            pdf_path
        )
        
        if success:
            return pdf_filename
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error in generate_pdf_from_request_no_copy: {str(e)}")
        return None


# Alternative approach using ReportLab (if Google Docs API fails)
def generate_pdf_fallback(service_request):
    """
    Fallback PDF generation using ReportLab
    """
    try:
        from document_processor import process_service_request_to_pdf
        
        # Check if service has DOCX template
        if hasattr(service_request.service, 'docx_template_path'):
            template_path = service_request.service.docx_template_path
        else:
            # Create a simple PDF without template
            from pdf_generator import PersianPDFGenerator
            
            generator = PersianPDFGenerator()
            
            # Build content from form data
            content = f"کد پیگیری: {service_request.tracking_code}\n\n"
            content += f"تاریخ درخواست: {service_request.created_at.strftime('%Y/%m/%d')}\n\n"
            
            form_data = service_request.get_form_data()
            for field in service_request.service.form_fields:
                label = field.field_label
                value = form_data.get(field.field_name, '')
                content += f"{label}: {value}\n"
            
            pdf_filename = f"output_{service_request.tracking_code}.pdf"
            pdf_path = os.path.join('pdf_outputs', pdf_filename)
            
            os.makedirs('pdf_outputs', exist_ok=True)
            
            success = generator.generate_pdf_from_text(
                content,
                pdf_path,
                title=f"درخواست خدمت: {service_request.service.name}",
                font_name='Vazir'
            )
            
            if success:
                return pdf_filename
        
        # Use DOCX template if available
        output_path = process_service_request_to_pdf(
            service_request,
            template_path
        )
        
        if output_path:
            return os.path.basename(output_path)
            
    except Exception as e:
        logger.error(f"Error in fallback PDF generation: {str(e)}")
    
    return None