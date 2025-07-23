# Template Files Feature

## Overview

This feature enhances the Flask application to better handle service request approvals by implementing a template file management system. Each service can now have multiple pre-uploaded Google Docs template files, and each template can only be used once.

## Key Features

### 1. Template File Management
- Each service can have multiple template files stored in Google Drive
- Templates are tracked in the database with the `TemplateFile` model
- Each template has a `used` flag to track whether it has been assigned to a request

### 2. Approval Process Enhancement
- Before approving a request, the system checks for available (unused) templates
- If no templates are available:
  - The approval is blocked
  - A clear error message is displayed
  - Only rejection is allowed

### 3. Admin Dashboard Updates
- Shows template statistics for each service (available/total)
- Visual indicators for services with low or no templates
- Warning badges for critical template shortages

### 4. Approver Dashboard Updates
- Shows template availability for each pending request
- Disables approve button for requests without available templates
- Visual warnings (color coding) for requests that cannot be approved

### 5. Template Management Interface
- Dedicated page for managing templates for each service
- Add new templates by providing Google Drive file ID or URL
- View all templates with their status (used/available)
- Delete unused templates
- Statistics showing total, used, and available templates

## Database Changes

### New Model: TemplateFile
```python
class TemplateFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)
    file_id = db.Column(db.String(255), nullable=False)  # Google Drive file ID
    file_name = db.Column(db.String(255))  # Original file name
    used = db.Column(db.Boolean, default=False)  # Track if template has been used
    used_at = db.Column(db.DateTime)  # When it was used
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Updated Model: ServiceRequest
- Added `template_file_id` column to link each approved request to its template

## Usage Instructions

### For System Administrators

1. **Adding Templates**:
   - Navigate to Admin Dashboard
   - Click "قالب‌ها" (Templates) button for a service
   - Click "افزودن قالب جدید" (Add New Template)
   - Enter template name and Google Drive file ID/URL
   - Submit to add the template

2. **Managing Templates**:
   - View all templates for a service
   - See which templates are used or available
   - Delete unused templates if needed
   - Monitor template availability

3. **Best Practices**:
   - Keep at least 5-10 unused templates per service
   - Monitor services with low template counts
   - Add templates before they run out completely

### For Approval Administrators

1. **Reviewing Requests**:
   - Check template availability indicator in the dashboard
   - Requests without templates are highlighted in yellow
   - Cannot approve requests without available templates

2. **Handling No-Template Situations**:
   - Only rejection is possible
   - Contact system administrator to add more templates
   - Clear error messages guide the process

## Migration

Run the migration script to update existing databases:

```bash
python migrate_template_files.py
```

This will:
- Create the `template_files` table
- Add `template_file_id` column to `service_requests`
- Create default templates from existing service Google Doc IDs

## Technical Implementation

### Template Assignment Flow
1. User submits request → Status: Pending
2. Admin tries to approve → System checks for available templates
3. If template available → Assign template, mark as used, generate PDF
4. If no template → Show error, block approval

### Rollback Mechanism
- If PDF generation fails after template assignment
- Template is marked as unused again
- Request remains pending

## Future Enhancements

1. **Bulk Template Upload**: Allow uploading multiple templates at once
2. **Template Preview**: Preview templates before adding
3. **Usage History**: Detailed log of which template was used for which request
4. **Auto-notification**: Alert admins when templates are running low
5. **Template Categories**: Organize templates by type or purpose