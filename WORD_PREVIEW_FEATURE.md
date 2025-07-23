# Word Document Preview Feature

## Overview
Added a live preview feature for Word (.docx) templates in the Flask admin panel. When system managers upload a Word template while creating or editing a service, they can immediately see a preview of the document content.

## Features Implemented

### 1. Backend Route (`/admin/services/preview-docx`)
- Accepts POST requests with Word file uploads
- Uses `python-docx` to read document content
- Extracts up to 5 paragraphs from the document
- Identifies placeholders using regex pattern `{{PLACEHOLDER}}`
- Returns JSON response with paragraphs, placeholders, and total count

### 2. Frontend Implementation

#### Create Service Page (`templates/admin/create_service.html`)
- Added preview container below file upload field
- Shows loading spinner during AJAX request
- Displays extracted paragraphs with RTL support
- Highlights placeholders with yellow background
- Shows list of found placeholders as badges

#### Edit Service Page (`templates/admin/edit_service.html`)
- Same preview functionality as create page
- Shows current template filename if exists
- Preview only shows when new file is selected

### 3. AJAX Implementation
- Uses Fetch API for asynchronous file upload
- No page reload required
- Instant feedback on file selection
- Error handling for invalid files

### 4. UI/UX Enhancements
- Persian RTL text properly displayed
- Placeholders highlighted with `<mark>` tags
- Responsive card-based design
- Loading states and error messages
- Maximum 5 paragraphs shown with scroll

### 5. Additional Features
- Created `edit_service` route for editing service details
- Added edit button in admin dashboard
- Created sample Word template generator script
- Added CSS styling for preview components

## Files Modified/Created

1. **app.py**
   - Added `preview_docx()` route
   - Added `edit_service()` route

2. **templates/admin/create_service.html**
   - Added preview container and JavaScript

3. **templates/admin/edit_service.html** (new)
   - Complete edit service page with preview

4. **templates/admin/dashboard.html**
   - Added edit service button

5. **static/css/style.css**
   - Added preview-specific styles

6. **create_sample_docx.py** (new)
   - Script to generate test Word templates

## Usage

### For System Managers:
1. Navigate to "Create Service" or "Edit Service"
2. Select a Word (.docx) file
3. Preview appears automatically below the file input
4. Shows:
   - Document paragraphs (max 5)
   - Identified placeholders
   - Total paragraph count

### Technical Details:
- Placeholders format: `{{PLACEHOLDER_NAME}}`
- Supports Persian/Arabic text
- File validation (only .docx allowed)
- In-memory file processing (no temp files)

## Testing

1. Run the sample template generator:
   ```bash
   python3 create_sample_docx.py
   ```

2. Upload the generated template in admin panel
3. Verify preview shows paragraphs and placeholders
4. Test with Persian text documents

## Security Considerations
- File type validation (only .docx)
- Login required + system manager role required
- File size limited by Flask config
- No execution of document macros