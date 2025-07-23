# Word Template Placeholder Replacement Fix

## Overview

This update fixes the issue where placeholders like `{{employee_name}}` in Word (.docx) templates were not being properly replaced with actual data. The solution handles complex scenarios including:

- Placeholders that span multiple runs in Word documents
- Placeholders in tables, headers, and footers
- Preservation of formatting (bold, italic, fonts, etc.)
- Full support for RTL (Persian) text
- Complex layouts with tables and multiple columns

## Key Improvements

### 1. **Robust Placeholder Detection**
- Detects all `{{...}}` placeholders throughout the document
- Handles placeholders in:
  - Regular paragraphs
  - Tables
  - Headers and footers
  - Formatted text (bold, italic, etc.)

### 2. **Smart Placeholder Replacement**
- Reconstructs paragraph text to handle placeholders spanning multiple runs
- Preserves original formatting while replacing placeholders
- Handles RTL text properly in both detection and replacement

### 3. **Automatic Placeholder Discovery**
- New endpoint `/admin/services/<service_id>/detect-placeholders`
- UI button in field management to auto-detect placeholders
- Shows which placeholders are mapped and which need mapping

### 4. **Enhanced PDF Generation**
- Better handling of document structure preservation
- Improved table rendering with proper RTL alignment
- Maintains heading styles and paragraph formatting

## Usage Guide

### For System Administrators

#### 1. **Creating Templates**
- Create Word documents with placeholders in the format `{{placeholder_name}}`
- Placeholders can be placed anywhere:
  ```
  Dear {{employee_name}},
  
  Your request for {{service_type}} from {{start_date}} to {{end_date}} 
  has been received.
  ```

#### 2. **Uploading Templates**
- Upload the template to Google Drive
- Copy the file ID and configure it in the service

#### 3. **Mapping Placeholders**
- Go to service field management
- Click "شناسایی خودکار" (Auto Detect) to find all placeholders
- Create form fields and map them to placeholders:
  - Field Name: `employee_name`
  - Document Placeholder: `employee_name`

### For Approval Administrators

- The approval process remains the same
- When approving, the system will:
  1. Export the template from Google Drive
  2. Replace all mapped placeholders with form data
  3. Generate a PDF with the filled data
  4. Save the PDF for user download

## Technical Details

### Placeholder Processing Algorithm

1. **Full Text Reconstruction**: The system reconstructs the full paragraph text from all runs to detect placeholders that might be split
2. **Format Preservation**: Formatting information is collected before replacement
3. **Smart Replacement**: Text is replaced while maintaining the original formatting style

### Example Code

```python
# The improved replacement method handles split placeholders
def _replace_placeholders_in_paragraph(self, paragraph, replacements):
    # Get full text from all runs
    full_text = paragraph.text
    
    # Check for placeholders
    for placeholder, value in replacements.items():
        placeholder_pattern = f'{{{{{placeholder}}}}}'
        full_text = full_text.replace(placeholder_pattern, value)
    
    # Preserve formatting while replacing
    # ... formatting preservation logic ...
```

### Supported Features

- **Text Formatting**: Bold, italic, underline, fonts, sizes
- **Paragraph Alignment**: Left, right, center, justified
- **Tables**: Full table support with cell formatting
- **RTL Support**: Proper Persian/Arabic text handling
- **Complex Layouts**: Multi-column, nested structures

## Testing

### Test Scripts

1. **`create_test_template.py`**: Creates a sample Word template with various placeholders
2. **`test_placeholder_replacement.py`**: Tests the replacement functionality

### Running Tests

```bash
# Create a test template
./create_test_template.py

# Test placeholder replacement
./test_placeholder_replacement.py
```

### Test Coverage

- Basic placeholder replacement
- Placeholders spanning multiple runs
- Formatted placeholders
- Multiple placeholders in one paragraph
- Table placeholders
- RTL text replacement

## Troubleshooting

### Common Issues

1. **Placeholder Not Replaced**
   - Ensure placeholder format is exactly `{{name}}`
   - Check that the field's document_placeholder matches
   - Use auto-detect to find exact placeholder names

2. **Formatting Lost**
   - The system preserves basic formatting (bold, italic)
   - Complex formatting may be simplified
   - Tables maintain their structure

3. **RTL Text Issues**
   - Ensure Persian fonts are installed
   - Check that text direction is set correctly in template

### Debug Mode

Enable debug output in `document_processor.py`:
```python
print(f"Found placeholders in document: {placeholders_found}")
```

## Migration Notes

- No database changes required
- Existing templates will work with the new system
- Recommended to test templates after update

## Future Enhancements

1. **Image Support**: Handle images and logos in templates
2. **Advanced Formatting**: Support for more complex Word formatting
3. **Template Preview**: Show preview with sample data
4. **Bulk Processing**: Process multiple requests at once
5. **Template Versioning**: Track template changes over time