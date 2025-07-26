#!/usr/bin/env python3
"""
Google Docs PDF Generator with Placeholder Replacement
Generates PDF from Google Docs while preserving all styles, fonts, and formatting
"""

import os
import time
import logging
from typing import Dict, Optional, List, Tuple, Any
import re
from datetime import datetime

# Google API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from google.oauth2 import service_account
    from googleapiclient.http import MediaIoBaseDownload
    import io
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Warning: Google API libraries not installed. Install with: pip install google-api-python-client google-auth")

logger = logging.getLogger(__name__)

class GoogleDocsPDFGenerator:
    """
    Generate PDF from Google Docs with temporary placeholder replacement
    Preserves all formatting, styles, fonts, images, and layout
    """
    
    def __init__(self, credentials_path: str = 'credentials.json'):
        """
        Initialize with Google service account credentials
        
        Args:
            credentials_path: Path to service account JSON file
        """
        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google API libraries required. Install with: pip install google-api-python-client google-auth")
            
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(f"Credentials file not found: {credentials_path}")
            
        # Initialize credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=[
                'https://www.googleapis.com/auth/documents',
                'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/drive.file'
            ]
        )
        
        # Build services
        self.docs_service = build('docs', 'v1', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        
        logger.info("Google Docs PDF Generator initialized")
    
    def _extract_all_text_with_positions(self, document: dict) -> List[Tuple[str, int, int]]:
        """
        Extract all text from document with their positions
        
        Returns:
            List of tuples (text, start_index, end_index)
        """
        text_elements = []
        
        def extract_from_element(element, parent_offset=0):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text_run = elem['textRun']
                        content = text_run.get('content', '')
                        start = elem.get('startIndex', 0) + parent_offset
                        end = elem.get('endIndex', 0) + parent_offset
                        if content.strip():  # Only add non-empty text
                            text_elements.append((content, start, end))
            
            elif 'table' in element:
                table = element['table']
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for content_elem in cell.get('content', []):
                            extract_from_element(content_elem, parent_offset)
        
        # Extract from body
        body = document.get('body', {})
        for element in body.get('content', []):
            extract_from_element(element)
        
        # Extract from headers and footers
        for header_id, header in document.get('headers', {}).items():
            for element in header.get('content', []):
                extract_from_element(element)
                
        for footer_id, footer in document.get('footers', {}).items():
            for element in footer.get('content', []):
                extract_from_element(element)
        
        return text_elements
    
    def _find_placeholders_with_positions(self, document: dict) -> List[Dict[str, Any]]:
        """
        Find all placeholders in document with their exact positions
        
        Returns:
            List of placeholder info with text, start, and end positions
        """
        placeholders = []
        text_elements = self._extract_all_text_with_positions(document)
        
        # Regex pattern for placeholders like {{name}}, {{date}}, etc.
        placeholder_pattern = re.compile(r'\{\{([^}]+)\}\}')
        
        for text, start_pos, end_pos in text_elements:
            # Find all placeholders in this text element
            for match in placeholder_pattern.finditer(text):
                placeholder_text = match.group(0)  # Full placeholder with {{}}
                placeholder_name = match.group(1)  # Just the name inside
                
                # Calculate absolute position in document
                match_start = start_pos + match.start()
                match_end = start_pos + match.end()
                
                placeholders.append({
                    'text': placeholder_text,
                    'name': placeholder_name,
                    'start': match_start,
                    'end': match_end,
                    'original_text': text
                })
        
        # Sort by position (important for batch updates)
        placeholders.sort(key=lambda x: x['start'], reverse=True)
        
        return placeholders
    
    def _create_replacement_requests(self, placeholders: List[Dict], replacements: Dict[str, str]) -> List[Dict]:
        """
        Create batch update requests for replacing placeholders
        
        Args:
            placeholders: List of placeholder info from _find_placeholders_with_positions
            replacements: Dict mapping placeholder names to replacement values
            
        Returns:
            List of Google Docs API requests
        """
        requests = []
        
        for placeholder in placeholders:
            placeholder_name = placeholder['name']
            placeholder_text = placeholder['text']
            
            # Get replacement value
            if placeholder_name in replacements:
                replacement_value = str(replacements[placeholder_name])
            elif placeholder_text in replacements:
                replacement_value = str(replacements[placeholder_text])
            else:
                # Skip if no replacement found
                continue
            
            # Create replace request
            requests.append({
                'replaceAllText': {
                    'containsText': {
                        'text': placeholder_text,
                        'matchCase': True
                    },
                    'replaceText': replacement_value
                }
            })
        
        return requests
    
    def _create_restoration_requests(self, placeholders: List[Dict], replacements: Dict[str, str]) -> List[Dict]:
        """
        Create requests to restore original placeholders
        """
        requests = []
        processed_replacements = set()
        
        for placeholder in placeholders:
            placeholder_name = placeholder['name']
            placeholder_text = placeholder['text']
            
            # Get replacement value that was used
            if placeholder_name in replacements:
                replacement_value = str(replacements[placeholder_name])
            elif placeholder_text in replacements:
                replacement_value = str(replacements[placeholder_text])
            else:
                continue
            
            # Avoid duplicate restoration requests
            replacement_key = f"{replacement_value}||{placeholder_text}"
            if replacement_key not in processed_replacements:
                processed_replacements.add(replacement_key)
                
                requests.append({
                    'replaceAllText': {
                        'containsText': {
                            'text': replacement_value,
                            'matchCase': True
                        },
                        'replaceText': placeholder_text
                    }
                })
        
        return requests
    
    def export_as_pdf(self, document_id: str) -> bytes:
        """
        Export Google Docs as PDF with all formatting preserved
        
        Args:
            document_id: Google Docs document ID
            
        Returns:
            PDF file content as bytes
        """
        try:
            # Request PDF export
            request = self.drive_service.files().export_media(
                fileId=document_id,
                mimeType='application/pdf'
            )
            
            # Download the PDF
            file = io.BytesIO()
            downloader = MediaIoBaseDownload(file, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
                if status:
                    logger.info(f"PDF export progress: {int(status.progress() * 100)}%")
            
            file.seek(0)
            pdf_content = file.read()
            
            logger.info(f"PDF exported successfully, size: {len(pdf_content)} bytes")
            return pdf_content
            
        except HttpError as e:
            logger.error(f"Error exporting PDF: {str(e)}")
            raise
    
    def generate_pdf_with_replacements(self,
                                     document_id: str,
                                     replacements: Dict[str, str],
                                     output_path: str,
                                     delay_before_export: float = 1.0,
                                     delay_before_restore: float = 0.5) -> bool:
        """
        Generate PDF with placeholder replacements, then restore original
        
        Args:
            document_id: Google Docs document ID
            replacements: Dictionary mapping placeholders to values
                         Can use either 'name' or '{{name}}' as keys
            output_path: Path to save the PDF file
            delay_before_export: Seconds to wait after replacement before exporting
            delay_before_restore: Seconds to wait after export before restoring
            
        Returns:
            True if successful, False otherwise
        """
        original_state_saved = False
        
        try:
            # Step 1: Get current document state
            logger.info(f"Getting document content for {document_id}")
            document = self.docs_service.documents().get(documentId=document_id).execute()
            
            # Step 2: Find all placeholders
            placeholders = self._find_placeholders_with_positions(document)
            logger.info(f"Found {len(placeholders)} placeholders in document")
            
            if not placeholders and replacements:
                logger.warning("No placeholders found in document")
            
            # Step 3: Create replacement requests
            replacement_requests = self._create_replacement_requests(placeholders, replacements)
            
            if replacement_requests:
                # Step 4: Apply replacements
                logger.info(f"Applying {len(replacement_requests)} replacements")
                result = self.docs_service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': replacement_requests}
                ).execute()
                
                # Mark that we've modified the document
                original_state_saved = True
                
                # Wait for changes to propagate
                time.sleep(delay_before_export)
            
            # Step 5: Export as PDF
            logger.info("Exporting document as PDF")
            pdf_content = self.export_as_pdf(document_id)
            
            # Step 6: Save PDF to file
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            logger.info(f"PDF saved to {output_path}")
            
            # Wait before restoring
            if original_state_saved:
                time.sleep(delay_before_restore)
            
            # Step 7: Restore original placeholders
            if original_state_saved and replacement_requests:
                restoration_requests = self._create_restoration_requests(placeholders, replacements)
                
                if restoration_requests:
                    logger.info(f"Restoring {len(restoration_requests)} placeholders")
                    self.docs_service.documents().batchUpdate(
                        documentId=document_id,
                        body={'requests': restoration_requests}
                    ).execute()
                    logger.info("Document restored to original state")
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            
            # Try to restore document on error
            if original_state_saved:
                try:
                    logger.info("Attempting to restore document after error")
                    restoration_requests = self._create_restoration_requests(placeholders, replacements)
                    if restoration_requests:
                        self.docs_service.documents().batchUpdate(
                            documentId=document_id,
                            body={'requests': restoration_requests}
                        ).execute()
                        logger.info("Document restored after error")
                except Exception as restore_error:
                    logger.error(f"Failed to restore document: {str(restore_error)}")
            
            return False


def generate_pdf_from_google_docs(document_id: str,
                                replacements: Dict[str, str],
                                output_path: str,
                                credentials_path: str = 'credentials.json') -> bool:
    """
    Convenience function to generate PDF from Google Docs
    
    Args:
        document_id: Google Docs document ID
        replacements: Dictionary of placeholders to replace
        output_path: Path to save PDF
        credentials_path: Path to Google credentials JSON
        
    Returns:
        True if successful, False otherwise
        
    Example:
        replacements = {
            'employee_name': 'علی محمدی',
            'department': 'فناوری اطلاعات',
            'date': '1402/11/15'
        }
        
        success = generate_pdf_from_google_docs(
            '1ABC...xyz',
            replacements,
            'output.pdf'
        )
    """
    try:
        generator = GoogleDocsPDFGenerator(credentials_path)
        return generator.generate_pdf_with_replacements(
            document_id,
            replacements,
            output_path
        )
    except Exception as e:
        logger.error(f"Error in generate_pdf_from_google_docs: {str(e)}")
        return False


# Integration with existing system
def generate_pdf_for_service_request(service_request,
                                   output_dir: str = 'pdf_outputs',
                                   credentials_path: str = 'credentials.json') -> Optional[str]:
    """
    Generate PDF for a service request using Google Docs
    
    Args:
        service_request: Service request object with form data
        output_dir: Directory to save PDFs
        credentials_path: Path to Google credentials
        
    Returns:
        Filename of generated PDF or None if failed
    """
    try:
        # Get Google Doc ID from service
        if not hasattr(service_request.service, 'google_doc_id'):
            logger.error("Service has no google_doc_id")
            return None
            
        document_id = service_request.service.google_doc_id
        if not document_id:
            logger.error("Service google_doc_id is empty")
            return None
        
        # Prepare replacements from form data
        replacements = {}
        form_data = service_request.get_form_data()
        
        # Add form field data
        for field in service_request.service.form_fields:
            if field.document_placeholder:
                # Support both {{name}} and name formats
                placeholder = field.document_placeholder
                value = str(form_data.get(field.field_name, ''))
                
                # Add with and without braces
                replacements[placeholder] = value
                if placeholder.startswith('{{') and placeholder.endswith('}}'):
                    replacements[placeholder[2:-2]] = value
                else:
                    replacements[f'{{{{{placeholder}}}}}'] = value
        
        # Add metadata
        replacements['tracking_code'] = service_request.tracking_code
        replacements['{{tracking_code}}'] = service_request.tracking_code
        
        replacements['request_date'] = service_request.created_at.strftime('%Y/%m/%d')
        replacements['{{request_date}}'] = service_request.created_at.strftime('%Y/%m/%d')
        
        if hasattr(service_request, 'user') and service_request.user:
            replacements['requester_name'] = service_request.user.username
            replacements['{{requester_name}}'] = service_request.user.username
        
        # Generate output path
        os.makedirs(output_dir, exist_ok=True)
        pdf_filename = f"request_{service_request.tracking_code}.pdf"
        output_path = os.path.join(output_dir, pdf_filename)
        
        # Generate PDF
        generator = GoogleDocsPDFGenerator(credentials_path)
        success = generator.generate_pdf_with_replacements(
            document_id,
            replacements,
            output_path
        )
        
        if success:
            return pdf_filename
        else:
            return None
            
    except Exception as e:
        logger.error(f"Error in generate_pdf_for_service_request: {str(e)}")
        return None


if __name__ == "__main__":
    # Test the generator
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python google_docs_pdf_generator.py <document_id>")
        print("Example: python google_docs_pdf_generator.py 1AbC123...")
        sys.exit(1)
    
    document_id = sys.argv[1]
    
    # Test replacements
    test_replacements = {
        'name': 'احمد رضایی',
        'employee_name': 'احمد رضایی',
        'department': 'بخش فناوری اطلاعات',
        'date': datetime.now().strftime('%Y/%m/%d'),
        'tracking_code': f'TEST-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    }
    
    print(f"Testing PDF generation for document: {document_id}")
    print(f"Replacements: {test_replacements}")
    
    output_file = f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    success = generate_pdf_from_google_docs(
        document_id,
        test_replacements,
        output_file
    )
    
    if success:
        print(f"✓ PDF generated successfully: {output_file}")
        print(f"  File size: {os.path.getsize(output_file):,} bytes")
    else:
        print("✗ PDF generation failed")