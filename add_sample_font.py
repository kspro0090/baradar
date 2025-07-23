#!/usr/bin/env python3
"""
Script to download and add a sample Persian font to the system
This will download Vazir font which is a popular open-source Persian font
"""

import os
import sys
import requests
from app import app, db
from models import Font

def download_vazir_font():
    """Download Vazir font from GitHub"""
    font_url = "https://github.com/rastikerdar/vazir-font/raw/v30.1.0/dist/Vazir-Regular.ttf"
    font_filename = "Vazir-Regular.ttf"
    fonts_folder = app.config['FONTS_FOLDER']
    
    # Create fonts folder if it doesn't exist
    os.makedirs(fonts_folder, exist_ok=True)
    
    font_path = os.path.join(fonts_folder, font_filename)
    
    # Check if font already exists
    if os.path.exists(font_path):
        print(f"Font already exists at: {font_path}")
        return font_filename
    
    print(f"Downloading Vazir font from: {font_url}")
    
    try:
        response = requests.get(font_url, stream=True)
        response.raise_for_status()
        
        with open(font_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Font downloaded successfully to: {font_path}")
        return font_filename
    except Exception as e:
        print(f"Error downloading font: {str(e)}")
        return None

def add_font_to_database(filename):
    """Add the font to the database"""
    with app.app_context():
        # Check if font already exists in database
        existing_font = Font.query.filter_by(filename=filename).first()
        if existing_font:
            print(f"Font already exists in database: {existing_font.name}")
            if not existing_font.is_default:
                existing_font.is_default = True
                db.session.commit()
                print("Set as default font")
            return
        
        # Remove default from other fonts
        Font.query.filter_by(is_default=True).update({'is_default': False})
        
        # Add new font
        font = Font(
            name="Vazir (فونت وزیر)",
            filename=filename,
            is_default=True
        )
        
        db.session.add(font)
        db.session.commit()
        
        print(f"Font added to database: {font.name}")
        print("Font set as default")

def main():
    """Main function"""
    print("=== Adding Sample Persian Font ===\n")
    
    # Download font
    filename = download_vazir_font()
    if not filename:
        print("Failed to download font")
        sys.exit(1)
    
    # Add to database
    add_font_to_database(filename)
    
    print("\n✓ Sample Persian font added successfully!")
    print("You can now generate PDFs with proper Persian text display.")

if __name__ == '__main__':
    main()