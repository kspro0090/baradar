#!/usr/bin/env python3
"""
Google Docs Font Manager API
RESTful API for analyzing Google Docs fonts and checking availability.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from typing import List, Dict, Optional
import os
import json
from font_manager import FontManager, GoogleDocsParser

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Configuration
FONTS_CONFIG_FILE = "available_fonts.json"
UPLOAD_FOLDER = "fonts"

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global font manager instance
font_manager = None


def load_available_fonts() -> List[str]:
    """Load available fonts from configuration file."""
    if os.path.exists(FONTS_CONFIG_FILE):
        with open(FONTS_CONFIG_FILE, 'r') as f:
            data = json.load(f)
            return data.get('fonts', [])
    return ['Arial', 'Roboto', 'Times New Roman']  # Default fonts


def save_available_fonts(fonts: List[str]):
    """Save available fonts to configuration file."""
    with open(FONTS_CONFIG_FILE, 'w') as f:
        json.dump({'fonts': fonts}, f, indent=2)


def initialize_font_manager():
    """Initialize the global font manager with available fonts."""
    global font_manager
    available_fonts = load_available_fonts()
    font_manager = FontManager(available_fonts)


@app.route('/api/fonts/analyze', methods=['POST'])
def analyze_document():
    """
    Analyze fonts in a Google Docs document.
    
    Expected JSON payload:
    {
        "doc_id": "1AbCDefgHiJKLmnopQRsTuv",
        "fonts": ["IRANSans", "B Nazanin", "Roboto"]  // Optional, if not using Google API
    }
    
    Returns:
    {
        "success": true,
        "doc_id": "1AbCDefgHiJKLmnopQRsTuv",
        "analysis": {
            "fonts": [
                {
                    "name": "IRANSans",
                    "available": true,
                    "status": "✅ Available"
                },
                {
                    "name": "B Nazanin",
                    "available": false,
                    "status": "❌ Not available",
                    "message": "Please upload the .ttf or .woff file"
                }
            ],
            "summary": {
                "total_fonts": 3,
                "available_fonts": 2,
                "missing_fonts": 1,
                "all_available": false
            }
        },
        "report": "Formatted report text..."
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'doc_id' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing doc_id in request'
            }), 400
        
        doc_id = data['doc_id']
        
        # Get fonts either from request or Google Docs API
        if 'fonts' in data:
            # Use provided fonts list
            document_fonts = data['fonts']
        else:
            # In production, this would use Google Docs API
            document_fonts = GoogleDocsParser.parse_document_fonts(doc_id)
            
            if not document_fonts:
                return jsonify({
                    'success': False,
                    'error': 'Could not fetch fonts from Google Docs. Please provide fonts list in request.'
                }), 400
        
        # Analyze fonts
        font_analysis = font_manager.analyze_document_fonts(document_fonts)
        
        # Prepare detailed response
        fonts_detail = []
        for font_name, info in font_analysis.items():
            fonts_detail.append({
                'name': font_name,
                'available': info.status.value.startswith('✅'),
                'status': info.status.value,
                'message': info.message if info.message else None
            })
        
        # Calculate summary
        total_fonts = len(font_analysis)
        available_count = sum(1 for f in fonts_detail if f['available'])
        missing_count = total_fonts - available_count
        
        # Generate report
        report = font_manager.format_analysis_report(font_analysis)
        
        return jsonify({
            'success': True,
            'doc_id': doc_id,
            'analysis': {
                'fonts': fonts_detail,
                'summary': {
                    'total_fonts': total_fonts,
                    'available_fonts': available_count,
                    'missing_fonts': missing_count,
                    'all_available': missing_count == 0
                }
            },
            'report': report
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fonts/available', methods=['GET'])
def get_available_fonts():
    """Get list of all available fonts in the system."""
    try:
        fonts = load_available_fonts()
        return jsonify({
            'success': True,
            'fonts': sorted(fonts),
            'count': len(fonts)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fonts/add', methods=['POST'])
def add_font():
    """
    Add a new font to the available fonts list.
    
    Expected JSON payload:
    {
        "font_name": "B Nazanin"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'font_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing font_name in request'
            }), 400
        
        font_name = data['font_name'].strip()
        
        # Load current fonts
        fonts = load_available_fonts()
        
        # Check if already exists (case-insensitive)
        if any(f.lower() == font_name.lower() for f in fonts):
            return jsonify({
                'success': False,
                'error': f'Font "{font_name}" already exists'
            }), 400
        
        # Add new font
        fonts.append(font_name)
        save_available_fonts(fonts)
        
        # Reinitialize font manager
        initialize_font_manager()
        
        return jsonify({
            'success': True,
            'message': f'Font "{font_name}" added successfully',
            'fonts': sorted(fonts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fonts/upload', methods=['POST'])
def upload_font():
    """
    Upload a font file and add it to available fonts.
    
    Expects multipart/form-data with:
    - file: The font file (.ttf, .woff, .woff2)
    - font_name: The name of the font (optional, extracted from filename if not provided)
    """
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        # Validate file extension
        allowed_extensions = {'.ttf', '.woff', '.woff2', '.otf'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'Invalid file type. Allowed types: {", ".join(allowed_extensions)}'
            }), 400
        
        # Get font name
        font_name = request.form.get('font_name')
        if not font_name:
            # Extract from filename
            font_name = os.path.splitext(file.filename)[0]
        
        # Save file
        safe_filename = f"{font_name.replace(' ', '_')}{file_ext}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        file.save(file_path)
        
        # Add to available fonts
        fonts = load_available_fonts()
        if font_name not in fonts:
            fonts.append(font_name)
            save_available_fonts(fonts)
            initialize_font_manager()
        
        return jsonify({
            'success': True,
            'message': f'Font "{font_name}" uploaded successfully',
            'font_name': font_name,
            'file_path': file_path
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fonts/remove', methods=['DELETE'])
def remove_font():
    """
    Remove a font from the available fonts list.
    
    Expected JSON payload:
    {
        "font_name": "B Nazanin"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'font_name' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing font_name in request'
            }), 400
        
        font_name = data['font_name']
        
        # Load current fonts
        fonts = load_available_fonts()
        
        # Remove font (case-insensitive)
        original_count = len(fonts)
        fonts = [f for f in fonts if f.lower() != font_name.lower()]
        
        if len(fonts) == original_count:
            return jsonify({
                'success': False,
                'error': f'Font "{font_name}" not found'
            }), 404
        
        # Save updated list
        save_available_fonts(fonts)
        initialize_font_manager()
        
        return jsonify({
            'success': True,
            'message': f'Font "{font_name}" removed successfully',
            'fonts': sorted(fonts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'fonts_loaded': len(load_available_fonts())
    })


if __name__ == '__main__':
    # Initialize font manager on startup
    initialize_font_manager()
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)