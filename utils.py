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

def save_pdf(file, user_id):
    """Save the uploaded PDF file to a secure location."""
    if not file:
        return None
        
    # Validate that it's a PDF
    if not is_valid_pdf(file):
        return None
        
    # Create a unique filename
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    
    # Ensure the upload directory exists
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(user_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = os.path.join(upload_dir, unique_filename)
    file.save(file_path)
    
    # Return the relative path to the file
    return os.path.join('uploads', str(user_id), unique_filename)

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
