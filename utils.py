import os
import uuid
import base64
from datetime import datetime, timedelta
from flask import current_app
from werkzeug.utils import secure_filename
import PyPDF2
from io import BytesIO

def generate_reset_token():
    """Generate a unique token for password reset."""
    return base64.urlsafe_b64encode(os.urandom(30)).decode('utf-8')

def get_token_expiry():
    """Return an expiry time 24 hours from now."""
    return datetime.utcnow() + timedelta(hours=24)

def is_valid_pdf(file_stream):
    """Check if the uploaded file is a valid PDF."""
    try:
        # Create a BytesIO object from the file stream
        mem_file = BytesIO(file_stream.read())
        # Reset the file pointer to the beginning
        file_stream.seek(0)
        # Try to read the PDF
        PyPDF2.PdfReader(mem_file)
        return True
    except:
        return False

def is_valid_image(file_stream):
    """Check if the uploaded file is a valid image (JPG, PNG)."""
    try:
        # Check file extension
        file_ext = os.path.splitext(file_stream.filename)[1].lower()
        return file_ext in ['.jpg', '.jpeg', '.png']
    except:
        return False

def save_document(file, user_id, document_type):
    """
    Save the uploaded document file to a secure location.
    Works with PDFs and images based on document type.
    Returns the relative path to the saved file.
    """
    if not file:
        return None
    
    # Validate file based on document type
    if document_type in ['photo']:
        if not is_valid_image(file):
            return None
    elif not is_valid_pdf(file) and not is_valid_image(file):
        return None
    
    # Create a unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{document_type}_{uuid.uuid4()}_{filename}"
    
    # Ensure the upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(user_id), document_type)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    # Return the relative path to the file
    return os.path.join('uploads', str(user_id), document_type, unique_filename)

def save_pdf(file, user_id):
    """Save the uploaded PDF file to a secure location."""
    return save_document(file, user_id, 'pdf')

def extract_pdf_data(file_path):
    """Extract text data from a PDF file."""
    try:
        # Open the PDF file
        full_path = os.path.join(current_app.root_path, 'static', file_path)
        with open(full_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            
            # Extract text from each page
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text() + "\n"
                
            return text
    except Exception as e:
        current_app.logger.error(f"Error extracting PDF data: {str(e)}")
        return None

def validate_login_identifier(identifier):
    """
    Determine if the login identifier is a username, employee ID, or Aadhar ID.
    Returns the type of identifier.
    """
    if '@' in identifier:
        return 'email'
    elif identifier.isdigit() and len(identifier) == 12:
        return 'aadhar_id'
    elif identifier.startswith('EMP'):
        return 'employee_id'
    else:
        return 'username'

def get_document_status(employee_id, document_type):
    """
    Check if a specific document type has been uploaded for an employee.
    Returns True if the document exists, False otherwise.
    """
    from models import Document
    doc = Document.query.filter_by(employee_id=employee_id, document_type=document_type).first()
    return doc is not None

def get_employee_documents(employee_id):
    """
    Get all documents for a specific employee.
    Returns a dictionary with document types as keys and document objects as values.
    """
    from models import Document, DocumentTypes
    documents = {}
    
    # Get all document types
    for doc_type in DocumentTypes.all_types():
        doc = Document.query.filter_by(employee_id=employee_id, document_type=doc_type).first()
        documents[doc_type] = doc
        
    return documents

def get_missing_documents(employee_id):
    """
    Get a list of required document types that are missing for an employee.
    """
    from models import Document, DocumentTypes
    missing_docs = []
    
    # Check for each required document type
    for doc_type in DocumentTypes.get_required_types():
        doc = Document.query.filter_by(employee_id=employee_id, document_type=doc_type).first()
        if not doc:
            missing_docs.append(doc_type)
            
    return missing_docs

def get_document_completion_percentage(employee_id):
    """
    Calculate the percentage of required documents that have been uploaded.
    """
    from models import DocumentTypes
    required_docs = DocumentTypes.get_required_types()
    missing_docs = get_missing_documents(employee_id)
    
    if not required_docs:
        return 100  # No required documents
        
    completed = len(required_docs) - len(missing_docs)
    return int((completed / len(required_docs)) * 100)
