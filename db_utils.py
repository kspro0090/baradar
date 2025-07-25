"""
Database utility functions for safe session management
"""

from functools import wraps
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

def safe_commit(session, error_message="Database error occurred"):
    """
    Safely commit database changes with automatic rollback on error
    
    Args:
        session: SQLAlchemy session object
        error_message: Custom error message for logging
        
    Returns:
        tuple: (success: bool, error: str or None)
    """
    try:
        session.commit()
        return True, None
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"{error_message}: {str(e)}")
        return False, str(e)
    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected error during commit: {str(e)}")
        return False, str(e)

def with_db_transaction(func):
    """
    Decorator to handle database transactions automatically
    Commits on success, rolls back on exception
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        from app import db
        try:
            result = func(*args, **kwargs)
            db.session.commit()
            return result
        except Exception as e:
            db.session.rollback()
            logger.error(f"Transaction failed in {func.__name__}: {str(e)}")
            raise
    return wrapper

def safe_db_operation(operation_name="database operation"):
    """
    Decorator for safe database operations with custom error handling
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from app import db, app
            try:
                result = func(*args, **kwargs)
                success, error = safe_commit(db.session, f"Error in {operation_name}")
                if not success:
                    # Log the error but don't necessarily raise
                    app.logger.error(f"{operation_name} failed: {error}")
                return result
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Exception in {operation_name}: {str(e)}")
                raise
        return wrapper
    return decorator

class DatabaseContextManager:
    """
    Context manager for database operations
    Automatically handles commit/rollback
    """
    def __init__(self, session, auto_commit=True):
        self.session = session
        self.auto_commit = auto_commit
        self.success = False
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self.auto_commit:
            try:
                self.session.commit()
                self.success = True
            except Exception as e:
                self.session.rollback()
                logger.error(f"Failed to commit: {str(e)}")
                raise
        else:
            self.session.rollback()
            if exc_type is not None:
                logger.error(f"Rolling back due to: {exc_val}")
        return False  # Don't suppress exceptions

# Usage examples:
"""
# Example 1: Using safe_commit
from db_utils import safe_commit

success, error = safe_commit(db.session, "Failed to create user")
if not success:
    flash(f'Error: {error}', 'danger')

# Example 2: Using decorator
from db_utils import with_db_transaction

@with_db_transaction
def create_user(username, email):
    user = User(username=username, email=email)
    db.session.add(user)
    # No need to commit, decorator handles it

# Example 3: Using context manager
from db_utils import DatabaseContextManager

with DatabaseContextManager(db.session) as dbcm:
    user = User(username='test')
    db.session.add(user)
    # Automatically commits on success, rolls back on exception
"""