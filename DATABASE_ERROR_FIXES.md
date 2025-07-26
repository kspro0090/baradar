# رفع خطاهای Database در app.py

## خلاصه تغییرات

برای رفع خطاهای `sqlalchemy.exc.PendingRollbackError` و `Working outside of application context`، تغییرات زیر اعمال شد:

## 1. اضافه کردن Try/Except/Rollback به تمام db.session.commit() ها

### موارد اصلاح شده:

1. **create_admin** (خط 134)
   - محافظت از ایجاد admin جدید
   - rollback در صورت خطا

2. **create_service** (خط 172)
   - محافظت از ایجاد service جدید
   - پیام خطای مناسب به کاربر

3. **edit_service** (خط 236)
   - محافظت از به‌روزرسانی service
   - حفظ داده‌های فرم در صورت خطا

4. **edit_service_fields** (خط 273 و 300)
   - محافظت از ذخیره تنظیمات تأیید خودکار
   - محافظت از اضافه کردن فیلد جدید

5. **review_request** (خط 375-389)
   - محافظت کامل از فرآیند تأیید/رد درخواست
   - commit های جداگانه برای هر مرحله

6. **request_service** (خط 465)
   - محافظت از ایجاد درخواست جدید
   - redirect به فرم در صورت خطا

7. **auto-approval** (خط 493)
   - محافظت از تأیید خودکار
   - fallback به تأیید دستی در صورت خطا

8. **init_db** (خط 644 و 674)
   - محافظت از ایجاد admin پیش‌فرض
   - در هر دو نسخه CLI و __main__

## 2. رفع مشکل Application Context

### callback در auto-approval (خط 510)
```python
def on_pdf_complete(task):
    with app.app_context():  # اضافه شد
        try:
            # Re-fetch service request in new context
            sr = ServiceRequest.query.filter_by(...).first()
            # ...
        except Exception as e:
            db.session.rollback()
```

## 3. ایجاد db_utils.py

فایل جدید `db_utils.py` شامل:

1. **safe_commit()**: تابع برای commit امن با rollback خودکار
2. **with_db_transaction**: دکوریتور برای مدیریت خودکار transaction
3. **DatabaseContextManager**: context manager برای عملیات database

### نحوه استفاده:

```python
# روش 1: safe_commit
from db_utils import safe_commit
success, error = safe_commit(db.session, "Failed to create user")
if not success:
    flash(f'Error: {error}', 'danger')

# روش 2: decorator
from db_utils import with_db_transaction

@with_db_transaction
def create_user(username, email):
    user = User(username=username, email=email)
    db.session.add(user)
    # نیازی به commit نیست

# روش 3: context manager
from db_utils import DatabaseContextManager

with DatabaseContextManager(db.session) as dbcm:
    user = User(username='test')
    db.session.add(user)
    # commit/rollback خودکار
```

## نتیجه

با این تغییرات:
- ✅ تمام commit ها محافظت شده‌اند
- ✅ خطاهای database به کاربر اطلاع داده می‌شود
- ✅ هیچ PendingRollbackError رخ نمی‌دهد
- ✅ callback ها در application context اجرا می‌شوند
- ✅ اپلیکیشن از crash محافظت می‌شود

## توصیه‌ها

1. برای عملیات‌های جدید database، از `db_utils.py` استفاده کنید
2. همیشه commit ها را در try/except قرار دهید
3. برای callback ها و background task ها از `with app.app_context()` استفاده کنید
4. پیام‌های خطای مناسب به کاربر نمایش دهید