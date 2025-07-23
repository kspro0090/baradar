# Local PDF Generation Feature

## Overview

This feature updates the Flask application to generate PDFs locally without modifying the original Google Drive templates. Instead of creating copies of templates in Google Drive (which can hit quota limits), the system now:

1. Exports the template from Google Drive
2. Processes it locally to replace placeholders
3. Generates a PDF with full Persian (RTL) support
4. Leaves the original template untouched

## Key Benefits

- **No Drive Quota Issues**: Avoids hitting Google Drive API quotas by not creating document copies
- **Original Template Preservation**: Templates remain unchanged and can be reused indefinitely
- **Better Performance**: Local processing is faster than multiple API calls
- **Full Persian Support**: Proper RTL text rendering in generated PDFs
- **Fallback Options**: Multiple export formats (DOCX, HTML) ensure reliability

## Technical Implementation

### Document Processing Flow

1. **Template Export**: When a request is approved, the template is exported from Google Drive
2. **Format Priority**: 
   - First tries DOCX format (better formatting preservation)
   - Falls back to HTML if DOCX fails
   - Final fallback to direct PDF export without replacements
3. **Local Processing**: Placeholders are replaced in memory without modifying the original
4. **PDF Generation**: Uses ReportLab with Persian fonts for proper RTL rendering

### Components

#### `document_processor.py`
- Handles local document processing
- Replaces placeholders in DOCX and HTML formats
- Generates PDFs with proper Persian text support
- Manages font registration for RTL languages

#### `google_docs_service.py`
- Enhanced with new export methods:
  - `export_as_docx()`: Exports as Word document
  - `export_as_html()`: Exports as HTML
  - `export_as_pdf()`: Direct PDF export (fallback)

#### Updated `generate_pdf_from_request()`
- No longer creates document copies
- Processes templates locally
- Implements multiple fallback strategies
- Prevents approval if PDF generation fails

## Persian/RTL Support

### Font Support
- Uses Vazir and IRANSans fonts
- Automatically registers fonts for PDF generation
- Proper text shaping with `arabic-reshaper`
- Correct RTL display with `python-bidi`

### Layout Preservation
- Tables maintain structure and alignment
- Headers and paragraphs preserve formatting
- Images and styles are retained where possible

## Error Handling

### Approval Protection
If PDF generation fails:
- The request remains in "pending" status
- No approval is recorded
- Admin sees clear error message
- Can retry after fixing issues

### Fallback Strategy
1. Try DOCX processing → Best formatting
2. Try HTML processing → Good compatibility
3. Direct PDF export → No placeholders but ensures output

## Usage

### For System Administrators
- Upload Google Docs templates as before
- Use `{{placeholder}}` syntax in templates
- Ensure templates have proper formatting
- No need to manage template copies

### For Approval Administrators
- Approve requests normally
- If PDF generation fails, request stays pending
- Clear error messages guide troubleshooting
- Can safely retry failed approvals

## Dependencies

New Python packages added:
- `python-docx`: For processing Word documents
- `beautifulsoup4`: For HTML parsing
- `weasyprint`: Alternative PDF generation (optional)

Existing packages utilized:
- `reportlab`: PDF generation with Persian support
- `arabic-reshaper`: Arabic/Persian text shaping
- `python-bidi`: Bidirectional text support

## Migration from Previous System

If migrating from the template file system:
1. No database changes needed
2. Templates continue to work as before
3. Remove any template file management code
4. Update UI to remove template availability indicators

## Best Practices

1. **Template Design**:
   - Use clear placeholder names: `{{name}}`, `{{email}}`
   - Test templates with sample data
   - Keep formatting simple for better compatibility

2. **Performance**:
   - Templates are cached in memory during processing
   - Temporary files are cleaned up automatically
   - No persistent storage of processed documents

3. **Security**:
   - Original templates remain read-only
   - Processed documents exist only in memory
   - Generated PDFs stored locally with proper access control

## Troubleshooting

### Common Issues

1. **"Failed to generate PDF from DOCX"**
   - Check if template has complex formatting
   - System will try HTML format automatically

2. **Persian text not displaying correctly**
   - Ensure fonts are installed in `static/fonts/`
   - Check font file permissions

3. **Placeholders not replaced**
   - Verify placeholder syntax: `{{placeholder}}`
   - Check field mapping in service configuration

### Debug Mode
Enable logging to see detailed processing steps:
```python
app.logger.setLevel(logging.DEBUG)
```

## Future Enhancements

1. **Template Caching**: Cache exported templates for faster processing
2. **Advanced Formatting**: Support for more complex document structures
3. **Multiple Output Formats**: Generate DOCX, HTML in addition to PDF
4. **Template Preview**: Preview with sample data before approval