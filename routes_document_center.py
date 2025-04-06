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
        DocumentTypes.JOINING_FORM: 1,
        DocumentTypes.PF_FORM: 2,
        DocumentTypes.FORM1: 3,
        DocumentTypes.FORM11: 4,
        DocumentTypes.AADHAR: 5,
        DocumentTypes.PAN: 6,
        DocumentTypes.PHOTO: 7,
        DocumentTypes.PASSBOOK: 8,
        DocumentTypes.POLICE_VERIFICATION: 9,
        DocumentTypes.MEDICAL_CERTIFICATE: 10,
        DocumentTypes.FAMILY_DETAILS: 11
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
            document_type=DocumentTypes.FAMILY_DETAILS
        ).first()
        
        if not family_document:
            # Create a placeholder document for family details
            family_document = Document(
                employee_id=employee.id,
                document_type=DocumentTypes.FAMILY_DETAILS,
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
    
    # Implementation for online form filling
    # ...
    
    return render_template('employee/forms/joining_form.html')


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