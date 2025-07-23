# Font Management Feature

## Overview

This feature automatically detects fonts used in Word (.docx) templates and ensures they are available for PDF generation. The system provides a complete font management solution with automatic detection, validation, upload capabilities, and intelligent fallback mechanisms.

## Key Features

### 1. **Automatic Font Detection**
- Extracts all fonts from Word documents including:
  - Paragraph fonts
  - Table fonts
  - Header/footer fonts
  - Default document font
- Provides detailed font usage information

### 2. **Font Availability Checking**
- Case-insensitive font matching
- Partial match tolerance (e.g., `vazir` matches `Vazir-Regular.ttf`)
- Intelligent normalization removes common suffixes (Regular, Bold, etc.)
- Real-time validation before PDF generation

### 3. **Font Management Interface**
- Upload fonts through admin panel
- View all available fonts with details
- Delete unused fonts
- Automatic font registration with ReportLab

### 4. **Smart Font Fallback**
- Uses requested font if available
- Falls back to Persian-compatible fonts for RTL text
- Final fallback to system default fonts
- Prevents PDF generation failures

## Technical Implementation

### Components

#### `font_manager.py`
The core font management module providing:
- `FontManager` class for all font operations
- Font extraction from DOCX files
- Font availability checking with normalization
- Font registration with ReportLab
- Upload/delete functionality

#### Key Methods:
```python
# Extract fonts from document
font_details = font_manager.extract_fonts_from_docx(docx_path)

# Check if font is available
is_available, matched_file = font_manager.is_font_available("Vazir")

# Get missing fonts
missing = font_manager.get_missing_fonts(font_set)

# Get font for PDF (with fallback)
pdf_font = font_manager.get_font_for_pdf("RequestedFont")
```

### Font Normalization Algorithm

The system normalizes font names for matching:
1. Convert to lowercase
2. Remove common suffixes (Regular, Bold, Italic, etc.)
3. Remove spaces, hyphens, underscores
4. Compare normalized names

Example:
- `Vazir-Bold` → `vazir`
- `IRANSans Regular` → `iransans`
- `B Nazanin Bold` → `bnazanin`

## Usage Guide

### For System Administrators

#### 1. **Checking Template Fonts**
- Edit any service in the admin panel
- Click "بررسی فونت‌ها" (Check Fonts) button
- View detected fonts and their availability status
- Missing fonts are highlighted in red

#### 2. **Managing Fonts**
- Navigate to "مدیریت فونت‌ها" (Font Management) from dashboard
- View all available fonts with:
  - Font name
  - File name
  - File size
  - Registration status

#### 3. **Uploading Fonts**
- Click on font management in admin dashboard
- Select TTF or OTF font file
- Click "آپلود فونت" (Upload Font)
- Font is automatically registered for use

#### 4. **Handling Missing Fonts**
When fonts are missing:
- System shows clear warning with font names
- Direct link to upload missing fonts
- PDF generation continues with fallback fonts

### For Developers

#### Integration with Document Processor
```python
# Initialize document processor with font manager
doc_processor = DocumentProcessor(font_manager=font_manager)

# Fonts are automatically resolved during PDF generation
pdf_font = self.font_manager.get_font_for_pdf(requested_font)
```

#### Adding New Font Sources
Extend the `FontManager` class:
```python
class CustomFontManager(FontManager):
    def _scan_additional_sources(self):
        # Add system fonts, web fonts, etc.
        pass
```

## Font Directory Structure

```
static/
└── fonts/
    ├── Vazir.ttf
    ├── Vazir-Bold.ttf
    ├── IRANSansWeb.ttf
    ├── IRANSansWeb_Bold.ttf
    └── [other fonts...]
```

## API Endpoints

### Font Checking
- `GET /admin/services/<service_id>/check-fonts`
  - Returns font usage and availability status

### Font Management
- `GET /admin/fonts` - Font management page
- `POST /admin/fonts/upload` - Upload new font
- `POST /admin/fonts/<filename>/delete` - Delete font

## Error Handling

### Missing Fonts
- Non-blocking: PDF generation continues with fallbacks
- Clear warnings in admin interface
- Detailed logs for debugging

### Font Registration Failures
- Invalid font files are rejected
- Corrupted fonts are not registered
- Clear error messages to admin

## Persian/RTL Support

### Default Persian Fonts
Priority order for Persian text:
1. Requested font (if available)
2. Vazir
3. IRANSans
4. B Nazanin
5. B Mitra
6. System default (Helvetica)

### Font Features
- Full Unicode support
- Proper RTL rendering
- Persian number support
- Diacritic marks

## Best Practices

1. **Pre-upload Common Fonts**
   - Upload frequently used fonts before creating templates
   - Include both regular and bold variants

2. **Template Design**
   - Use standard font names in templates
   - Avoid custom or system-specific fonts
   - Test templates with actual fonts

3. **Font Naming**
   - Use consistent naming conventions
   - Keep original font file names
   - Avoid special characters

4. **Performance**
   - Fonts are registered once at startup
   - Font matching is optimized with caching
   - Minimal overhead during PDF generation

## Troubleshooting

### Common Issues

1. **Font Not Found Despite Upload**
   - Check font file name normalization
   - Verify font registration in logs
   - Ensure file has correct extension

2. **PDF Shows Wrong Font**
   - Check font name in Word template
   - Verify font is properly registered
   - Check fallback chain in logs

3. **Font Upload Fails**
   - Ensure file is valid TTF/OTF
   - Check file permissions
   - Verify disk space

### Debug Mode
Enable detailed logging:
```python
import logging
logging.getLogger('font_manager').setLevel(logging.DEBUG)
```

## Testing

Run the test suite:
```bash
./test_font_management.py
```

Tests include:
- Font detection from DOCX
- Font name normalization
- Font matching algorithms
- Fallback mechanisms

## Future Enhancements

1. **Font Preview**: Show font preview in management interface
2. **Batch Upload**: Upload multiple fonts at once
3. **Font Families**: Group related fonts (Regular, Bold, Italic)
4. **Web Fonts**: Support for Google Fonts and web fonts
5. **Font Subsetting**: Include only used characters for smaller PDFs
6. **Auto-download**: Automatically download missing open-source fonts