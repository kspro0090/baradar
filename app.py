from flask import Flask, render_template, redirect, url_for, flash, request, send_file, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from functools import wraps
import os
import secrets
import json
from datetime import datetime

from google_docs_service import GoogleDocsService
from wtforms.validators import DataRequired, Email
from wtforms import StringField, IntegerField, TextAreaField, SelectField

from config import Config
from models import db, User, Service, FormField, ServiceRequest, TemplateFile
from forms import (LoginForm, CreateAdminForm, ServiceForm, FormFieldForm, 
                   ServiceRequestForm, ApprovalForm, TrackingForm)

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'لطفاً وارد شوید.'

# Create directories if they don't exist
os.makedirs(app.config['PDF_OUTPUT_FOLDER'], exist_ok=True)

# Initialize Google Docs service
google_docs_service = None
try:
    google_docs_service = GoogleDocsService(os.path.join(os.path.dirname(__file__), 'credentials.json'))
except Exception as e:
    app.logger.error(f"Failed to initialize Google Docs service: {str(e)}")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Decorators for role checking
def system_manager_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_system_manager():
            flash('شما دسترسی به این بخش ندارید.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def approval_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_approval_admin():
            flash('شما دسترسی به این بخش ندارید.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def generate_tracking_code():
    """Generate a unique tracking code"""
    while True:
        code = secrets.token_hex(5).upper()
        if not ServiceRequest.query.filter_by(tracking_code=code).first():
            return code



# Routes
@app.route('/')
def index():
    """Public homepage showing available services"""
    services = Service.query.filter_by(is_active=True).all()
    return render_template('user/index.html', services=services)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for system managers and approval admins"""
    if current_user.is_authenticated:
        if current_user.is_system_manager():
            return redirect(url_for('admin_dashboard'))
        elif current_user.is_approval_admin():
            return redirect(url_for('approver_dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if not next_page:
                if user.is_system_manager():
                    next_page = url_for('admin_dashboard')
                else:
                    next_page = url_for('approver_dashboard')
            return redirect(next_page)
        flash('نام کاربری یا رمز عبور اشتباه است.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('با موفقیت خارج شدید.', 'success')
    return redirect(url_for('index'))

# System Manager Routes
@app.route('/admin')
@login_required
@system_manager_required
def admin_dashboard():
    """System manager dashboard"""
    services = Service.query.all()
    admins = User.query.filter_by(role='approval_admin').all()
    
    # Add template statistics for each service
    services_with_stats = []
    for service in services:
        services_with_stats.append({
            'service': service,
            'stats': service.get_stats(),
            'template_stats': service.get_template_stats()
        })
    
    return render_template('admin/dashboard.html', 
                         services=services, 
                         services_with_stats=services_with_stats,
                         admins=admins)

@app.route('/admin/create-admin', methods=['GET', 'POST'])
@login_required
@system_manager_required
def create_admin():
    """Create new approval admin"""
    form = CreateAdminForm()
    if form.validate_on_submit():
        admin = User(
            username=form.username.data,
            email=form.email.data,
            role='approval_admin'
        )
        admin.set_password(form.password.data)
        db.session.add(admin)
        db.session.commit()
        flash(f'مدیر تایید "{admin.username}" با موفقیت ایجاد شد.', 'success')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_admin.html', form=form)

@app.route('/admin/services/create', methods=['GET', 'POST'])
@login_required
@system_manager_required
def create_service():
    """Create new service"""
    form = ServiceForm()
    if form.validate_on_submit():
        # Verify Google Doc access
        if google_docs_service:
            try:
                if not google_docs_service.verify_document_access(form.google_doc_id.data):
                    flash('خطا: دسترسی به Google Doc امکان‌پذیر نیست. لطفاً شناسه را بررسی کنید.', 'danger')
                    return render_template('admin/create_service.html', form=form)
            except Exception as e:
                flash(f'خطا در دسترسی به Google Doc: {str(e)}', 'danger')
                return render_template('admin/create_service.html', form=form)
        else:
            flash('خطا: سرویس Google Docs پیکربندی نشده است.', 'danger')
            return render_template('admin/create_service.html', form=form)
        
        service = Service(
            name=form.name.data,
            description=form.description.data,
            google_doc_id=form.google_doc_id.data,
            created_by=current_user.id
        )
        
        db.session.add(service)
        db.session.commit()
        flash('خدمت جدید با موفقیت ایجاد شد.', 'success')
        return redirect(url_for('edit_service_fields', service_id=service.id))
    return render_template('admin/create_service.html', form=form)

@app.route('/admin/services/preview-google-doc/<doc_id>')
@login_required
@system_manager_required
def preview_google_doc(doc_id):
    """Preview Google Doc content via AJAX"""
    if not google_docs_service:
        return jsonify({'error': 'سرویس Google Docs پیکربندی نشده است'}), 500
    
    try:
        # Extract content and placeholders
        doc_info = google_docs_service.extract_text_and_placeholders(doc_id)
        
        return jsonify({
            'success': True,
            'title': doc_info['title'],
            'paragraphs': doc_info['text_content'][:10],  # First 10 paragraphs
            'placeholders': doc_info['placeholders'],
            'total_paragraphs': len(doc_info['text_content']),
            'doc_url': google_docs_service.get_document_url(doc_id)
        })
        
    except Exception as e:
        app.logger.error(f"Error previewing Google Doc: {str(e)}")
        return jsonify({'error': f'خطا در خواندن سند: {str(e)}'}), 500



@app.route('/admin/services/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
@system_manager_required
def edit_service(service_id):
    """Edit service details"""
    service = Service.query.get_or_404(service_id)
    form = ServiceForm(obj=service)
    
    if form.validate_on_submit():
        # Verify Google Doc access if changed
        if form.google_doc_id.data != service.google_doc_id:
            if google_docs_service:
                try:
                    if not google_docs_service.verify_document_access(form.google_doc_id.data):
                        flash('خطا: دسترسی به Google Doc امکان‌پذیر نیست. لطفاً شناسه را بررسی کنید.', 'danger')
                        return render_template('admin/edit_service.html', form=form, service=service)
                except Exception as e:
                    flash(f'خطا در دسترسی به Google Doc: {str(e)}', 'danger')
                    return render_template('admin/edit_service.html', form=form, service=service)
            else:
                flash('خطا: سرویس Google Docs پیکربندی نشده است.', 'danger')
                return render_template('admin/edit_service.html', form=form, service=service)
        
        service.name = form.name.data
        service.description = form.description.data
        service.google_doc_id = form.google_doc_id.data
        
        db.session.commit()
        flash('خدمت با موفقیت به‌روزرسانی شد.', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_service.html', form=form, service=service)

@app.route('/admin/services/<int:service_id>/fields', methods=['GET', 'POST'])
@login_required
@system_manager_required
def edit_service_fields(service_id):
    """Edit service form fields"""
    service = Service.query.get_or_404(service_id)
    form = FormFieldForm()
    
    if form.validate_on_submit():
        field = FormField(
            service_id=service.id,
            field_name=form.field_name.data,
            field_label=form.field_label.data,
            field_type=form.field_type.data,
            is_required=form.is_required.data,
            placeholder=form.placeholder.data,
            document_placeholder=form.document_placeholder.data,
            field_order=service.form_fields.count()
        )
        
        if form.field_type.data == 'select' and form.options.data:
            options = [opt.strip() for opt in form.options.data.split('\n') if opt.strip()]
            field.options = json.dumps(options, ensure_ascii=False)
        
        db.session.add(field)
        db.session.commit()
        flash('فیلد جدید اضافه شد.', 'success')
        return redirect(url_for('edit_service_fields', service_id=service.id))
    
    fields = service.form_fields.order_by(FormField.field_order).all()
    return render_template('admin/edit_fields.html', service=service, form=form, fields=fields)

@app.route('/admin/services/<int:service_id>/stats')
@login_required
@system_manager_required
def service_stats(service_id):
    """View detailed statistics for a service"""
    service = Service.query.get_or_404(service_id)
    stats = service.get_stats()
    template_stats = service.get_template_stats()
    
    # Get all requests for this service
    page = request.args.get('page', 1, type=int)
    requests = ServiceRequest.query.filter_by(service_id=service_id).order_by(
        ServiceRequest.created_at.desc()
    ).paginate(page=page, per_page=app.config['REQUESTS_PER_PAGE'])
    
    return render_template('admin/service_stats.html', 
                         service=service, 
                         stats=stats, 
                         template_stats=template_stats,
                         requests=requests)

@app.route('/admin/service/<int:service_id>/templates')
@login_required
@system_manager_required
def manage_templates(service_id):
    """Manage template files for a service"""
    service = Service.query.get_or_404(service_id)
    templates = TemplateFile.query.filter_by(service_id=service_id).order_by(
        TemplateFile.created_at.desc()
    ).all()
    
    template_stats = service.get_template_stats()
    
    return render_template('admin/manage_templates.html',
                         service=service,
                         templates=templates,
                         template_stats=template_stats)

@app.route('/admin/service/<int:service_id>/templates/add', methods=['GET', 'POST'])
@login_required
@system_manager_required
def add_template(service_id):
    """Add a new template file to a service"""
    from forms import TemplateUploadForm
    
    service = Service.query.get_or_404(service_id)
    form = TemplateUploadForm()
    
    if form.validate_on_submit():
        try:
            # Get file ID from form (either direct ID or Drive URL)
            file_id = form.file_id.data
            
            # Extract file ID from Drive URL if needed
            if 'drive.google.com' in file_id:
                import re
                match = re.search(r'/d/([a-zA-Z0-9-_]+)', file_id)
                if match:
                    file_id = match.group(1)
            
            # Create new template file record
            template_file = TemplateFile(
                service_id=service_id,
                file_id=file_id,
                file_name=form.file_name.data
            )
            
            db.session.add(template_file)
            db.session.commit()
            
            flash('Template file added successfully!', 'success')
            return redirect(url_for('manage_templates', service_id=service_id))
            
        except Exception as e:
            flash(f'Error adding template: {str(e)}', 'danger')
    
    return render_template('admin/add_template.html',
                         service=service,
                         form=form)

@app.route('/admin/template/<int:template_id>/delete', methods=['POST'])
@login_required
@system_manager_required
def delete_template(template_id):
    """Delete a template file"""
    template = TemplateFile.query.get_or_404(template_id)
    service_id = template.service_id
    
    # Don't delete if template is already used
    if template.used:
        flash('Cannot delete a template that has been used!', 'danger')
    else:
        db.session.delete(template)
        db.session.commit()
        flash('Template deleted successfully!', 'success')
    
    return redirect(url_for('manage_templates', service_id=service_id))


# Approval Admin Routes
@app.route('/approver')
@login_required
@approval_admin_required
def approver_dashboard():
    """Approval admin dashboard"""
    page = request.args.get('page', 1, type=int)
    requests = ServiceRequest.query.filter_by(status='pending').order_by(
        ServiceRequest.created_at.desc()
    ).paginate(page=page, per_page=app.config['REQUESTS_PER_PAGE'])
    
    # Check template availability for each request
    requests_with_template_info = []
    for req in requests.items:
        requests_with_template_info.append({
            'request': req,
            'has_templates': req.service.has_available_templates(),
            'template_stats': req.service.get_template_stats()
        })
    
    return render_template('approver/dashboard.html', 
                         requests=requests,
                         requests_with_template_info=requests_with_template_info)

@app.route('/approver/request/<int:request_id>', methods=['GET', 'POST'])
@login_required
@approval_admin_required
def review_request(request_id):
    """Review and approve/reject a request"""
    service_request = ServiceRequest.query.get_or_404(request_id)
    form = ApprovalForm()
    
    # Check if service has available templates
    has_templates = service_request.service.has_available_templates()
    
    if form.validate_on_submit():
        if form.action.data == 'approve':
            # Check for available templates before approving
            if not has_templates:
                flash('No available template files for this service. Please contact the system administrator to add more templates.', 'danger')
                return redirect(url_for('review_request', request_id=request_id))
            
            # Get an available template
            template_file = service_request.service.get_available_template()
            if not template_file:
                flash('No available template files for this service. Please contact the system administrator to add more templates.', 'danger')
                return redirect(url_for('review_request', request_id=request_id))
            
            # Mark template as used and assign to request
            template_file.used = True
            template_file.used_at = datetime.utcnow()
            service_request.template_file_id = template_file.id
            
            service_request.status = 'approved'
            service_request.approval_note = form.note.data
            service_request.approved_by = current_user.id
            
            # Generate PDF using the template
            try:
                pdf_filename = generate_pdf_from_request(service_request)
                service_request.pdf_filename = pdf_filename
                flash('درخواست تایید شد و PDF تولید شد.', 'success')
            except Exception as e:
                # Rollback template usage if PDF generation fails
                template_file.used = False
                template_file.used_at = None
                service_request.template_file_id = None
                flash(f'خطا در تولید PDF: {str(e)}', 'danger')
                return redirect(url_for('review_request', request_id=request_id))
        else:
            # Rejection
            service_request.status = 'rejected'
            service_request.approval_note = form.note.data
            service_request.approved_by = current_user.id
            flash('درخواست رد شد.', 'info')
        
        db.session.commit()
        return redirect(url_for('approver_dashboard'))
    
    form_data = service_request.get_form_data()
    return render_template('approver/review_request.html', 
                         request=service_request, 
                         form=form,
                         form_data=form_data,
                         has_templates=has_templates)

# Public User Routes
@app.route('/service/<int:service_id>/request', methods=['GET', 'POST'])
def request_service(service_id):
    """Submit a service request"""
    service = Service.query.get_or_404(service_id)
    if not service.is_active:
        flash('این خدمت در حال حاضر غیرفعال است.', 'warning')
        return redirect(url_for('index'))
    
    # Create dynamic form
    class DynamicForm(ServiceRequestForm):
        pass
    
    # Add fields dynamically
    for field in service.form_fields.order_by(FormField.field_order):
        field_class = None
        validators = []
        
        if field.is_required:
            validators.append(DataRequired(message='این فیلد اجباری است'))
        
        if field.field_type == 'text':
            field_class = StringField
        elif field.field_type == 'number':
            field_class = IntegerField
        elif field.field_type == 'email':
            field_class = StringField
            validators.append(Email(message='ایمیل معتبر وارد کنید'))
        elif field.field_type == 'textarea':
            field_class = TextAreaField
        elif field.field_type == 'select':
            choices = [(opt, opt) for opt in field.get_options()]
            setattr(DynamicForm, field.field_name, 
                   SelectField(field.field_label, choices=choices, validators=validators))
            continue
        else:
            field_class = StringField
        
        if field_class:
            setattr(DynamicForm, field.field_name, 
                   field_class(field.field_label, validators=validators, 
                             render_kw={'placeholder': field.placeholder}))
    
    form = DynamicForm()
    
    if form.validate_on_submit():
        # Collect form data
        form_data = {}
        for field in service.form_fields:
            if hasattr(form, field.field_name):
                form_data[field.field_name] = getattr(form, field.field_name).data
        
        # Create request
        service_request = ServiceRequest(
            service_id=service.id,
            tracking_code=generate_tracking_code()
        )
        service_request.set_form_data(form_data)
        
        db.session.add(service_request)
        db.session.commit()
        
        flash(f'درخواست شما با کد پیگیری {service_request.tracking_code} ثبت شد.', 'success')
        return redirect(url_for('track_request', tracking_code=service_request.tracking_code))
    
    return render_template('user/request_service.html', service=service, form=form)

@app.route('/track', methods=['GET', 'POST'])
def track_request():
    """Track request status"""
    form = TrackingForm()
    tracking_code = request.args.get('tracking_code')
    
    if tracking_code:
        form.tracking_code.data = tracking_code
    
    if form.validate_on_submit() or tracking_code:
        code = form.tracking_code.data if form.validate_on_submit() else tracking_code
        service_request = ServiceRequest.query.filter_by(tracking_code=code).first()
        
        if service_request:
            return render_template('user/request_status.html', 
                                 request=service_request, 
                                 form_data=service_request.get_form_data())
        else:
            flash('کد پیگیری یافت نشد.', 'warning')
    
    return render_template('user/track.html', form=form)

@app.route('/download/<tracking_code>')
def download_pdf(tracking_code):
    """Download approved request PDF"""
    service_request = ServiceRequest.query.filter_by(tracking_code=tracking_code).first_or_404()
    
    if service_request.status != 'approved' or not service_request.pdf_filename:
        flash('فایل PDF موجود نیست.', 'warning')
        return redirect(url_for('track_request', tracking_code=tracking_code))
    
    pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], service_request.pdf_filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, 
                        download_name=f'request_{tracking_code}.pdf')
    else:
        flash('فایل PDF یافت نشد.', 'danger')
        return redirect(url_for('track_request', tracking_code=tracking_code))

# PDF Generation
def generate_pdf_from_request(service_request):
    """Generate PDF from approved request using Google Docs"""
    service = service_request.service
    form_data = service_request.get_form_data()
    
    if not google_docs_service:
        raise Exception("Google Docs service not configured")
    
    # Use the assigned template file if available, otherwise fall back to service template
    if service_request.template_file and service_request.template_file.file_id:
        template_id = service_request.template_file.file_id
    elif service.google_doc_id:
        template_id = service.google_doc_id
    else:
        raise Exception("No template file assigned to this request")
    
    try:
        # Create a copy of the template document
        copy_title = f"Request_{service_request.tracking_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_doc_id = google_docs_service.create_document_copy(template_id, copy_title)
        
        # Prepare replacements mapping
        replacements = {}
        for field in service.form_fields:
            if field.document_placeholder:
                value = str(form_data.get(field.field_name, ''))
                replacements[field.document_placeholder] = value
        
        # Replace placeholders in the copy
        if replacements:
            google_docs_service.replace_placeholders_in_doc(temp_doc_id, replacements)
        
        # Export as PDF
        pdf_data = google_docs_service.export_as_pdf(temp_doc_id)
        
        # Save PDF locally
        pdf_filename = f"output_{service_request.tracking_code}.pdf"
        pdf_path = os.path.join(app.config['PDF_OUTPUT_FOLDER'], pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(pdf_data)
        
        # Clean up - delete the temporary document
        google_docs_service.delete_document(temp_doc_id)
        
        return pdf_filename
        
    except Exception as e:
        app.logger.error(f"Error generating PDF from Google Docs: {str(e)}")
        # Try to clean up temp doc if it exists
        if 'temp_doc_id' in locals():
            try:
                google_docs_service.delete_document(temp_doc_id)
            except:
                pass
        raise e
    


# Initialize database
@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    
    # Create default system manager if not exists
    if not User.query.filter_by(role='system_manager').first():
        admin = User(
            username='admin',
            email='admin@example.com',
            role='system_manager'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Default system manager created: username='admin', password='admin123'")
    
    print("Database initialized!")



# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default system manager if not exists
        if not User.query.filter_by(role='system_manager').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                role='system_manager'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default system manager created: username='admin', password='admin123'")
    
    app.run(debug=True)