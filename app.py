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
from models import db, User, Service, FormField, ServiceRequest
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

# Initialize PDF queue processor with app and db
from pdf_queue_processor import init_queue_processor
init_queue_processor(app, db)

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
    return render_template('admin/dashboard.html', services=services, admins=admins)

@app.route('/admin/create-admin', methods=['GET', 'POST'])
@login_required
@system_manager_required
def create_admin():
    """Create new approval admin"""
    form = CreateAdminForm()
    if form.validate_on_submit():
        try:
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
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating admin: {str(e)}')
            flash('خطا در ایجاد مدیر. لطفاً دوباره تلاش کنید.', 'danger')
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
        
        try:
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
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating service: {str(e)}')
            flash('خطا در ایجاد خدمت. لطفاً دوباره تلاش کنید.', 'danger')
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
        
        try:
            service.name = form.name.data
            service.description = form.description.data
            service.google_doc_id = form.google_doc_id.data
            
            db.session.commit()
            flash('خدمت با موفقیت به‌روزرسانی شد.', 'success')
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error updating service: {str(e)}')
            flash('خطا در به‌روزرسانی خدمت. لطفاً دوباره تلاش کنید.', 'danger')
    
    return render_template('admin/edit_service.html', form=form, service=service)

@app.route('/admin/services/<int:service_id>/fields', methods=['GET', 'POST'])
@login_required
@system_manager_required
def edit_service_fields(service_id):
    """Edit service form fields"""
    service = Service.query.get_or_404(service_id)
    form = FormFieldForm()
    
    # Auto-approval settings form
    from forms import AutoApprovalSettingsForm
    auto_approval_form = AutoApprovalSettingsForm()
    
    # Populate field choices for auto-approval
    field_choices = [('', '-- انتخاب کنید --')]
    for field in service.form_fields:
        field_choices.append((field.field_name, field.field_label))
    auto_approval_form.auto_approve_field_name.choices = field_choices
    
    # Handle auto-approval form submission
    if request.method == 'POST' and 'save_auto_approval' in request.form:
        if auto_approval_form.validate():
            try:
                service.auto_approve_enabled = auto_approval_form.auto_approve_enabled.data
                service.auto_approve_sheet_id = auto_approval_form.auto_approve_sheet_id.data or "1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ"
                service.auto_approve_sheet_column = auto_approval_form.auto_approve_sheet_column.data or "A"
                service.auto_approve_field_name = auto_approval_form.auto_approve_field_name.data
                
                db.session.commit()
                flash('تنظیمات تأیید خودکار ذخیره شد.', 'success')
                return redirect(url_for('edit_service_fields', service_id=service.id))
            except Exception as e:
                db.session.rollback()
                app.logger.error(f'Error saving auto-approval settings: {str(e)}')
                flash('خطا در ذخیره تنظیمات تأیید خودکار. لطفاً دوباره تلاش کنید.', 'danger')
    
    # Handle field form submission
    if form.validate_on_submit() and 'save_auto_approval' not in request.form:
        try:
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
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error adding field: {str(e)}')
            flash('خطا در افزودن فیلد. لطفاً دوباره تلاش کنید.', 'danger')
    
    # Pre-populate auto-approval form with current values
    if request.method == 'GET':
        auto_approval_form.auto_approve_enabled.data = service.auto_approve_enabled
        auto_approval_form.auto_approve_sheet_id.data = service.auto_approve_sheet_id
        auto_approval_form.auto_approve_sheet_column.data = service.auto_approve_sheet_column
        auto_approval_form.auto_approve_field_name.data = service.auto_approve_field_name
    
    fields = service.form_fields.order_by(FormField.field_order).all()
    return render_template('admin/edit_fields.html', 
                         service=service, 
                         form=form, 
                         fields=fields,
                         auto_approval_form=auto_approval_form)

@app.route('/admin/services/<int:service_id>/stats')
@login_required
@system_manager_required
def service_stats(service_id):
    """View service statistics"""
    service = Service.query.get_or_404(service_id)
    stats = service.get_stats()
    recent_requests = service.requests.order_by(ServiceRequest.created_at.desc()).limit(10).all()
    return render_template('admin/service_stats.html', service=service, stats=stats, recent_requests=recent_requests)



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
    return render_template('approver/dashboard.html', requests=requests)

@app.route('/approver/request/<int:request_id>', methods=['GET', 'POST'])
@login_required
@approval_admin_required
def review_request(request_id):
    """Review and approve/reject a request"""
    service_request = ServiceRequest.query.get_or_404(request_id)
    form = ApprovalForm()
    
    if form.validate_on_submit():
        try:
            service_request.status = form.action.data + 'd'  # approved or rejected
            service_request.approval_note = form.note.data
            service_request.approved_by = current_user.id
            
            if form.action.data == 'approve':
                # Generate PDF using queue system
                try:
                    from pdf_queue_processor import add_pdf_task, wait_for_task, ProcessingStatus
                    
                    # Add PDF generation to queue
                    task_id = add_pdf_task(service_request)
                    app.logger.info(f"Added PDF task {task_id} to queue for manual approval")
                    
                    # Wait for task completion (with timeout)
                    task = wait_for_task(task_id, timeout=30)
                    
                    if task:
                        if task.status == ProcessingStatus.COMPLETED:
                            service_request.pdf_filename = task.result
                            db.session.commit()
                            flash('درخواست تایید شد و PDF تولید شد.', 'success')
                        else:
                            db.session.commit()
                            flash(f'درخواست تایید شد اما تولید PDF با خطا مواجه شد: {task.error}', 'warning')
                    else:
                        db.session.commit()
                        flash('درخواست تایید شد. PDF در صف تولید قرار گرفت.', 'info')
                        
                except Exception as e:
                    db.session.commit()
                    app.logger.error(f'Error adding PDF to queue: {str(e)}')
                    flash(f'خطا در تولید PDF: {str(e)}', 'danger')
            else:
                db.session.commit()
                flash('درخواست رد شد.', 'info')
        
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error processing request approval/rejection: {str(e)}')
            flash('خطا در پردازش درخواست. لطفاً دوباره تلاش کنید.', 'danger')
        return redirect(url_for('approver_dashboard'))
    
    form_data = service_request.get_form_data()
    return render_template('approver/review_request.html', 
                         request=service_request, 
                         form=form, 
                         form_data=form_data)

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
        try:
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
        except Exception as e:
            db.session.rollback()
            app.logger.error(f'Error creating service request: {str(e)}')
            flash('خطا در ثبت درخواست. لطفاً دوباره تلاش کنید.', 'danger')
            return redirect(url_for('request_service', service_id=service.id))
        
        # Check for auto-approval
        if service.auto_approve_enabled and service.auto_approve_field_name:
            try:
                from google_sheets_checker import check_employee_in_sheet
                from pdf_queue_processor import add_pdf_task, wait_for_task, ProcessingStatus
                
                # Get the value to check
                check_value = form_data.get(service.auto_approve_field_name, '')
                
                if check_value:
                    # Check if value exists in Google Sheet
                    sheet_id = service.auto_approve_sheet_id or "1qqmTsIfLwGVPVj7kHnvb3AvAdFcMw37dh0RCoBxYViQ"
                    column = service.auto_approve_sheet_column or "A"
                    
                    if check_employee_in_sheet(check_value, sheet_id, column):
                        app.logger.info(f"Auto-approving request {service_request.tracking_code} for {check_value}")
                        
                        # Auto-approve the request
                        try:
                            service_request.status = 'approved'
                            service_request.approval_note = 'تأیید خودکار بر اساس لیست پرسنل'
                            db.session.commit()
                        except Exception as e:
                            db.session.rollback()
                            app.logger.error(f"Error auto-approving request: {str(e)}")
                            flash('خطا در تأیید خودکار. درخواست شما ثبت شد و منتظر تأیید دستی است.', 'warning')
                            return redirect(url_for('track_request', tracking_code=service_request.tracking_code))
                        
                        # Add PDF generation to queue
                        def on_pdf_complete(task):
                            """Callback when PDF is generated"""
                            with app.app_context():
                                try:
                                    if task.status == ProcessingStatus.COMPLETED:
                                        # Re-fetch the service request using the ID
                                        sr = db.session.get(ServiceRequest, service_request.id)
                                        if sr:
                                            sr.pdf_filename = task.result
                                            db.session.commit()
                                            app.logger.info(f"PDF generated for auto-approved request: {task.result}")
                                        else:
                                            app.logger.error(f"Service request {service_request.id} not found in callback")
                                    else:
                                        app.logger.error(f"PDF generation failed for auto-approved request: {task.error}")
                                except Exception as e:
                                    db.session.rollback()
                                    app.logger.error(f"Error in PDF callback: {str(e)}")
                        
                        task_id = add_pdf_task(service_request, callback=on_pdf_complete)
                        app.logger.info(f"Added PDF task {task_id} to queue")
                        
                        flash(f'درخواست شما با کد پیگیری {service_request.tracking_code} به صورت خودکار تأیید شد. PDF در حال آماده‌سازی است.', 'success')
                        return redirect(url_for('track_request', tracking_code=service_request.tracking_code))
                    else:
                        app.logger.info(f"Value '{check_value}' not found in sheet, proceeding with manual approval")
                        
            except Exception as e:
                app.logger.error(f"Error in auto-approval check: {str(e)}")
                # Continue with normal flow if auto-approval fails
        
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
    
    if not service.google_doc_id:
        raise Exception("No Google Doc template configured for this service")
    
    try:
        # Create a copy of the template document
        copy_title = f"Request_{service_request.tracking_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        temp_doc_id = google_docs_service.create_document_copy(service.google_doc_id, copy_title)
        
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
        try:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='system_manager'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default system manager created: username='admin', password='admin123'")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating default admin: {str(e)}")
    
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
            try:
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    role='system_manager'
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("Default system manager created: username='admin', password='admin123'")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating default admin: {str(e)}")
    
    app.run(debug=True)