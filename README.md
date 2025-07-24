# Google Docs Font Manager

A comprehensive font management system for analyzing Google Docs files and managing font availability in your document processing system.

## Features

- **Document Font Analysis**: Analyze Google Docs to identify all fonts used
- **Font Availability Checking**: Check which fonts are available in your system
- **Font Management**: Add, remove, and upload font files
- **Web Interface**: Modern, responsive UI for easy management
- **REST API**: Full API for integration with other systems

## Components

### 1. Core Font Manager (`font_manager.py`)
The main logic for font analysis and management:
- Font availability checking
- Document font analysis
- Report generation
- Support for case-insensitive font matching

### 2. REST API (`font_manager_api.py`)
Flask-based API with endpoints:
- `POST /api/fonts/analyze` - Analyze document fonts
- `GET /api/fonts/available` - List available fonts
- `POST /api/fonts/add` - Add a font to the system
- `POST /api/fonts/upload` - Upload font files
- `DELETE /api/fonts/remove` - Remove a font
- `GET /api/health` - Health check

### 3. Web Interface (`index.html`)
Modern, responsive web interface featuring:
- Document analysis form
- Real-time font availability display
- Font upload functionality
- System font management

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Create the fonts directory:
```bash
mkdir fonts
```

## Usage

### Running the API Server

```bash
python font_manager_api.py
```

The API will start on `http://localhost:5000`

### Using the Web Interface

1. Open `index.html` in a web browser
2. Make sure the API server is running
3. Use the interface to:
   - Analyze documents by providing Google Docs ID and fonts list
   - Manage system fonts
   - Upload font files

### Using the Command Line

```bash
python font_manager.py
```

This will run example demonstrations of the font management system.

## API Examples

### Analyze Document Fonts
```bash
curl -X POST http://localhost:5000/api/fonts/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "1AbCDefgHiJKLmnopQRsTuv",
    "fonts": ["IRANSans", "B Nazanin", "Roboto"]
  }'
```

### Add a Font
```bash
curl -X POST http://localhost:5000/api/fonts/add \
  -H "Content-Type: application/json" \
  -d '{"font_name": "B Nazanin"}'
```

### Upload Font File
```bash
curl -X POST http://localhost:5000/api/fonts/upload \
  -F "file=@BNazanin.ttf" \
  -F "font_name=B Nazanin"
```

## Output Format

When analyzing a document, the system provides:

```
Fonts used in the document:
- IRANSans ✅ Available
- B Nazanin ❌ Not available (Please upload the .ttf or .woff file)
- Roboto ✅ Available

1 font(s) missing. Please upload the required font files before processing.
```

Or if all fonts are available:

```
Fonts used in the document:
- Arial ✅ Available
- Roboto ✅ Available

All fonts used in the document are available. Ready to proceed with document processing.
```

## Configuration

### Available Fonts
The system stores available fonts in `available_fonts.json`:
```json
{
  "fonts": ["Arial", "Roboto", "Times New Roman", "IRANSans"]
}
```

### Font Files
Uploaded font files are stored in the `fonts/` directory with supported formats:
- `.ttf` (TrueType Font)
- `.woff` (Web Open Font Format)
- `.woff2` (Web Open Font Format 2)
- `.otf` (OpenType Font)

## Integration Notes

### Google Docs API
The current implementation includes a placeholder for Google Docs API integration. To fully integrate:

1. Set up Google Cloud Project
2. Enable Google Docs API
3. Obtain credentials
4. Update `GoogleDocsParser.parse_document_fonts()` to:
   - Authenticate with Google
   - Fetch document content
   - Extract font families from styles

### Frontend Integration
The web interface can be integrated into existing systems by:
- Adjusting the API base URL in the JavaScript
- Customizing the styling to match your design system
- Adding authentication if needed

## Error Handling

The system includes comprehensive error handling:
- Invalid font files are rejected
- Duplicate fonts are prevented
- Missing parameters return appropriate error messages
- All errors are returned with HTTP status codes and descriptive messages

## Future Enhancements

- Direct Google Docs API integration
- Batch document analysis
- Font similarity detection
- Font substitution suggestions
- Font preview functionality
- Export/import font configurations