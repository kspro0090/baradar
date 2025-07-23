"""
Google Docs API Service Module
Handles authentication and document operations
"""

import os
import re
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError

class GoogleDocsService:
    """Service class for Google Docs API operations"""
    
    SCOPES = [
        'https://www.googleapis.com/auth/documents.readonly',
        'https://www.googleapis.com/auth/drive.readonly',
        'https://www.googleapis.com/auth/drive.file'
    ]
    
    def __init__(self, credentials_path='credentials.json'):
        """Initialize Google Docs service with credentials"""
        self.credentials_path = credentials_path
        self.docs_service = None
        self.drive_service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate using service account credentials"""
        try:
            if os.path.exists(self.credentials_path):
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path, scopes=self.SCOPES)
                
                self.docs_service = build('docs', 'v1', credentials=creds)
                self.drive_service = build('drive', 'v3', credentials=creds)
            else:
                raise FileNotFoundError(f"Credentials file not found: {self.credentials_path}")
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google API: {str(e)}")
    
    def get_document_content(self, doc_id):
        """Get the content of a Google Doc"""
        try:
            document = self.docs_service.documents().get(documentId=doc_id).execute()
            return document
        except HttpError as error:
            if error.resp.status == 404:
                raise Exception(f"Document not found: {doc_id}")
            else:
                raise Exception(f"Error accessing document: {str(error)}")
    
    def extract_text_and_placeholders(self, doc_id):
        """Extract text content and find placeholders from Google Doc"""
        document = self.get_document_content(doc_id)
        
        text_content = []
        placeholders = set()
        
        # Extract text from document content
        content = document.get('body', {}).get('content', [])
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                para_text = ''
                
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        text = elem['textRun'].get('content', '')
                        para_text += text
                
                if para_text.strip():
                    text_content.append(para_text.strip())
                    
                    # Find placeholders
                    found_placeholders = re.findall(r'\{\{([^}]+)\}\}', para_text)
                    placeholders.update(found_placeholders)
        
        return {
            'text_content': text_content,
            'placeholders': list(placeholders),
            'title': document.get('title', 'Untitled')
        }
    
    def create_document_copy(self, doc_id, copy_title):
        """Create a copy of the Google Doc"""
        try:
            copy_metadata = {
                'name': copy_title
            }
            
            copied_file = self.drive_service.files().copy(
                fileId=doc_id,
                body=copy_metadata
            ).execute()
            
            return copied_file['id']
        except HttpError as error:
            raise Exception(f"Error creating document copy: {str(error)}")
    
    def replace_placeholders_in_doc(self, doc_id, replacements):
        """Replace placeholders in a Google Doc copy"""
        try:
            # First, get the document to find all text positions
            document = self.get_document_content(doc_id)
            
            # Build requests for batch update
            requests = []
            
            # Process content in reverse order to maintain indices
            content = document.get('body', {}).get('content', [])
            
            for element in reversed(content):
                if 'paragraph' in element:
                    paragraph = element['paragraph']
                    
                    for elem in reversed(paragraph.get('elements', [])):
                        if 'textRun' in elem:
                            text = elem['textRun'].get('content', '')
                            start_index = elem.get('startIndex', 0)
                            end_index = elem.get('endIndex', 0)
                            
                            # Check for placeholders
                            for placeholder, value in replacements.items():
                                placeholder_pattern = f'{{{{{placeholder}}}}}'
                                if placeholder_pattern in text:
                                    # Calculate the exact positions
                                    placeholder_start = text.find(placeholder_pattern)
                                    if placeholder_start != -1:
                                        absolute_start = start_index + placeholder_start
                                        absolute_end = absolute_start + len(placeholder_pattern)
                                        
                                        # Create replace request
                                        requests.append({
                                            'replaceAllText': {
                                                'containsText': {
                                                    'text': placeholder_pattern,
                                                    'matchCase': True
                                                },
                                                'replaceText': value
                                            }
                                        })
            
            # Execute batch update if there are replacements
            if requests:
                result = self.docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={'requests': requests}
                ).execute()
                
                return result
            
            return None
            
        except HttpError as error:
            raise Exception(f"Error replacing placeholders: {str(error)}")
    
    def export_as_pdf(self, doc_id):
        """Export Google Doc as PDF"""
        try:
            request = self.drive_service.files().export_media(
                fileId=doc_id,
                mimeType='application/pdf'
            )
            
            file_data = io.BytesIO()
            downloader = MediaIoBaseDownload(file_data, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_data.seek(0)
            return file_data.getvalue()
            
        except HttpError as error:
            raise Exception(f"Error exporting document as PDF: {str(error)}")
    
    def delete_document(self, doc_id):
        """Delete a Google Doc (cleanup temporary copies)"""
        try:
            self.drive_service.files().delete(fileId=doc_id).execute()
        except HttpError as error:
            # Ignore errors when deleting
            pass
    
    def get_document_url(self, doc_id):
        """Get the URL to view/edit the Google Doc"""
        return f"https://docs.google.com/document/d/{doc_id}/edit"
    
    def verify_document_access(self, doc_id):
        """Verify that we can access the document"""
        try:
            self.get_document_content(doc_id)
            return True
        except:
            return False