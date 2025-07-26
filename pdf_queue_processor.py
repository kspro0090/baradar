#!/usr/bin/env python3
"""
PDF Queue Processor
Manages a queue for PDF generation to prevent concurrent Google Docs modifications
"""

import os
import queue
import threading
import time
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from google_docs_pdf_generator import generate_pdf_for_service_request

logger = logging.getLogger(__name__)

# Flask app and db will be set when initialized
_app = None
_db = None

def init_queue_processor(app, db):
    """Initialize the queue processor with Flask app and db"""
    global _app, _db
    _app = app
    _db = db

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class PDFTask:
    """Represents a PDF generation task"""
    task_id: str
    service_request: Any
    status: ProcessingStatus = ProcessingStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class PDFQueueProcessor:
    """Processes PDF generation requests sequentially"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 5.0):
        """
        Initialize the PDF queue processor
        
        Args:
            max_retries: Maximum number of retries for failed tasks
            retry_delay: Delay between retries in seconds
        """
        self.queue = queue.Queue()
        self.tasks = {}  # task_id -> PDFTask
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.is_running = False
        self.worker_thread = None
        self._lock = threading.Lock()
        
        logger.info("PDF Queue Processor initialized")
    
    def start(self):
        """Start the queue processor"""
        if self.is_running:
            logger.warning("Queue processor already running")
            return
        
        self.is_running = True
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        logger.info("Queue processor started")
    
    def stop(self):
        """Stop the queue processor"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=10)
        logger.info("Queue processor stopped")
    
    def add_task(self, service_request: Any, callback: Optional[Callable] = None) -> str:
        """
        Add a PDF generation task to the queue
        
        Args:
            service_request: Service request object
            callback: Optional callback function to call when task completes
            
        Returns:
            Task ID
        """
        task_id = f"pdf_task_{service_request.tracking_code}_{int(time.time())}"
        
        task = PDFTask(
            task_id=task_id,
            service_request=service_request,
            callback=callback
        )
        
        with self._lock:
            self.tasks[task_id] = task
        
        self.queue.put(task)
        logger.info(f"Added task {task_id} to queue")
        
        return task_id
    
    def get_task_status(self, task_id: str) -> Optional[PDFTask]:
        """Get the status of a task"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def get_queue_size(self) -> int:
        """Get the number of tasks in queue"""
        return self.queue.qsize()
    
    def get_all_tasks(self) -> Dict[str, PDFTask]:
        """Get all tasks"""
        with self._lock:
            return self.tasks.copy()
    
    def _process_queue(self):
        """Worker thread that processes the queue"""
        logger.info("Queue processor worker started")
        
        while self.is_running:
            try:
                # Get task from queue with timeout
                task = self.queue.get(timeout=1)
                
                # Process the task
                self._process_task(task)
                
            except queue.Empty:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in queue processor: {str(e)}")
                time.sleep(1)
        
        logger.info("Queue processor worker stopped")
    
    def _process_task(self, task: PDFTask):
        """Process a single PDF generation task"""
        logger.info(f"Processing task {task.task_id}")
        
        # Update task status
        with self._lock:
            task.status = ProcessingStatus.PROCESSING
            task.processed_at = datetime.now()
        
        retries = 0
        success = False
        
        while retries <= self.max_retries and not success:
            try:
                # Use app context for database operations
                if _app:
                    with _app.app_context():
                        # Re-fetch the service request from database to avoid detached instance errors
                        if hasattr(task.service_request, 'id') and _db:
                            from models import ServiceRequest
                            service_request = _db.session.get(ServiceRequest, task.service_request.id)
                            if not service_request:
                                raise Exception(f"Service request with id {task.service_request.id} not found")
                        else:
                            service_request = task.service_request
                        
                        # Generate PDF
                        pdf_filename = generate_pdf_for_service_request(service_request)
                        
                        if pdf_filename:
                            # Success
                            with self._lock:
                                task.status = ProcessingStatus.COMPLETED
                                task.result = pdf_filename
                            
                            logger.info(f"Task {task.task_id} completed successfully: {pdf_filename}")
                            success = True
                            
                            # Call callback if provided
                            if task.callback:
                                try:
                                    task.callback(task)
                                except Exception as e:
                                    logger.error(f"Error in task callback: {str(e)}")
                        else:
                            raise Exception("PDF generation returned None")
                else:
                    # No app context, run directly
                    pdf_filename = generate_pdf_for_service_request(task.service_request)
                    
                    if pdf_filename:
                        # Success
                        with self._lock:
                            task.status = ProcessingStatus.COMPLETED
                            task.result = pdf_filename
                        
                        logger.info(f"Task {task.task_id} completed successfully: {pdf_filename}")
                        success = True
                        
                        # Call callback if provided
                        if task.callback:
                            try:
                                task.callback(task)
                            except Exception as e:
                                logger.error(f"Error in task callback: {str(e)}")
                    else:
                        raise Exception("PDF generation returned None")
                    
            except Exception as e:
                retries += 1
                error_msg = f"Error processing task {task.task_id} (attempt {retries}): {str(e)}"
                logger.error(error_msg)
                
                if retries <= self.max_retries:
                    logger.info(f"Retrying task {task.task_id} in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    # Max retries reached
                    with self._lock:
                        task.status = ProcessingStatus.FAILED
                        task.error = str(e)
                    
                    logger.error(f"Task {task.task_id} failed after {retries} attempts")
                    
                    # Call callback with failure
                    if task.callback:
                        try:
                            task.callback(task)
                        except Exception as callback_error:
                            logger.error(f"Error in task callback: {str(callback_error)}")

# Global instance
_queue_processor = None

def get_queue_processor() -> PDFQueueProcessor:
    """Get or create the global queue processor"""
    global _queue_processor
    if _queue_processor is None:
        _queue_processor = PDFQueueProcessor()
        _queue_processor.start()
    return _queue_processor

def add_pdf_task(service_request: Any, callback: Optional[Callable] = None) -> str:
    """
    Add a PDF generation task to the global queue
    
    Args:
        service_request: Service request object
        callback: Optional callback function
        
    Returns:
        Task ID
    """
    processor = get_queue_processor()
    return processor.add_task(service_request, callback)

def get_task_status(task_id: str) -> Optional[PDFTask]:
    """Get the status of a task"""
    processor = get_queue_processor()
    return processor.get_task_status(task_id)

def wait_for_task(task_id: str, timeout: float = 60.0) -> Optional[PDFTask]:
    """
    Wait for a task to complete
    
    Args:
        task_id: Task ID to wait for
        timeout: Maximum time to wait in seconds
        
    Returns:
        Completed task or None if timeout
    """
    processor = get_queue_processor()
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        task = processor.get_task_status(task_id)
        
        if task and task.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]:
            return task
        
        time.sleep(0.5)
    
    return None

if __name__ == "__main__":
    # Test the queue processor
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create mock service request
    class MockServiceRequest:
        def __init__(self, tracking_code):
            self.tracking_code = tracking_code
            self.service = type('Service', (), {
                'google_doc_id': 'test_doc_id',
                'form_fields': []
            })()
            
        def get_form_data(self):
            return {'name': 'Test User'}
    
    # Start processor
    processor = get_queue_processor()
    
    # Add some tasks
    print("Adding tasks to queue...")
    task_ids = []
    for i in range(3):
        request = MockServiceRequest(f"TEST-{i}")
        task_id = add_pdf_task(request)
        task_ids.append(task_id)
        print(f"Added task: {task_id}")
    
    print(f"\nQueue size: {processor.get_queue_size()}")
    
    # Wait for tasks to complete
    print("\nWaiting for tasks to complete...")
    for task_id in task_ids:
        task = wait_for_task(task_id, timeout=30)
        if task:
            print(f"Task {task_id}: {task.status.value}")
            if task.error:
                print(f"  Error: {task.error}")
            elif task.result:
                print(f"  Result: {task.result}")
    
    # Stop processor
    processor.stop()