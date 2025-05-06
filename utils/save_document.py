import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app

def save_document(file, user_id, document_type):
    """
    Save an uploaded file under static/uploads/<user_id>/<document_type>/ with a unique filename.
    Returns the relative path to the saved file for storage in the database.
    """
    # Secure the filename
    filename = secure_filename(file.filename)

    # Create directory path
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(user_id), document_type)
    os.makedirs(upload_dir, exist_ok=True)

    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{document_type}_{timestamp}_{filename}"

    # Full path to save the file
    full_path = os.path.join(upload_dir, unique_filename)

    # Save the file
    file.save(full_path)

    # Return relative path from static folder with forward slashes for web URLs
    relative_path = os.path.join('uploads', str(user_id), document_type, unique_filename)
    # Convert backslashes to forward slashes for web URL compatibility
    relative_path = relative_path.replace('\\', '/')
    return relative_path
