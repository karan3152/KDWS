from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import urlsplit
from datetime import datetime
import os

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, PasswordResetToken, DocumentTypes, FamilyMember, ROLE_ADMIN, ROLE_EMPLOYER, ROLE_EMPLOYEE, NewsUpdate
from forms import (
    LoginForm, PasswordResetRequestForm, PasswordResetForm, FirstLoginForm,
    CreateEmployeeForm, CreateEmployerForm, EmployeeProfileForm,
    EmployeeSearchForm, DocumentUploadForm, AadharUploadForm, PANUploadForm,
    PhotoUploadForm, PassbookUploadForm, JoiningFormUploadForm, PFFormUploadForm,
    Form1UploadForm, Form11UploadForm, NewsUpdateForm, PoliceVerificationUploadForm,
    MedicalCertificateUploadForm, FamilyMemberForm, FamilyDetailsUploadForm
)
from utils import (
    generate_reset_token, get_token_expiry, save_document, save_pdf,
    extract_pdf_data, validate_login_identifier, get_document_status,
    get_employee_documents, get_missing_documents, get_document_completion_percentage
)
from pdf_utils import generate_combined_pdf, create_documents_zip, add_metadata_to_combined_pdf

# Login and Authentication Routes

@app.route('/')
def index():
    """Redirect to login if not logged in, otherwise to appropriate dashboard."""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin_dashboard'))
        elif current_user.is_employer():
            return redirect(url_for('employer_dashboard'))
        elif current_user.is_employee():
            # Check if this is the first login
            if current_user.first_login:
                return redirect(url_for('first_login'))
            return redirect(url_for('employee_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    # Get the latest news/updates for login page
    latest_news = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.published_date.desc()).limit(5).all()
        
    form = LoginForm()
    if form.validate_on_submit():
        # Determine the type of identifier (username, employee ID, or Aadhar ID)
        identifier_type = validate_login_identifier(form.username.data)
        user = None
        
        if identifier_type == 'email':
            user = User.query.filter_by(email=form.username.data).first()
        elif identifier_type == 'username':
            user = User.query.filter_by(username=form.username.data).first()
        elif identifier_type == 'employee_id':
            employee = EmployeeProfile.query.filter_by(employee_id=form.username.data).first()
            if employee:
                user = User.query.get(employee.user_id)
        elif identifier_type == 'aadhar_id':
            employee = EmployeeProfile.query.filter_by(aadhar_id=form.username.data).first()
            if employee:
                user = User.query.get(employee.user_id)
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return render_template('login.html', form=form, latest_news=latest_news)
            
        login_user(user)
        
        # Redirect to appropriate dashboard or first login page
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            if user.first_login and user.is_employee():
                next_page = url_for('first_login')
            elif user.is_admin():
                next_page = url_for('admin_dashboard')
            elif user.is_employer():
                next_page = url_for('employer_dashboard')
            else:
                next_page = url_for('employee_dashboard')
        return redirect(next_page)
        
    return render_template('login.html', form=form, latest_news=latest_news)

@app.route('/logout')
@login_required
def logout():
    """Log out the current user."""
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/reset-password/request', methods=['GET', 'POST'])
def reset_password_request():
    """Handle requests for password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate a reset token
            token = generate_reset_token()
            # Create a new reset token record
            reset_token = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=get_token_expiry()
            )
            db.session.add(reset_token)
            db.session.commit()
            
            # In a real app, send an email with the reset link
            # For this demo, just flash the token
            flash(f'Your password reset token is: {token}', 'info')
            flash('Please use this token to reset your password.', 'info')
            return redirect(url_for('reset_password', token=token))
        else:
            flash('Email not found in our records', 'error')
            
    return render_template('reset_password.html', form=form, request_form=True)

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Handle password reset with a valid token."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    # Check if the token is valid
    token_record = PasswordResetToken.query.filter_by(token=token).first()
    if not token_record or token_record.expires_at < datetime.utcnow():
        flash('The password reset link is invalid or has expired', 'error')
        return redirect(url_for('reset_password_request'))
        
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.get(token_record.user_id)
        user.set_password(form.password.data)
        
        # Delete all reset tokens for this user
        PasswordResetToken.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        flash('Your password has been reset successfully', 'success')
        return redirect(url_for('login'))
        
    return render_template('reset_password.html', form=form, request_form=False)

@app.route('/first-login', methods=['GET', 'POST'])
@login_required
def first_login():
    """Handle employee's first login to set a new password."""
    if not current_user.is_employee() or not current_user.first_login:
        return redirect(url_for('index'))
        
    form = FirstLoginForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            current_user.first_login = False
            db.session.commit()
            
            flash('Password updated successfully', 'success')
            return redirect(url_for('employee_dashboard'))
        else:
            flash('Current password is incorrect', 'error')
            
    return render_template('employee/first_login.html', form=form)

# Admin Routes

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard page."""
    if not current_user.is_admin():
        abort(403)  # Forbidden
    
    # Get counts for dashboard
    employee_count = User.query.filter_by(role=ROLE_EMPLOYEE).count()
    employer_count = User.query.filter_by(role=ROLE_EMPLOYER).count()
    document_count = Document.query.count()
    
    return render_template('admin/dashboard.html', 
                          employee_count=employee_count,
                          employer_count=employer_count,
                          document_count=document_count)

@app.route('/admin/create-employee', methods=['GET', 'POST'])
@login_required
def create_employee():
    """Create a new employee account."""
    if not current_user.is_admin():
        abort(403)  # Forbidden
        
    form = CreateEmployeeForm()
    if form.validate_on_submit():
        # Create a new user with employee role
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_EMPLOYEE,
            first_login=True
        )
        user.set_password(form.temporary_password.data)
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Create the employee profile
        employee = EmployeeProfile(
            user_id=user.id,
            aadhar_id=form.aadhar_id.data,
            employee_id=form.employee_id.data,
            department=form.department.data,
            position=form.position.data
        )
        db.session.add(employee)
        db.session.commit()
        
        flash('Employee account created successfully', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/create_account.html', form=form, account_type='employee')

@app.route('/admin/create-employer', methods=['GET', 'POST'])
@login_required
def create_employer():
    """Create a new employer/HR account."""
    if not current_user.is_admin():
        abort(403)  # Forbidden
        
    form = CreateEmployerForm()
    if form.validate_on_submit():
        # Create a new user with employer role
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_EMPLOYER,
            first_login=False  # Employers don't need first login flow
        )
        user.set_password(form.temporary_password.data)
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID
        
        # Create the employer profile
        employer = EmployerProfile(
            user_id=user.id,
            company_name=form.company_name.data,
            company_id=form.company_id.data,
            department=form.department.data,
            contact_number=form.contact_number.data
        )
        db.session.add(employer)
        db.session.commit()
        
        flash('Employer account created successfully', 'success')
        return redirect(url_for('admin_dashboard'))
        
    return render_template('admin/create_account.html', form=form, account_type='employer')

@app.route('/admin/manage-accounts')
@login_required
def manage_accounts():
    """Manage existing user accounts."""
    if not current_user.is_admin():
        abort(403)  # Forbidden
        
    employees = User.query.filter_by(role=ROLE_EMPLOYEE).all()
    employers = User.query.filter_by(role=ROLE_EMPLOYER).all()
    
    return render_template('admin/manage_accounts.html', employees=employees, employers=employers)

@app.route('/admin/delete-account/<int:user_id>', methods=['POST'])
@login_required
def delete_account(user_id):
    """Delete a user account."""
    if not current_user.is_admin():
        abort(403)  # Forbidden
        
    user = User.query.get_or_404(user_id)
    
    # Don't allow deleting own account
    if user.id == current_user.id:
        flash('You cannot delete your own account', 'error')
        return redirect(url_for('manage_accounts'))
        
    db.session.delete(user)
    db.session.commit()
    
    flash('Account deleted successfully', 'success')
    return redirect(url_for('manage_accounts'))

# Employer Routes

@app.route('/employer/dashboard')
@login_required
def employer_dashboard():
    """Employer dashboard page."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    # Get basic stats for the dashboard
    employee_count = User.query.filter_by(role=ROLE_EMPLOYEE).count()
    recent_documents = Document.query.order_by(Document.upload_date.desc()).limit(5).all()
    
    return render_template('employer/dashboard.html', 
                          employee_count=employee_count,
                          recent_documents=recent_documents)

@app.route('/employer/employee-search', methods=['GET', 'POST'])
@login_required
def employee_search():
    """Search for employees by various criteria."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    form = EmployeeSearchForm()
    employees = []
    
    if form.validate_on_submit() or request.args.get('search_query'):
        search_type = form.search_type.data if form.validate_on_submit() else request.args.get('search_type', 'name')
        search_query = form.search_query.data if form.validate_on_submit() else request.args.get('search_query', '')
        
        if search_type == 'employee_id':
            employee = EmployeeProfile.query.filter_by(employee_id=search_query).first()
            if employee:
                employees = [employee]
        elif search_type == 'aadhar_id':
            employee = EmployeeProfile.query.filter_by(aadhar_id=search_query).first()
            if employee:
                employees = [employee]
        elif search_type == 'name':
            # Search by first or last name
            employees = EmployeeProfile.query.filter(
                (EmployeeProfile.first_name.contains(search_query)) | 
                (EmployeeProfile.last_name.contains(search_query))
            ).all()
            
        if not employees:
            flash('No employees found matching your criteria', 'info')
            
    return render_template('employer/employee_search.html', form=form, employees=employees)

@app.route('/employer/employee/<int:employee_id>')
@login_required
def employee_detail(employee_id):
    """View detailed information about an employee."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.get_or_404(employee_id)
    documents = Document.query.filter_by(employee_id=employee_id).all()
    
    return render_template('employer/employee_detail.html', employee=employee, documents=documents)
    
@app.route('/employer/employee/<int:employee_id>/profile')
@login_required
def view_employee_profile(employee_id):
    """View an employee's profile details."""
    if not current_user.is_employer() and not current_user.is_admin():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.get_or_404(employee_id)
    user = User.query.get(employee.user_id)
    
    # Get required documents and completion status
    documents = get_employee_documents(employee_id)
    missing_docs = get_missing_documents(employee_id)
    completion_percentage = get_document_completion_percentage(employee_id)
    
    return render_template(
        'employer/view_employee_profile.html',
        employee=employee,
        user=user,
        documents=documents,
        missing_docs=missing_docs,
        completion_percentage=completion_percentage
    )

# Employee Routes

@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    """Employee dashboard page."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        # This should never happen if DB is set up correctly
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
        
    # Get documents for this employee
    documents = Document.query.filter_by(employee_id=employee.id).all()
    
    return render_template('employee/dashboard.html', employee=employee, documents=documents)

@app.route('/employee/profile', methods=['GET', 'POST'])
@login_required
def employee_profile():
    """View and update employee profile."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = EmployeeProfileForm(obj=employee)
    
    if form.validate_on_submit():
        # Update the employee profile
        form.populate_obj(employee)
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('employee_dashboard'))
        
    return render_template('employee/profile.html', form=form, employee=employee)

@app.route('/employee/forms', methods=['GET', 'POST'])
@login_required
def employee_forms():
    """View and upload PDF forms."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    # Get existing documents
    documents = get_employee_documents(employee.id)
    missing_docs = get_missing_documents(employee.id)
    completion_percentage = get_document_completion_percentage(employee.id)
    
    # Generic form for document upload (used as fallback)
    form = DocumentUploadForm()
    
    # Pass all the specific document forms to the template
    aadhar_form = AadharUploadForm()
    pan_form = PANUploadForm()
    photo_form = PhotoUploadForm()
    passbook_form = PassbookUploadForm()
    joining_form = JoiningFormUploadForm()
    pf_form = PFFormUploadForm()
    form1_form = Form1UploadForm()
    form11_form = Form11UploadForm()
    police_verification_form = PoliceVerificationUploadForm()
    medical_certificate_form = MedicalCertificateUploadForm()
    family_details_form = FamilyDetailsUploadForm()
    
    return render_template(
        'employee/forms.html',
        form=form,
        documents=documents,
        missing_docs=missing_docs,
        completion_percentage=completion_percentage,
        aadhar_form=aadhar_form,
        pan_form=pan_form,
        photo_form=photo_form,
        passbook_form=passbook_form,
        joining_form=joining_form,
        pf_form=pf_form,
        form1_form=form1_form,
        form11_form=form11_form,
        police_verification_form=police_verification_form,
        medical_certificate_form=medical_certificate_form,
        family_details_form=family_details_form
    )

@app.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View a document."""
    document = Document.query.get_or_404(document_id)
    
    # Check if the user has permission to view this document
    if current_user.is_employee():
        employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee or document.employee_id != employee.id:
            abort(403)  # Forbidden
    elif not (current_user.is_admin() or current_user.is_employer()):
        abort(403)  # Forbidden
        
    return render_template('view_document.html', document=document)

@app.route('/api/document/<int:document_id>')
@login_required
def get_document(document_id):
    """API endpoint to get document data for PDF.js viewer."""
    document = Document.query.get_or_404(document_id)
    
    # Check if the user has permission to view this document
    if current_user.is_employee():
        employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee or document.employee_id != employee.id:
            abort(403)  # Forbidden
    elif not (current_user.is_admin() or current_user.is_employer()):
        abort(403)  # Forbidden
        
    # Return the document path for the PDF.js viewer
    return jsonify({'path': url_for('static', filename=document.file_path)})

# Document Upload Routes

@app.route('/employee/upload/aadhar', methods=['POST'])
@login_required
def upload_aadhar():
    """Upload Aadhar card document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = AadharUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.AADHAR)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.AADHAR
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.document_number = form.document_number.data
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.AADHAR,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    document_number=form.document_number.data,
                    status='pending'
                )
                db.session.add(document)
                
            # Update employee's Aadhar ID if provided
            if form.document_number.data:
                employee.aadhar_id = form.document_number.data
                
            db.session.commit()
            
            flash('Aadhar card uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/pan', methods=['POST'])
@login_required
def upload_pan():
    """Upload PAN card document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = PANUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.PAN)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.PAN
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.document_number = form.document_number.data
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.PAN,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    document_number=form.document_number.data,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('PAN card uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/photo', methods=['POST'])
@login_required
def upload_photo():
    """Upload photo document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = PhotoUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.PHOTO)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.PHOTO
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.PHOTO,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Photo uploaded successfully', 'success')
        else:
            flash('Failed to upload photo. Please ensure it is a valid image file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/passbook', methods=['POST'])
@login_required
def upload_passbook():
    """Upload bank passbook document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = PassbookUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.PASSBOOK)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.PASSBOOK
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.document_number = form.document_number.data
                existing_doc.bank_name = form.bank_name.data
                existing_doc.ifsc_code = form.ifsc_code.data
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.PASSBOOK,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    document_number=form.document_number.data,
                    bank_name=form.bank_name.data,
                    ifsc_code=form.ifsc_code.data,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Bank passbook uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/joining_form', methods=['POST'])
@login_required
def upload_joining_form():
    """Upload joining form document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = JoiningFormUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.JOINING_FORM)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.JOINING_FORM
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.JOINING_FORM,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Joining Application Form uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid PDF file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/pf_form', methods=['POST'])
@login_required
def upload_pf_form():
    """Upload PF form document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = PFFormUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.PF_FORM)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.PF_FORM
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.PF_FORM,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('PF Form 2 uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid PDF file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/form1', methods=['POST'])
@login_required
def upload_form1():
    """Upload Form 1 document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = Form1UploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.FORM1)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.FORM1
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.FORM1,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Nomination & Declaration Form uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid PDF file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/form11', methods=['POST'])
@login_required
def upload_form11():
    """Upload Form 11 document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = Form11UploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.FORM11)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.FORM11
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.FORM11,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Form 11 uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid PDF file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# News/Update Routes for all users
@app.route('/news')
def news_list():
    """List all active news and updates."""
    # Get active news/updates sorted by most recent first
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.published_date.desc()).all()
    return render_template('news/list.html', news_updates=news_updates)

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    """Show details of a specific news/update."""
    news_update = NewsUpdate.query.get_or_404(news_id)
    return render_template('news/detail.html', news_update=news_update)

# News/Update Management Routes for Employers
@app.route('/employer/news-updates')
@login_required
def employer_news_list():
    """List and manage news/updates created by this employer."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer:
        flash('Employer profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employer_dashboard'))
        
    news_updates = NewsUpdate.query.filter_by(employer_id=employer.id).order_by(NewsUpdate.published_date.desc()).all()
    return render_template('employer/news_list.html', news_updates=news_updates)

@app.route('/employer/news-updates/create', methods=['GET', 'POST'])
@login_required
def create_news_update():
    """Create a new news/update."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer:
        flash('Employer profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employer_dashboard'))
        
    form = NewsUpdateForm()
    if form.validate_on_submit():
        news_update = NewsUpdate(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            employer_id=employer.id
        )
        
        # Only set interview details if this is an interview notice
        if form.is_interview_notice.data:
            news_update.location_address = form.location_address.data
            news_update.interview_date = form.interview_date.data
            
        db.session.add(news_update)
        db.session.commit()
        
        flash('News/Update published successfully', 'success')
        return redirect(url_for('employer_news_list'))
        
    return render_template('employer/create_news.html', form=form)

@app.route('/employer/news-updates/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news_update(news_id):
    """Edit an existing news/update."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer:
        flash('Employer profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employer_dashboard'))
        
    news_update = NewsUpdate.query.get_or_404(news_id)
    
    # Make sure employers can only edit their own updates
    if news_update.employer_id != employer.id:
        abort(403)  # Forbidden
        
    form = NewsUpdateForm(obj=news_update)
    
    # Is this an interview notice?
    is_interview = bool(news_update.location_address or news_update.interview_date)
    form.is_interview_notice.data = is_interview
    
    if form.validate_on_submit():
        form.populate_obj(news_update)
        
        # Only set interview details if this is an interview notice
        if not form.is_interview_notice.data:
            news_update.location_address = None
            news_update.interview_date = None
            
        db.session.commit()
        
        flash('News/Update edited successfully', 'success')
        return redirect(url_for('employer_news_list'))
        
    return render_template('employer/edit_news.html', form=form, news_update=news_update)

@app.route('/employer/news-updates/delete/<int:news_id>', methods=['POST'])
@login_required
def delete_news_update(news_id):
    """Delete a news/update."""
    if not current_user.is_employer():
        abort(403)  # Forbidden
        
    employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer:
        flash('Employer profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employer_dashboard'))
        
    news_update = NewsUpdate.query.get_or_404(news_id)
    
    # Make sure employers can only delete their own updates
    if news_update.employer_id != employer.id:
        abort(403)  # Forbidden
        
    db.session.delete(news_update)
    db.session.commit()
    
    flash('News/Update deleted successfully', 'success')
    return redirect(url_for('employer_news_list'))

# New Document Types Upload Routes
@app.route('/employee/upload/police_verification', methods=['POST'])
@login_required
def upload_police_verification():
    """Upload Police Verification Certificate document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = PoliceVerificationUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.POLICE_VERIFICATION)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.POLICE_VERIFICATION
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.document_number = form.document_number.data
                existing_doc.issue_date = form.issue_date.data
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.POLICE_VERIFICATION,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    document_number=form.document_number.data,
                    issue_date=form.issue_date.data,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Police Verification Certificate uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/medical_certificate', methods=['POST'])
@login_required
def upload_medical_certificate():
    """Upload Medical Certificate document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = MedicalCertificateUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.MEDICAL_CERTIFICATE)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.MEDICAL_CERTIFICATE
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.issue_date = form.issue_date.data
                existing_doc.expiry_date = form.expiry_date.data
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.MEDICAL_CERTIFICATE,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    issue_date=form.issue_date.data,
                    expiry_date=form.expiry_date.data,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Medical Certificate uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

@app.route('/employee/upload/family_details', methods=['POST'])
@login_required
def upload_family_details():
    """Upload Family Details document."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
        
    form = FamilyDetailsUploadForm()
    if form.validate_on_submit():
        # Save the uploaded file
        file_path = save_document(form.document_file.data, current_user.id, DocumentTypes.FAMILY_DETAILS)
        
        if file_path:
            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id, 
                document_type=DocumentTypes.FAMILY_DETAILS
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.document_name = form.document_name.data
                existing_doc.file_path = file_path
                existing_doc.upload_date = datetime.utcnow()
                existing_doc.status = 'pending'
            else:
                # Create a new document record
                document = Document(
                    employee_id=employee.id,
                    document_type=DocumentTypes.FAMILY_DETAILS,
                    document_name=form.document_name.data,
                    file_path=file_path,
                    status='pending'
                )
                db.session.add(document)
                
            db.session.commit()
            
            flash('Family Details document uploaded successfully', 'success')
        else:
            flash('Failed to upload document. Please ensure it is a valid PDF file.', 'error')
            
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'error')
                
    return redirect(url_for('employee_forms'))

# Combined PDF Preview Route
@app.route('/employee/documents/combined-pdf')
@login_required
def generate_combined_pdf_preview():
    """Generate a combined PDF from all employee documents."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    # Get all documents for this employee
    all_documents = Document.query.filter_by(employee_id=employee.id).all()
    
    if not all_documents:
        flash('No documents available to generate combined PDF.', 'warning')
        return redirect(url_for('employee_forms'))
    
    # Generate the combined PDF
    from pdf_utils import generate_combined_pdf, add_metadata_to_combined_pdf
    pdf_buffer = generate_combined_pdf(all_documents)
    
    if not pdf_buffer:
        flash('Error generating combined PDF. Please try again later.', 'error')
        return redirect(url_for('employee_forms'))
    
    # Add metadata to the PDF
    pdf_buffer = add_metadata_to_combined_pdf(pdf_buffer, employee)
    
    # Return the PDF as a response
    from flask import send_file
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'employee_{employee.employee_id}_documents.pdf'
    )

@app.route('/employee/documents/download-zip')
@login_required
def download_documents_zip():
    """Download a ZIP file containing all employee documents."""
    if not current_user.is_employee():
        abort(403)  # Forbidden
        
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('employee_dashboard'))
    
    # Get all documents for this employee
    all_documents = Document.query.filter_by(employee_id=employee.id).all()
    
    if not all_documents:
        flash('No documents available to download.', 'warning')
        return redirect(url_for('employee_forms'))
    
    # Create a ZIP file with all documents
    from pdf_utils import create_documents_zip
    zip_buffer = create_documents_zip(all_documents)
    
    if not zip_buffer:
        flash('Error creating ZIP file. Please try again later.', 'error')
        return redirect(url_for('employee_forms'))
    
    # Return the ZIP file as a response
    from flask import send_file
    return send_file(
        zip_buffer,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'employee_{employee.employee_id}_documents.zip'
    )

# Employer document preview routes
@app.route('/employer/view-employee-documents/<int:employee_id>')
@login_required
def view_employee_documents(employee_id):
    """View all documents for a specific employee."""
    if not (current_user.is_employer() or current_user.is_admin()):
        abort(403)  # Forbidden
    
    employee = EmployeeProfile.query.get_or_404(employee_id)
    documents = Document.query.filter_by(employee_id=employee_id).all()
    
    return render_template(
        'employer/view_employee_documents.html',
        employee=employee,
        documents=documents
    )

@app.route('/employer/employee-combined-pdf/<int:employee_id>')
@login_required
def employer_view_combined_pdf(employee_id):
    """Generate a combined PDF from all employee documents for employer viewing."""
    if not (current_user.is_employer() or current_user.is_admin()):
        abort(403)  # Forbidden
    
    employee = EmployeeProfile.query.get_or_404(employee_id)
    
    # Get all documents for this employee
    all_documents = Document.query.filter_by(employee_id=employee_id).all()
    
    if not all_documents:
        flash('No documents available to generate combined PDF.', 'warning')
        return redirect(url_for('view_employee_documents', employee_id=employee_id))
    
    # Generate the combined PDF
    from pdf_utils import generate_combined_pdf, add_metadata_to_combined_pdf
    pdf_buffer = generate_combined_pdf(all_documents)
    
    if not pdf_buffer:
        flash('Error generating combined PDF. Please try again later.', 'error')
        return redirect(url_for('view_employee_documents', employee_id=employee_id))
    
    # Add metadata to the PDF
    pdf_buffer = add_metadata_to_combined_pdf(pdf_buffer, employee)
    
    # Return the PDF as a response
    from flask import send_file
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'employee_{employee.employee_id}_documents.pdf'
    )

