import os
import secrets
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app, request
from PIL import Image
import io

from models import Document, DocumentTypes


def send_password_reset_email(user, token):
    """
    Send a password reset email to the user.
    
    In a production environment, this would use an email service like SendGrid, Mailgun, etc.
    For development, just print the reset link to the console.
    """
    reset_url = f"{request.host_url.rstrip('/')}/reset-password/{token}"
    
    # Print to console for development
    print(f"Password reset requested for {user.email}")
    print(f"Reset URL: {reset_url}")
    
    # In production, would send an actual email
    # send_email(
    #     subject='Password Reset Request',
    #     sender=current_app.config['MAIL_DEFAULT_SENDER'],
    #     recipients=[user.email],
    #     text_body=f'Please use the following link to reset your password: {reset_url}',
    #     html_body=f'<p>Please use the following link to reset your password:</p><p><a href="{reset_url}">{reset_url}</a></p>'
    # )


def save_document(file, user_id, subfolder=None):
    """
    Save an uploaded document file to the appropriate location.
    
    Args:
        file: The uploaded file object from Flask's request.files
        user_id: The ID of the user uploading the document
        subfolder: Optional subfolder within the user's uploads directory
    
    Returns:
        The relative path to the saved file
    """
    # Ensure uploads directory exists
    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(user_id))
    if subfolder:
        uploads_dir = os.path.join(uploads_dir, subfolder)
    os.makedirs(uploads_dir, exist_ok=True)
    
    # Secure the filename and add a timestamp to prevent duplicates
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"{timestamp}_{filename}"
    
    # Save the file
    file_path = os.path.join(uploads_dir, filename)
    file.save(file_path)
    
    # Return the relative path from the app root
    return os.path.join('static', 'uploads', str(user_id), subfolder if subfolder else '', filename)


def resize_image(image_path, max_width=800, max_height=800):
    """
    Resize an image to the specified maximum dimensions while preserving aspect ratio.
    
    Args:
        image_path: Path to the image file
        max_width: Maximum width for the resized image
        max_height: Maximum height for the resized image
    
    Returns:
        The path to the resized image (same as input if no resize was needed)
    """
    # Open the image
    img = Image.open(image_path)
    
    # Check if resize is needed
    if img.width <= max_width and img.height <= max_height:
        img.close()
        return image_path
    
    # Calculate new dimensions while preserving aspect ratio
    ratio = min(max_width / img.width, max_height / img.height)
    new_width = int(img.width * ratio)
    new_height = int(img.height * ratio)
    
    # Resize the image
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    # Save the resized image (overwrite original)
    resized_img.save(image_path, optimize=True, quality=85)
    
    # Close the images
    img.close()
    resized_img.close()
    
    return image_path


def get_employee_documents(employee_id):
    """
    Get all documents for an employee, organized by document type.
    
    Args:
        employee_id: The ID of the employee
    
    Returns:
        A dictionary with document types as keys and document objects as values
    """
    documents = {}
    for doc_type in DocumentTypes.all_types():
        doc = Document.query.filter_by(employee_id=employee_id, document_type=doc_type).first()
        documents[doc_type] = doc
    
    return documents


def get_document_completion_percentage(employee_id):
    """
    Calculate the percentage of required documents that have been submitted.
    
    Args:
        employee_id: The ID of the employee
    
    Returns:
        An integer percentage value (0-100)
    """
    required_types = DocumentTypes.get_required_types()
    submitted_count = Document.query.filter(
        Document.employee_id == employee_id,
        Document.document_type.in_(required_types)
    ).count()
    
    total_required = len(required_types)
    if total_required == 0:
        return 100  # Avoid division by zero
    
    return int((submitted_count / total_required) * 100)


def get_missing_documents(employee_id):
    """
    Get a list of required document types that have not been submitted.
    
    Args:
        employee_id: The ID of the employee
    
    Returns:
        A list of document type strings
    """
    required_types = DocumentTypes.get_required_types()
    submitted_docs = Document.query.filter(
        Document.employee_id == employee_id,
        Document.document_type.in_(required_types)
    ).all()
    
    submitted_types = [doc.document_type for doc in submitted_docs]
    missing_types = [doc_type for doc_type in required_types if doc_type not in submitted_types]
    
    return missing_types


def format_date(date):
    """Format a date object as a string."""
    if date:
        return date.strftime('%d-%b-%Y')
    return 'N/A'


def replace_underscores(text):
    """Replace underscores with spaces and capitalize each word."""
    if text:
        return text.replace('_', ' ').title()
    return ''