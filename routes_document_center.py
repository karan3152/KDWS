from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_required, current_user
from datetime import datetime
import os
import io

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, DocumentTypes, FamilyMember
from forms import (
    DocumentUploadForm, FamilyMemberForm
)
from utils import (
    save_document, get_employee_documents, get_document_completion_percentage, 
    get_missing_documents
)
from pdf_utils import generate_combined_pdf, create_documents_zip, add_metadata_to_combined_pdf


# Document Center Route
@app.route('/employee/document-center')
@login_required
def document_center():
    """Employee Document Center - Central hub for all document management."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    # Get all documents for this employee
    documents = {}
    for doc_type in DocumentTypes.all_types():
        doc = Document.query.filter_by(employee_id=employee.id, document_type=doc_type).first()
        documents[doc_type] = doc
    
    # Get completion percentage
    completion_percentage = get_document_completion_percentage(employee.id)
    
    # Get family members
    family_members = FamilyMember.query.filter_by(employee_id=employee.id).all()
    
    # Check if combined PDF exists
    combined_pdf_path = os.path.join(app.root_path, 'static', 'uploads', str(current_user.id), 'combined', 'combined_documents.pdf')
    has_combined_pdf = os.path.exists(combined_pdf_path)
    
    # Initialize document upload form
    upload_form = DocumentUploadForm()
    # Pre-populate document type choices based on DocumentTypes.all_types()
    upload_form.document_type.choices = [(doc_type, doc_type.replace('_', ' ').title()) for doc_type in DocumentTypes.all_types()]
    
    return render_template('employee/document_center.html',
                          employee=employee,
                          documents=documents,
                          document_types=DocumentTypes.all_types(),
                          completion_percentage=completion_percentage,
                          family_members=family_members,
                          has_combined_pdf=has_combined_pdf,
                          upload_form=upload_form,
                          missing_documents=get_missing_documents(employee.id))


# Combined Document Generation
@app.route('/employee/generate-combined-documents')
@login_required
def generate_combined_documents():
    """Generate a combined PDF of all documents for an employee."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    # Check if all required documents are uploaded
    missing_docs = get_missing_documents(employee.id)
    if missing_docs:
        missing_docs_str = ', '.join([doc.replace('_', ' ').title() for doc in missing_docs])
        flash(f'Cannot generate combined PDF. Missing required documents: {missing_docs_str}', 'warning')
        return redirect(url_for('document_center'))
    
    # Get all documents for this employee
    all_documents = Document.query.filter_by(employee_id=employee.id).all()
    
    # Order documents in the desired sequence
    document_order = {
        DocumentTypes.NEW_JOINING_FORM: 1,
        DocumentTypes.PF_FORM: 2,
        DocumentTypes.FORM_1_NOMINATION: 3,
        DocumentTypes.FORM_11: 4,
        DocumentTypes.AADHAR_CARD: 5,
        DocumentTypes.PAN_CARD: 6,
        DocumentTypes.PHOTO: 7,
        DocumentTypes.BANK_PASSBOOK: 8,
        DocumentTypes.POLICE_VERIFICATION: 9,
        DocumentTypes.MEDICAL_CERTIFICATE: 10,
        DocumentTypes.FAMILY_DECLARATION: 11
    }
    
    # Sort documents by the order defined above
    ordered_documents = sorted(all_documents, key=lambda doc: document_order.get(doc.document_type, 99))
    
    # Generate the combined PDF
    pdf_buffer = generate_combined_pdf(ordered_documents)
    
    if not pdf_buffer:
        flash('Error generating combined PDF. Please try again later.', 'error')
        return redirect(url_for('document_center'))
    
    # Add metadata to the PDF
    pdf_buffer_with_metadata = add_metadata_to_combined_pdf(pdf_buffer, employee)
    
    # Save the combined PDF
    combined_dir = os.path.join(app.root_path, 'static', 'uploads', str(current_user.id), 'combined')
    os.makedirs(combined_dir, exist_ok=True)
    
    combined_path = os.path.join(combined_dir, 'combined_documents.pdf')
    with open(combined_path, 'wb') as f:
        f.write(pdf_buffer_with_metadata.getbuffer())
    
    flash('Combined PDF generated successfully!', 'success')
    return redirect(url_for('document_center'))


# Preview Combined PDF
@app.route('/employee/preview-combined-pdf')
@login_required
def preview_combined_pdf():
    """Preview the combined PDF in the browser."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    combined_path = os.path.join(app.root_path, 'static', 'uploads', str(current_user.id), 'combined', 'combined_documents.pdf')
    
    if not os.path.exists(combined_path):
        flash('Combined PDF not found. Please generate it first.', 'warning')
        return redirect(url_for('document_center'))
    
    return send_file(combined_path, mimetype='application/pdf')


# Download All Documents as ZIP
@app.route('/employee/download-all-documents')
@login_required
def download_all_documents():
    """Download all uploaded documents as a ZIP file."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    # Get all documents for this employee
    all_documents = Document.query.filter_by(employee_id=employee.id).all()
    
    if not all_documents:
        flash('No documents found to download.', 'warning')
        return redirect(url_for('document_center'))
    
    # Create a ZIP file with all documents
    zip_buffer = create_documents_zip(all_documents)
    
    # Return the ZIP file
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f"employee_{employee.employee_id}_documents.zip"
    )


# Download Form Package
@app.route('/employee/download-form-package')
@login_required
def download_form_package():
    """Download a package of blank forms for offline filling."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    # Path to the blank forms package
    forms_package_path = os.path.join(app.root_path, 'static', 'forms', 'blank_forms_package.zip')
    
    # Check if the package exists
    if not os.path.exists(forms_package_path):
        flash('Forms package not found. Please contact administrator.', 'warning')
        return redirect(url_for('document_center'))
    
    # Return the ZIP file
    return send_file(
        forms_package_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name="hr_talent_blank_forms.zip"
    )


# Manage Family Members
@app.route('/employee/manage-family-members', methods=['GET', 'POST'])
@login_required
def manage_family_members():
    """Add, edit, or remove family members."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    form = FamilyMemberForm()
    
    if form.validate_on_submit():
        # Create a new family member
        member = FamilyMember(
            employee_id=employee.id,
            name=form.name.data,
            relationship=form.relationship.data,
            date_of_birth=form.date_of_birth.data,
            aadhar_id=form.aadhar_id.data,
            contact_number=form.contact_number.data
        )
        
        # Handle photo upload if provided
        if form.photo.data:
            photo_path = save_document(form.photo.data, current_user.id, 'family_photos')
            member.photo_path = photo_path
        
        db.session.add(member)
        
        # Check if we need to create a family details document
        family_document = Document.query.filter_by(
            employee_id=employee.id,
            document_type=DocumentTypes.FAMILY_DECLARATION
        ).first()
        
        if not family_document:
            # Create a placeholder document for family details
            family_document = Document(
                employee_id=employee.id,
                document_type=DocumentTypes.FAMILY_DECLARATION,
                document_name="Family Details",
                file_path="system/family_details.pdf",  # Placeholder path
                status='pending'
            )
            db.session.add(family_document)
        
        db.session.commit()
        flash(f'Family member {form.name.data} added successfully!', 'success')
        return redirect(url_for('manage_family_members'))
    
    # Get existing family members
    family_members = FamilyMember.query.filter_by(employee_id=employee.id).all()
    
    return render_template('employee/manage_family_members.html',
                          employee=employee,
                          form=form,
                          family_members=family_members)


# Remove Family Member
@app.route('/employee/remove-family-member/<int:member_id>', methods=['POST'])
@login_required
def remove_family_member(member_id):
    """Remove a family member."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    member = FamilyMember.query.get_or_404(member_id)
    
    # Check if this member belongs to the current user
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee or member.employee_id != employee.id:
        flash('Access denied. You can only manage your own family members.', 'error')
        return redirect(url_for('manage_family_members'))
    
    member_name = member.name
    db.session.delete(member)
    db.session.commit()
    
    flash(f'Family member {member_name} removed successfully!', 'success')
    return redirect(url_for('manage_family_members'))


# FORM FILLING ROUTES

# Joining Form
@app.route('/employee/fill/joining-form', methods=['GET', 'POST'])
@login_required
def fill_joining_form():
    """Online form for New Joining Application."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    from flask_wtf import FlaskForm
    from wtforms import StringField, DateField, SelectField, TextAreaField
    from wtforms.validators import DataRequired, Email, Length
    
    class JoiningForm(FlaskForm):
        full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
        guardian_name = StringField("Father's/Husband's Name", validators=[DataRequired(), Length(max=100)])
        date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
        gender = SelectField('Gender', choices=[('', 'Select Gender'), ('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
        marital_status = SelectField('Marital Status', choices=[('', 'Select Status'), ('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widowed', 'Widowed')], validators=[DataRequired()])
        contact_number = StringField('Contact Number', validators=[DataRequired(), Length(min=10, max=15)])
        email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
        current_address = TextAreaField('Current Address', validators=[DataRequired(), Length(max=200)])

    form = JoiningForm()
    
    if form.validate_on_submit():
        # Handle form submission here
        flash('Form submitted successfully!', 'success')
        return redirect(url_for('document_center'))
    
    return render_template('employee/forms/joining_form.html', form=form)


# PF Form
@app.route('/employee/fill/pf-form', methods=['GET', 'POST'])
@login_required
def fill_pf_form():
    """Online form for PF Form 2 (Revised)."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    # Implementation for online form filling
    # ...
    
    return render_template('employee/forms/pf_form.html')


# Form 1
@app.route('/employee/fill/form1', methods=['GET', 'POST'])
@login_required
def fill_form1():
    """Online form for Form 1 (Nomination & Declaration)."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    # Implementation for online form filling
    # ...
    
    return render_template('employee/forms/form1.html')


# Form 11
@app.route('/employee/fill/form11', methods=['GET', 'POST'])
@login_required
def fill_form11():
    """Online form for Form 11 (Revised)."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    # Implementation for online form filling
    # ...
    
    return render_template('employee/forms/form11.html')


# Document Upload
@app.route('/employee/upload-document', methods=['POST'])
@login_required
def upload_document():
    """Upload a document for the current employee."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    form = DocumentUploadForm()
    # Pre-populate document type choices based on DocumentTypes.all_types()
    form.document_type.choices = [(doc_type, doc_type.replace('_', ' ').title()) for doc_type in DocumentTypes.all_types()]
    
    if form.validate_on_submit():
        document_type = form.document_type.data
        file = form.file.data
        notes = form.notes.data
        
        # Check if this document type already exists for the employee
        existing_doc = Document.query.filter_by(
            employee_id=employee.id,
            document_type=document_type
        ).first()
        
        if existing_doc:
            # Update existing document
            if existing_doc.file_path and existing_doc.file_path.startswith('static/uploads/'):
                # Try to remove old file if it exists
                try:
                    old_file_path = os.path.join(app.root_path, existing_doc.file_path)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)
                except Exception as e:
                    app.logger.error(f"Error removing old file: {str(e)}")
            
            # Save new file
            file_path = save_document(file, current_user.id, document_type.lower())
            
            # Update document record
            existing_doc.document_name = file.filename
            existing_doc.file_path = file_path
            existing_doc.notes = notes
            existing_doc.upload_date = datetime.now()
            existing_doc.status = 'pending'  # Reset status when document is updated
            
            db.session.commit()
            flash(f'{document_type.replace("_", " ").title()} has been updated successfully!', 'success')
        else:
            # Save new file
            file_path = save_document(file, current_user.id, document_type.lower())
            
            # Create new document record
            new_document = Document(
                employee_id=employee.id,
                document_type=document_type,
                document_name=file.filename,
                file_path=file_path,
                notes=notes,
                status='pending'
            )
            
            db.session.add(new_document)
            db.session.commit()
            flash(f'{document_type.replace("_", " ").title()} has been uploaded successfully!', 'success')
        
        return redirect(url_for('document_center'))
    
    # If validation fails, show errors
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'Error in {field}: {error}', 'error')
    
    return redirect(url_for('document_center'))


# Replace Document
@app.route('/employee/replace-document', methods=['POST'])
@login_required
def replace_document():
    """Replace an existing document."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    document_id = request.form.get('document_id')
    if not document_id:
        flash('Document ID is required.', 'error')
        return redirect(url_for('document_center'))
    
    # Check if document exists and belongs to this employee
    document = Document.query.get_or_404(document_id)
    if document.employee_id != employee.id:
        flash('Access denied. You can only replace your own documents.', 'error')
        return redirect(url_for('document_center'))
    
    # Process the new file
    file = request.files.get('file')
    if not file:
        flash('No file provided.', 'error')
        return redirect(url_for('document_center'))
    
    # Check file type (simplified check)
    filename = file.filename.lower()
    if not (filename.endswith('.pdf') or filename.endswith('.jpg') or 
            filename.endswith('.jpeg') or filename.endswith('.png')):
        flash('Invalid file type. Only PDF, JPG, JPEG, and PNG are allowed.', 'error')
        return redirect(url_for('document_center'))
    
    # Remove old file if it exists
    if document.file_path and document.file_path.startswith('static/uploads/'):
        try:
            old_file_path = os.path.join(app.root_path, document.file_path)
            if os.path.exists(old_file_path):
                os.remove(old_file_path)
        except Exception as e:
            app.logger.error(f"Error removing old file: {str(e)}")
    
    # Save new file
    file_path = save_document(file, current_user.id, document.document_type.lower())
    
    # Update document record
    document.document_name = file.filename
    document.file_path = file_path
    document.upload_date = datetime.now()
    document.status = 'pending'  # Reset status when document is replaced
    
    db.session.commit()
    flash(f'{document.document_type.replace("_", " ").title()} has been replaced successfully!', 'success')
    
    return redirect(url_for('document_center'))
