#!/usr/bin/env python3
"""
Test script for image-based form functionality
"""

import os
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont
from app import app, db
from models import Service, User, FormField
from image_pdf_generator import ImagePDFGenerator

def create_test_image():
    """Create a test image for testing"""
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add some text to make it look like a form
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    draw.text((50, 50), "Test Form", fill='black', font=font)
    draw.text((50, 100), "Name: ________________", fill='black', font=font)
    draw.text((50, 150), "Email: ________________", fill='black', font=font)
    draw.text((50, 200), "Phone: ________________", fill='black', font=font)
    
    # Save the test image
    test_image_path = os.path.join('static', 'uploads', 'images', 'test_form.jpg')
    os.makedirs(os.path.dirname(test_image_path), exist_ok=True)
    img.save(test_image_path, 'JPEG')
    
    return test_image_path

def test_image_pdf_generator():
    """Test the image PDF generator"""
    print("Testing Image PDF Generator...")
    
    # Create test image
    image_path = create_test_image()
    print(f"Created test image: {image_path}")
    
    # Test design data
    design_data = {
        'textboxes': [
            {
                'id': 1,
                'x': 200,
                'y': 100,
                'width': 200,
                'height': 30,
                'label': 'نام و نام خانوادگی',
                'field': 'name',
                'font': 'Arial',
                'size': 14,
                'color': '#000000'
            },
            {
                'id': 2,
                'x': 200,
                'y': 150,
                'width': 200,
                'height': 30,
                'label': 'ایمیل',
                'field': 'email',
                'font': 'Arial',
                'size': 14,
                'color': '#000000'
            }
        ]
    }
    
    # Test form data
    form_data = {
        'name': 'احمد محمدی',
        'email': 'ahmad@example.com'
    }
    
    # Test PDF generation
    generator = ImagePDFGenerator()
    output_path = 'test_output.pdf'
    
    try:
        success = generator.generate_pdf_from_image_pil(
            image_path=image_path,
            output_path=output_path,
            form_data=form_data,
            design_data=design_data,
            page_size='A4'
        )
        
        if success:
            print(f"✅ PDF generated successfully: {output_path}")
            return True
        else:
            print("❌ PDF generation failed")
            return False
            
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        return False

def test_database_models():
    """Test database models for image forms"""
    print("\nTesting Database Models...")
    
    with app.app_context():
        try:
            # Test creating a service with image form type
            service = Service(
                name='Test Image Form',
                description='Test service with image form',
                form_type='image',
                image_path='static/uploads/images/test_form.jpg',
                page_size='A4'
            )
            
            # Test form design data
            design_data = {
                'textboxes': [
                    {
                        'id': 1,
                        'x': 100,
                        'y': 100,
                        'width': 200,
                        'height': 30,
                        'label': 'نام',
                        'field': 'name',
                        'font': 'Arial',
                        'size': 12,
                        'color': '#000000'
                    }
                ]
            }
            service.set_form_design_data(design_data)
            
            # Test retrieving design data
            retrieved_data = service.get_form_design_data()
            if retrieved_data == design_data:
                print("✅ Form design data storage/retrieval works correctly")
            else:
                print("❌ Form design data storage/retrieval failed")
                return False
            
            print("✅ Database models work correctly")
            return True
            
        except Exception as e:
            print(f"❌ Database model test failed: {str(e)}")
            return False

def test_form_creation():
    """Test creating a complete image-based form"""
    print("\nTesting Form Creation...")
    
    with app.app_context():
        try:
            # Create test image
            image_path = create_test_image()
            
            # Create service
            service = Service(
                name='Complete Test Form',
                description='Complete test of image form functionality',
                form_type='image',
                image_path=image_path,
                page_size='A4'
            )
            
            # Add form fields
            field1 = FormField(
                service=service,
                field_label='نام و نام خانوادگی',
                field_name='name',
                field_type='text',
                is_required=True,
                placeholder='نام خود را وارد کنید',
                document_placeholder='name'
            )
            
            field2 = FormField(
                service=service,
                field_label='ایمیل',
                field_name='email',
                field_type='email',
                is_required=True,
                placeholder='ایمیل خود را وارد کنید',
                document_placeholder='email'
            )
            
            # Set design data
            design_data = {
                'textboxes': [
                    {
                        'id': 1,
                        'x': 200,
                        'y': 100,
                        'width': 200,
                        'height': 30,
                        'label': 'نام و نام خانوادگی',
                        'field': 'name',
                        'font': 'Arial',
                        'size': 14,
                        'color': '#000000'
                    },
                    {
                        'id': 2,
                        'x': 200,
                        'y': 150,
                        'width': 200,
                        'height': 30,
                        'label': 'ایمیل',
                        'field': 'email',
                        'font': 'Arial',
                        'size': 14,
                        'color': '#000000'
                    }
                ]
            }
            service.set_form_design_data(design_data)
            
            print("✅ Complete form creation test passed")
            return True
            
        except Exception as e:
            print(f"❌ Form creation test failed: {str(e)}")
            return False

def main():
    """Run all tests"""
    print("🧪 Testing Image-Based Form Functionality")
    print("=" * 50)
    
    tests = [
        test_image_pdf_generator,
        test_database_models,
        test_form_creation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Image-based form functionality is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == '__main__':
    sys.exit(main())