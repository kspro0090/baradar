#!/usr/bin/env python3
"""
Demo script for the new image-based form feature
"""

import os
import json
from datetime import datetime
from app import app, db
from models import User, Service, FormField, ServiceRequest
from image_pdf_generator import generate_pdf_from_image

def create_demo_data():
    """Create demo data to showcase the image-based form feature"""
    
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            
            # Create a demo user (or get existing one)
            demo_user = User.query.filter_by(username='demo_admin').first()
            if not demo_user:
                demo_user = User(
                    username='demo_admin',
                    email='admin@demo.com',
                    password_hash='demo_hash',
                    role='system_manager'
                )
                db.session.add(demo_user)
                db.session.commit()
                print("✅ Created demo admin user")
            else:
                print("✅ Using existing demo admin user")
            
            # Create a demo image-based service
            demo_service = Service(
                name='فرم درخواست کارت شناسایی',
                description='فرم الکترونیکی برای درخواست کارت شناسایی جدید',
                form_type='image',
                image_path='static/uploads/images/test_form.jpg',
                page_size='A4',
                created_by=demo_user.id
            )
            
            # Add form design data
            design_data = {
                'textboxes': [
                    {
                        'id': 1,
                        'label': 'نام و نام خانوادگی',
                        'field_name': 'full_name',
                        'x': 150,
                        'y': 100,
                        'width': 200,
                        'height': 30,
                        'font_family': 'Arial',
                        'font_size': 14,
                        'color': '#000000'
                    },
                    {
                        'id': 2,
                        'label': 'شماره ملی',
                        'field_name': 'national_id',
                        'x': 150,
                        'y': 150,
                        'width': 150,
                        'height': 30,
                        'font_family': 'Arial',
                        'font_size': 14,
                        'color': '#000000'
                    },
                    {
                        'id': 3,
                        'label': 'تاریخ تولد',
                        'field_name': 'birth_date',
                        'x': 150,
                        'y': 200,
                        'width': 120,
                        'height': 30,
                        'font_family': 'Arial',
                        'font_size': 14,
                        'color': '#000000'
                    }
                ]
            }
            
            demo_service.set_form_design_data(design_data)
            db.session.add(demo_service)
            db.session.commit()
            print("✅ Created demo image-based service")
            
            # Add form fields
            fields_data = [
                {
                    'field_label': 'نام و نام خانوادگی',
                    'field_name': 'full_name',
                    'field_type': 'text',
                    'is_required': True,
                    'placeholder': 'نام و نام خانوادگی خود را وارد کنید',
                    'document_placeholder': '{{full_name}}',
                    'field_order': 1
                },
                {
                    'field_label': 'شماره ملی',
                    'field_name': 'national_id',
                    'field_type': 'text',
                    'is_required': True,
                    'placeholder': 'شماره ملی ۱۰ رقمی',
                    'document_placeholder': '{{national_id}}',
                    'field_order': 2
                },
                {
                    'field_label': 'تاریخ تولد',
                    'field_name': 'birth_date',
                    'field_type': 'date',
                    'is_required': True,
                    'placeholder': 'تاریخ تولد',
                    'document_placeholder': '{{birth_date}}',
                    'field_order': 3
                }
            ]
            
            for field_data in fields_data:
                field = FormField(
                    service_id=demo_service.id,
                    **field_data
                )
                db.session.add(field)
            
            db.session.commit()
            print("✅ Added form fields to demo service")
            
            # Create a demo service request
            demo_request = ServiceRequest(
                service_id=demo_service.id,
                tracking_code='DEMO001',
                form_data=json.dumps({
                    'full_name': 'احمد محمدی',
                    'national_id': '1234567890',
                    'birth_date': '1370-05-15'
                }),
                status='approved',
                approved_by=demo_user.id
            )
            db.session.add(demo_request)
            db.session.commit()
            print("✅ Created demo service request")
            
            # Generate PDF from the demo request
            form_data = demo_request.get_form_data()
            design_data = demo_service.get_form_design_data()
            
            # Prepare paths
            image_path = os.path.join(app.root_path, demo_service.image_path)
            output_path = os.path.join(app.root_path, 'demo_output.pdf')
            
            # Generate PDF
            success = generate_pdf_from_image(
                image_path=image_path,
                output_path=output_path,
                form_data=form_data,
                design_data=design_data,
                page_size=demo_service.page_size,
                fonts_dir=os.path.join(app.root_path, 'fonts')
            )
            
            if success:
                print("✅ Generated demo PDF: demo_output.pdf")
            else:
                print("❌ Failed to generate demo PDF")
            
            print("\n🎉 Demo data created successfully!")
            print(f"📊 Demo Service ID: {demo_service.id}")
            print(f"📊 Demo Request ID: {demo_request.id}")
            print(f"📊 Tracking Code: {demo_request.tracking_code}")
            
        except Exception as e:
            print(f"❌ Error creating demo data: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    create_demo_data()