from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField, IntegerField, FieldList, FormField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
import re

# Custom validator for Persian text
class PersianTextValidator:
    def __init__(self, message=None):
        if not message:
            message = 'متن وارد شده معتبر نیست.'
        self.message = message
    
    def __call__(self, form, field):
        # Allow Persian, Arabic, English characters, numbers, and common punctuation
        if field.data:
            # This regex allows Persian/Arabic letters, English letters, numbers, spaces, and common punctuation
            pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFFa-zA-Z0-9\s\-_.,!?؟،؛:()]+$'
            if not re.match(pattern, field.data):
                raise ValidationError(self.message)

class LoginForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired()])
    password = PasswordField('رمز عبور', validators=[DataRequired()])
    remember_me = BooleanField('مرا به خاطر بسپار')

class CreateAdminForm(FlaskForm):
    username = StringField('نام کاربری', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('ایمیل', validators=[DataRequired(), Email()])
    password = PasswordField('رمز عبور', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('تکرار رمز عبور', validators=[DataRequired(), EqualTo('password')])
    
    def validate_username(self, username):
        from models import User
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('این نام کاربری قبلاً استفاده شده است.')
    
    def validate_email(self, email):
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('این ایمیل قبلاً ثبت شده است.')

class ServiceForm(FlaskForm):
    name = StringField('نام خدمت', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('توضیحات')
    google_doc_id = StringField('شناسه Google Docs', validators=[DataRequired()], 
                               render_kw={'placeholder': 'مثال: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms'})

class FormFieldForm(FlaskForm):
    field_label = StringField('برچسب فیلد', validators=[DataRequired()])
    field_name = StringField('نام فیلد (انگلیسی)', validators=[DataRequired()])
    field_type = SelectField('نوع فیلد', choices=[
        ('text', 'متن'),
        ('number', 'عدد'),
        ('email', 'ایمیل'),
        ('date', 'تاریخ'),
        ('textarea', 'متن چند خطی'),
        ('select', 'لیست کشویی')
    ])
    is_required = BooleanField('اجباری')
    placeholder = StringField('متن راهنما')
    document_placeholder = StringField('جایگزین در سند', validators=[DataRequired()])
    options = TextAreaField('گزینه‌ها (هر خط یک گزینه)')

class ServiceRequestForm(FlaskForm):
    # Dynamic form - fields will be added at runtime
    pass

class ApprovalForm(FlaskForm):
    action = SelectField('عملیات', choices=[('approve', 'تایید'), ('reject', 'رد')], validators=[DataRequired()])
    note = TextAreaField('یادداشت')



class TrackingForm(FlaskForm):
    tracking_code = StringField('کد پیگیری', validators=[DataRequired(), Length(max=20)])

class TemplateUploadForm(FlaskForm):
    file_id = StringField('شناسه فایل Google Drive یا لینک', 
                         validators=[DataRequired()],
                         render_kw={'placeholder': 'مثال: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms یا https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view'})
    file_name = StringField('نام فایل', 
                           validators=[DataRequired(), Length(max=255)],
                           render_kw={'placeholder': 'مثال: قالب درخواست مرخصی'})