# راهنمای سیستم تولید PDF از Google Docs

## خلاصه

این سیستم PDF را مستقیماً از Google Docs با استفاده از export API گوگل تولید می‌کند و تمام استایل‌ها، فونت‌ها، تصاویر و قالب‌بندی را حفظ می‌کند.

## ویژگی‌های کلیدی

✅ **حفظ کامل قالب**: تمام استایل‌ها، فونت‌ها، رنگ‌ها، تصاویر و لوگوها حفظ می‌شوند  
✅ **بدون کپی**: هیچ کپی از فایل Google Docs ایجاد نمی‌شود  
✅ **بازگردانی خودکار**: پس از تولید PDF، placeholder ها به حالت اولیه برمی‌گردند  
✅ **پشتیبانی از فارسی**: کاملاً با متن فارسی و RTL سازگار است  
✅ **مدیریت خطا**: در صورت بروز خطا، سند به حالت اولیه بازگردانده می‌شود

## نحوه عملکرد

1. **دریافت سند**: محتوای فعلی Google Docs دریافت می‌شود
2. **یافتن placeholder ها**: تمام placeholder های `{{name}}` شناسایی می‌شوند
3. **جایگزینی موقت**: مقادیر واقعی جایگزین placeholder ها می‌شوند
4. **Export PDF**: سند با Google Drive API به PDF تبدیل می‌شود
5. **بازگردانی**: placeholder ها به حالت اولیه بازگردانده می‌شوند

## نصب و راه‌اندازی

### 1. نصب وابستگی‌ها

```bash
pip install google-api-python-client google-auth
```

### 2. ایجاد Service Account

1. به [Google Cloud Console](https://console.cloud.google.com) بروید
2. یک پروژه جدید ایجاد کنید یا پروژه موجود را انتخاب کنید
3. APIs & Services > Enable APIs را انتخاب کنید
4. این API ها را فعال کنید:
   - Google Docs API
   - Google Drive API

### 3. ایجاد Credentials

1. به APIs & Services > Credentials بروید
2. Create Credentials > Service Account را انتخاب کنید
3. نام و توضیحات وارد کنید
4. کلید JSON را دانلود کنید و به نام `credentials.json` ذخیره کنید

### 4. اشتراک‌گذاری سند

ایمیل service account (که در فایل credentials.json است) را به عنوان Editor به سند Google Docs اضافه کنید.

## استفاده

### روش 1: استفاده مستقیم

```python
from google_docs_pdf_generator import generate_pdf_from_google_docs

# تعریف جایگزینی‌ها
replacements = {
    'employee_name': 'علی محمدی',
    'department': 'فناوری اطلاعات',
    'date': '1402/11/15',
    'leave_type': 'استحقاقی',
    'start_date': '1402/11/20',
    'end_date': '1402/11/25'
}

# تولید PDF
success = generate_pdf_from_google_docs(
    document_id='1ABC...xyz',  # شناسه Google Docs
    replacements=replacements,
    output_path='output.pdf'
)

if success:
    print("PDF تولید شد!")
```

### روش 2: با Service Request

```python
from google_docs_pdf_generator import generate_pdf_for_service_request

# service_request باید دارای:
# - service.google_doc_id
# - get_form_data()
# - tracking_code

pdf_filename = generate_pdf_for_service_request(service_request)
```

## قالب Google Docs

### نمونه قالب

```
فرم درخواست مرخصی

نام کارمند: {{employee_name}}
بخش: {{department}}
نوع مرخصی: {{leave_type}}

از تاریخ: {{start_date}}
تا تاریخ: {{end_date}}

دلیل درخواست:
{{reason}}

کد پیگیری: {{tracking_code}}
تاریخ ثبت: {{request_date}}

[امضا]
```

### نکات مهم برای قالب

- از `{{placeholder_name}}` برای متغیرها استفاده کنید
- می‌توانید از تصاویر، لوگو، جداول و هر قالب‌بندی استفاده کنید
- فونت‌ها و استایل‌ها دقیقاً حفظ می‌شوند
- برای متن فارسی از فونت‌های فارسی در Google Docs استفاده کنید

## یکپارچه‌سازی با app.py

در `app.py`، در تابع `review_request`:

```python
if form.action.data == 'approve':
    try:
        from google_docs_pdf_generator import generate_pdf_for_service_request
        
        pdf_filename = generate_pdf_for_service_request(service_request)
        
        if pdf_filename:
            service_request.pdf_filename = pdf_filename
            flash('درخواست تایید شد و PDF تولید شد.', 'success')
```

## تست سیستم

برای تست:

```bash
python test_google_docs_pdf.py
```

این اسکریپت:
- بررسی می‌کند که credentials.json موجود باشد
- امکان تست با document ID واقعی را فراهم می‌کند
- نمونه قالب برای Google Docs نشان می‌دهد

## رفع مشکلات

### خطا: "The caller does not have permission"
- مطمئن شوید سند با service account به اشتراک گذاشته شده
- دسترسی Editor داده باشید

### خطا: "Document not found"
- Document ID را بررسی کنید
- مطمئن شوید ID کامل و صحیح است

### Placeholder ها جایگزین نمی‌شوند
- دقت کنید placeholder ها دقیقاً مطابق با کلیدهای dictionary باشند
- می‌توانید با یا بدون `{{}}` استفاده کنید

### PDF خالی است
- بررسی کنید که سند محتوا داشته باشد
- زمان delay ها را افزایش دهید

## مزایا نسبت به روش‌های دیگر

1. **کیفیت بالا**: PDF دقیقاً مثل سند اصلی با تمام جزئیات
2. **بدون محدودیت فضا**: نیازی به کپی کردن فایل نیست
3. **سرعت بالا**: مستقیماً از Google export می‌کند
4. **امنیت**: تغییرات موقتی و بازگردانی خودکار

## نمونه کد کامل

```python
# مثال کامل برای تولید PDF از یک فرم درخواست

from google_docs_pdf_generator import GoogleDocsPDFGenerator
from datetime import datetime

# ایجاد generator
generator = GoogleDocsPDFGenerator('credentials.json')

# داده‌های فرم
form_data = {
    'employee_name': 'مریم حسینی',
    'employee_id': 'EMP-1234',
    'department': 'حسابداری',
    'manager_name': 'علی محمدی',
    'leave_type': 'استحقاقی',
    'start_date': '1402/12/01',
    'end_date': '1402/12/05',
    'days_count': '5',
    'reason': 'سفر خانوادگی',
    'tracking_code': f'REQ-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
    'request_date': datetime.now().strftime('%Y/%m/%d')
}

# تولید PDF
success = generator.generate_pdf_with_replacements(
    document_id='YOUR_DOCUMENT_ID',
    replacements=form_data,
    output_path='leave_request.pdf',
    delay_before_export=1.5,  # زمان انتظار قبل از export
    delay_before_restore=0.5  # زمان انتظار قبل از بازگردانی
)

if success:
    print("✅ PDF با موفقیت تولید شد!")
else:
    print("❌ خطا در تولید PDF")
```

## نتیجه

این سیستم راه‌حلی کامل برای تولید PDF از Google Docs با حفظ تمام قالب‌بندی و بدون ایجاد کپی اضافی است. مناسب برای سیستم‌هایی که نیاز به تولید اسناد رسمی با قالب دقیق دارند.