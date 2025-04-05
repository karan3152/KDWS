from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import urlsplit
from datetime import datetime

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, PasswordResetToken, ROLE_ADMIN, ROLE_EMPLOYER, ROLE_EMPLOYEE
from forms import (
    LoginForm, PasswordResetRequestForm, PasswordResetForm, FirstLoginForm,
    CreateEmployeeForm, CreateEmployerForm, EmployeeProfileForm,
    EmployeeSearchForm, DocumentUploadForm
)
from utils import (
    generate_reset_token, get_token_expiry, save_pdf,
    extract_pdf_data, validate_login_identifier
)

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
            return render_template('login.html', form=form)
            
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
        
    return render_template('login.html', form=form)

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
        
    form = DocumentUploadForm()
    
    if form.validate_on_submit():
        # Save the uploaded PDF
        file_path = save_pdf(request.files['document_file'], current_user.id)
        
        if file_path:
            # Create a new document record
            document = Document(
                employee_id=employee.id,
                document_type=form.document_type.data,
                document_name=form.document_name.data,
                file_path=file_path,
                status='pending'
            )
            db.session.add(document)
            db.session.commit()
            
            flash('Document uploaded successfully', 'success')
            return redirect(url_for('employee_forms'))
        else:
            flash('Failed to upload document. Please ensure it is a valid PDF file.', 'error')
            
    # Get existing documents
    documents = Document.query.filter_by(employee_id=employee.id).all()
    
    return render_template('employee/forms.html', form=form, documents=documents)

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
