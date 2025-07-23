# Google Docs Integration Setup Guide

## Overview
This Flask application now uses Google Docs API instead of local Word file uploads. This allows for cloud-based template management and better collaboration.

## Prerequisites

1. **Google Cloud Project**
   - Create a project at [Google Cloud Console](https://console.cloud.google.com/)
   - Enable the following APIs:
     - Google Docs API
     - Google Drive API

2. **Service Account**
   - Go to "IAM & Admin" > "Service Accounts"
   - Create a new service account
   - Download the JSON credentials file
   - Rename it to `credentials.json` and place it in the project root

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Credentials
1. Copy `credentials.json.example` to `credentials.json`
2. Replace with your actual service account credentials
3. Ensure the file is in the project directory

### 3. Google Docs Template Setup
1. Create a Google Doc template with placeholders like:
   - `{{NAME}}` - نام و نام خانوادگی
   - `{{PHONE}}` - شماره تماس
   - `{{ADDRESS}}` - آدرس
   - `{{DESCRIPTION}}` - توضیحات

2. Share the document with your service account email:
   - Find the email in `credentials.json` (client_email)
   - Share the doc with "Viewer" or "Editor" permissions

3. Copy the document ID from the URL:
   ```
   https://docs.google.com/document/d/[DOCUMENT_ID]/edit
   ```

### 4. Database Migration
If upgrading from the old version:
```sql
-- Add google_doc_id column
ALTER TABLE services ADD COLUMN google_doc_id VARCHAR(255);

-- Remove old columns (optional)
ALTER TABLE services DROP COLUMN template_filename;
```

## Usage

### For System Managers

1. **Creating a Service:**
   - Enter the service name and description
   - Paste the Google Doc ID (or full URL)
   - Click "پیش‌نمایش" to preview the document
   - The system will show found placeholders

2. **Editing a Service:**
   - Change the Google Doc ID to use a different template
   - Preview updates automatically on page load

### For End Users

1. Submit a service request as usual
2. When approved, the system will:
   - Create a copy of the Google Doc template
   - Replace placeholders with form data
   - Export as PDF with RTL support preserved
   - Delete the temporary copy

## Features

- ✅ **Cloud-based templates** - Edit templates directly in Google Docs
- ✅ **Real-time preview** - See document content and placeholders instantly
- ✅ **RTL Support** - Persian/Arabic text is preserved in PDF export
- ✅ **Automatic cleanup** - Temporary documents are deleted after PDF generation
- ✅ **No local storage** - Templates stay in Google Drive

## Troubleshooting

### "Google Docs service not configured"
- Ensure `credentials.json` exists and is valid
- Check file permissions

### "Document not found"
- Verify the document ID is correct
- Ensure the document is shared with the service account

### "Error accessing document"
- Check API quotas in Google Cloud Console
- Verify the service account has proper permissions

## Security Notes

1. **Never commit `credentials.json` to version control**
2. Add it to `.gitignore`
3. Use environment-specific credentials for production
4. Limit service account permissions to minimum required

## API Quotas

Google Docs API has the following limits:
- 300 requests per minute per user
- 60 requests per minute per project

For high-volume usage, consider:
- Implementing caching
- Request batching
- Rate limiting