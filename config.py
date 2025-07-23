import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'service_requests.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Output folder
    PDF_OUTPUT_FOLDER = os.path.join(basedir, 'pdf_outputs')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'docx', 'ttf', 'otf'}
    
    # Pagination
    REQUESTS_PER_PAGE = 20