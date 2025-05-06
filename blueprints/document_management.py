from flask import Blueprint, flash, redirect, url_for, current_app, render_template
from flask_login import login_required, current_user
import os
import shutil

from extensions import db, csrf
from models import Document, EmployeeProfile

document_management = Blueprint('document_management', __name__)

@document_management.route('/confirm-delete-all-documents', methods=['GET'])
@login_required
def confirm_delete_all_documents():
    """Show confirmation page for deleting all documents."""
    if not current_user.is_employee():
        flash('Access denied. Only employees can delete their documents.', 'danger')
        return redirect(url_for('main.index'))

    return render_template('documents/delete_all_confirmation.html')

@document_management.route('/delete-all-documents', methods=['POST'])
@login_required
def delete_all_documents():
    """Delete all documents for the current user."""
    if not current_user.is_employee():
        flash('Access denied. Only employees can delete their documents.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('main.index'))

    # Get all documents for this user
    documents = Document.query.filter_by(user_id=current_user.id).all()

    if not documents:
        flash('No documents found to delete.', 'info')
        return redirect(url_for('main.document_center'))

    # Track statistics for user feedback
    deleted_count = 0
    file_count = 0

    # Delete each document and its associated file
    for document in documents:
        # Try to delete the file if it exists
        if document.file_path:
            try:
                # Get the full path to the file
                if document.file_path.startswith('static/'):
                    file_path = os.path.join(current_app.root_path, document.file_path)
                else:
                    file_path = os.path.join(current_app.root_path, 'static', document.file_path)

                # Check if the file exists and delete it
                if os.path.exists(file_path):
                    os.remove(file_path)
                    file_count += 1
                    current_app.logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                current_app.logger.error(f"Error deleting file for document {document.id}: {str(e)}")

        # Delete the document record from the database
        db.session.delete(document)
        deleted_count += 1

    # Commit the changes to the database
    db.session.commit()

    # Clean up empty directories in the user's upload folder
    try:
        user_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
        if os.path.exists(user_upload_dir):
            # Remove all subdirectories and files
            for root, dirs, files in os.walk(user_upload_dir, topdown=False):
                for file in files:
                    os.remove(os.path.join(root, file))
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if os.path.exists(dir_path):
                        shutil.rmtree(dir_path)
    except Exception as e:
        current_app.logger.error(f"Error cleaning up directories: {str(e)}")

    # Also check for any files in the joining_forms directory
    try:
        joining_forms_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'joining_forms')
        if os.path.exists(joining_forms_dir):
            for file in os.listdir(joining_forms_dir):
                if file.startswith(f"joining_form_{employee.id}_"):
                    file_path = os.path.join(joining_forms_dir, file)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        file_count += 1
                        current_app.logger.info(f"Deleted joining form: {file_path}")
    except Exception as e:
        current_app.logger.error(f"Error cleaning up joining forms: {str(e)}")

    flash(f'Successfully deleted {deleted_count} document records and {file_count} files.', 'success')
    return redirect(url_for('main.document_center'))
