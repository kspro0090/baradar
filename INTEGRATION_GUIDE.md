# راهنمای یکپارچه‌سازی سیستم PDF بدون کپی

## خلاصه تغییرات

سیستم جدید PDF را بدون کپی کردن فایل Google Docs تولید می‌کند و از روش‌های زیر استفاده می‌کند:

1. **روش اصلی**: تغییر موقت Google Docs و بازگردانی آن
2. **روش جایگزین**: استفاده از ReportLab با فونت‌های فارسی

## فایل‌های جدید

### 1. `pdf_generator_no_copy.py`
- کلاس `NoCopyPDFGenerator`: مدیریت Google Docs بدون کپی
- تابع `generate_pdf_from_request_no_copy`: تولید PDF از Google Docs
- تابع `generate_pdf_fallback`: تولید PDF با ReportLab

### 2. `pdf_generator.py`
- کلاس `PersianPDFGenerator`: تولید PDF با پشتیبانی فونت فارسی
- مدیریت فونت‌های Vazirmatn
- پردازش متن RTL

### 3. `document_processor.py`
- رابط‌های سازگار با سیستم موجود
- مدیریت template های DOCX

## تغییرات در `app.py`

در تابع `review_request` (خط 290-320):

```python
if form.action.data == 'approve':
    # Generate PDF using new method without copying
    try:
        # First try the no-copy method
        from pdf_generator_no_copy import generate_pdf_from_request_no_copy, generate_pdf_fallback
        
        pdf_filename = None
        
        # Try Google Docs API without copy
        if google_docs_service:
            try:
                pdf_filename = generate_pdf_from_request_no_copy(service_request)
                if pdf_filename:
                    app.logger.info(f"PDF generated using no-copy method: {pdf_filename}")
            except Exception as e:
                app.logger.warning(f"No-copy method failed: {str(e)}")
        
        # If no-copy method failed, try fallback with ReportLab
        if not pdf_filename:
            app.logger.info("Trying fallback PDF generation with ReportLab")
            pdf_filename = generate_pdf_fallback(service_request)
        
        # If all else fails, use the old method (last resort)
        if not pdf_filename:
            app.logger.warning("Using old copy method as last resort")
            pdf_filename = generate_pdf_from_request(service_request)
```

## نحوه عملکرد

### روش No-Copy (Google Docs)

1. **دریافت محتوای فعلی**: سند Google Docs خوانده می‌شود
2. **جایگزینی placeholder ها**: مقادیر واقعی جایگزین می‌شوند
3. **تولید PDF**: سند به PDF تبدیل می‌شود
4. **بازگردانی**: placeholder ها دوباره بازگردانده می‌شوند

```python
# مثال جایگزینی‌ها
replacements = {
    '{{employee_name}}': 'علی محمدی',
    '{{department}}': 'فناوری اطلاعات'
}

# بازگردانی
reverse_replacements = {
    'علی محمدی': '{{employee_name}}',
    'فناوری اطلاعات': '{{department}}'
}
```

### روش Fallback (ReportLab)

اگر Google Docs در دسترس نباشد:
- از template های DOCX استفاده می‌کند
- یا PDF ساده با محتوای فرم تولید می‌کند

## پیکربندی فونت‌ها

فونت‌های فارسی در پوشه `fonts/`:
- `Vazirmatn-Regular.ttf`
- `Vazirmatn-Bold.ttf`
- `Vazirmatn-Light.ttf`
- `Vazirmatn-Medium.ttf`

## نکات مهم

### 1. عدم استفاده از files().copy()
سیستم جدید هرگز کپی از فایل Google Docs نمی‌سازد، بنابراین:
- ✅ مشکل پر شدن حافظه Google Drive حل شده
- ✅ نیازی به حذف فایل‌های موقت نیست
- ✅ عملکرد سریع‌تر

### 2. پشتیبانی از فونت‌های فارسی
- فونت‌های `vazir`, `B Nazanin`, `IRANSans` به Vazirmatn نگاشت می‌شوند
- متن RTL به درستی پردازش می‌شود
- کاراکترهای فارسی به شکل متصل نمایش داده می‌شوند

### 3. مدیریت خطا
اگر تغییرات اعمال شده و خطایی رخ دهد:
- سیستم سعی می‌کند سند را به حالت اولیه بازگرداند
- از روش‌های جایگزین استفاده می‌کند

## تست سیستم

برای تست:
```bash
python3 test_pdf_simple.py
```

## مثال استفاده مستقیم

```python
from pdf_generator_no_copy import generate_pdf_from_request_no_copy

# برای service_request موجود
pdf_filename = generate_pdf_from_request_no_copy(service_request)

# یا با ReportLab
from pdf_generator_no_copy import generate_pdf_fallback
pdf_filename = generate_pdf_fallback(service_request)
```

## وابستگی‌های جدید

در `requirements.txt`:
```
reportlab==4.0.7
python-docx==0.8.11
arabic-reshaper==3.0.0
python-bidi==0.4.2
```

## نتیجه

این سیستم:
- ✅ PDF را بدون کپی کردن Google Docs تولید می‌کند
- ✅ از فونت‌های فارسی پشتیبانی می‌کند
- ✅ تغییرات دائمی در Google Docs ایجاد نمی‌کند
- ✅ در صورت عدم دسترسی به Google Docs، از ReportLab استفاده می‌کند