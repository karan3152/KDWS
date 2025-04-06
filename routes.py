from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
import os
import secrets
import uuid

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, DocumentTypes, PasswordResetToken, FamilyMember, NewsUpdate
from forms import (
    LoginForm, RegisterForm, FirstLoginForm, PasswordResetRequestForm, PasswordResetForm,
    EmployeeProfileForm, EmployeeProfileEditForm, EmployerProfileForm, EmployeeSearchForm,
    CreateEmployeeForm, NewsUpdateForm, DocumentReviewForm
)
from utils import send_password_reset_email


from flask import render_template, redirect, url_for, flash, request, abort, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
import os
import secrets
import uuid

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, DocumentTypes, PasswordResetToken, FamilyMember, NewsUpdate
from forms import (
    LoginForm, RegisterForm, FirstLoginForm, PasswordResetRequestForm, PasswordResetForm,
    EmployeeProfileForm, EmployeeProfileEditForm, EmployerProfileForm, EmployeeSearchForm,
    CreateEmployeeForm, NewsUpdateForm, DocumentReviewForm
)
from utils import send_password_reset_email


# Basic routes
@app.route('/')
def index():
    """Homepage route."""
    # Get active news updates for the login page
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.published_date.desc()).limit(5).all()
    
    return render_template('home.html', news_updates=news_updates)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        
        # Update last login time
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user, remember=form.remember_me.data)
        
        # Check if this is the first login (for employees)
        if user.first_login and user.is_employee():
            return redirect(url_for('first_login'))
        
        # Redirect to the requested page or default dashboard
        next_page = request.args.get('next')
        # Check if next_page is a relative URL
        if not next_page or next_page.startswith('http'):
            if user.is_admin():
                next_page = url_for('admin_dashboard')
            elif user.is_employer():
                next_page = url_for('employer_dashboard')
            else:  # Employee
                next_page = url_for('employee_dashboard')
        
        return redirect(next_page)
    
    # Get active news updates for the login page
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.published_date.desc()).limit(5).all()
    
    return render_template('login.html', form=form, news_updates=news_updates)


@app.route('/first-login', methods=['GET', 'POST'])
@login_required
def first_login():
    """First-time login for employees to verify Aadhar and Employee ID and set a new password."""
    if not current_user.is_employee() or not current_user.first_login:
        return redirect(url_for('index'))
    
    form = FirstLoginForm()
    if form.validate_on_submit():
        # Get the employee profile
        employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        
        if not employee:
            flash('Employee profile not found. Please contact administrator.', 'error')
            return redirect(url_for('first_login'))
        
        # Verify Aadhar and Employee ID
        if employee.aadhar_id != form.aadhar_id.data or employee.employee_id != form.employee_id.data:
            flash('Verification failed. Please check your Aadhar and Employee ID.', 'error')
            return redirect(url_for('first_login'))
        
        # Update password and first login status
        current_user.set_password(form.new_password.data)
        current_user.first_login = False
        db.session.commit()
        
        flash('Password set successfully! You can now access your account.', 'success')
        return redirect(url_for('employee_dashboard'))
    
    return render_template('first_login.html', form=form)


@app.route('/logout')
def logout():
    """User logout route."""
    logout_user()
    return redirect(url_for('index'))


@app.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """Request a password reset."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # Generate token and send email
            token = PasswordResetToken.generate_token(user.id)
            db.session.add(token)
            db.session.commit()
            
            send_password_reset_email(user, token.token)
        
        # Always show success message to prevent email enumeration
        flash('Check your email for the instructions to reset your password', 'info')
        return redirect(url_for('login'))
    
    return render_template('password_reset_request.html', form=form)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with a valid token."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Find the token
    token_obj = PasswordResetToken.query.filter_by(token=token).first()
    
    if not token_obj or token_obj.is_expired():
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('reset_password_request'))
    
    user = User.query.get(token_obj.user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('reset_password_request'))
    
    form = PasswordResetForm()
    if form.validate_on_submit():
        # Update password
        user.set_password(form.password.data)
        
        # Remove all tokens for this user
        PasswordResetToken.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        flash('Your password has been reset.', 'success')
        return redirect(url_for('login'))
    
    return render_template('password_reset_confirm.html', form=form)


# Dashboard routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard route."""
    if not current_user.is_admin():
        flash('Access denied. This page is for admin users only.', 'error')
        return redirect(url_for('index'))
    
    # Get counts for summary
    employee_count = User.query.filter_by(role='employee').count()
    employer_count = User.query.filter_by(role='employer').count()
    document_count = Document.query.count()
    pending_documents = Document.query.filter_by(status='pending').count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                           employee_count=employee_count,
                           employer_count=employer_count,
                           document_count=document_count,
                           pending_documents=pending_documents,
                           recent_users=recent_users)


@app.route('/employer/dashboard')
@login_required
def employer_dashboard():
    """Employer dashboard route."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This page is for employers and admin users only.', 'error')
        return redirect(url_for('index'))
    
    # Get employer profile
    employer_profile = None
    if current_user.is_employer():
        employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    
    # Get counts for summary
    employee_count = User.query.filter_by(role='employee').count()
    pending_documents = Document.query.filter_by(status='pending').count()
    
    # Get recent documents
    recent_documents = Document.query.order_by(Document.uploaded_at.desc()).limit(10).all()
    
    # Get recent news updates by this employer
    if employer_profile:
        news_updates = NewsUpdate.query.filter_by(employer_id=employer_profile.id).order_by(NewsUpdate.published_date.desc()).limit(5).all()
    else:
        news_updates = NewsUpdate.query.order_by(NewsUpdate.published_date.desc()).limit(5).all()
    
    return render_template('employer/dashboard.html', 
                           employer=employer_profile,
                           employee_count=employee_count,
                           pending_documents=pending_documents,
                           news_updates=news_updates,
                           recent_documents=recent_documents)


@app.route('/employee/dashboard')
@login_required
def employee_dashboard():
    """Employee dashboard route."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    # Get employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    # Get document counts
    total_documents = len(DocumentTypes.all_types())
    submitted_documents = Document.query.filter_by(employee_id=employee.id).count()
    approved_documents = Document.query.filter_by(employee_id=employee.id, status='approved').count()
    pending_documents = Document.query.filter_by(employee_id=employee.id, status='pending').count()
    
    # Calculate completion percentage
    from utils import get_document_completion_percentage
    completion_percentage = get_document_completion_percentage(employee.id)
    
    # Get recent news updates
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.published_date.desc()).limit(5).all()
    
    # Get the employee's documents
    documents = Document.query.filter_by(employee_id=employee.id).all()
    
    return render_template('employee/dashboard.html', 
                           employee=employee,
                           total_documents=total_documents,
                           submitted_documents=submitted_documents,
                           approved_documents=approved_documents,
                           pending_documents=pending_documents,
                           completion_percentage=completion_percentage,
                           news_updates=news_updates,
                           documents=documents)


# Profile routes
@app.route('/profile')
@login_required
def profile():
    """User profile route - redirects to the appropriate profile page based on role."""
    if current_user.is_admin():
        return redirect(url_for('admin_profile'))
    elif current_user.is_employer():
        return redirect(url_for('employer_profile_page'))
    else:  # Employee
        return redirect(url_for('employee_profile_page'))


@app.route('/admin/profile')
@login_required
def admin_profile():
    """Admin profile page."""
    if not current_user.is_admin():
        flash('Access denied. This page is for admin users only.', 'error')
        return redirect(url_for('index'))
    
    return render_template('admin/profile.html')


@app.route('/employer/profile', methods=['GET', 'POST'])
@app.route('/employer/profile/<int:employer_id>', methods=['GET', 'POST'])
@login_required
def employer_profile_page(employer_id=None):
    """Employer profile page with edit form."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This page is for employers and admins only.', 'error')
        return redirect(url_for('index'))
    
    # Get employer profile
    if employer_id and current_user.is_admin():
        employer = EmployerProfile.query.get_or_404(employer_id)
        user = User.query.get(employer.user_id)
    else:
        employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
        user = current_user
        
    if not employer:
        flash('Employer profile not found.', 'error')
        return redirect(url_for('index'))
    
    form = EmployerProfileForm()
    if form.validate_on_submit():
        # Update profile
        employer.company_name = form.company_name.data
        employer.department = form.department.data
        employer.contact_number = form.contact_number.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('employer_profile_page'))
    elif request.method == 'GET':
        # Populate form with current data
        form.company_name.data = employer.company_name
        form.department.data = employer.department
        form.contact_number.data = employer.contact_number
    
    return render_template('employer/profile.html', form=form, employer=employer)


@app.route('/employee/profile', methods=['GET', 'POST'])
@login_required
def employee_profile_page():
    """Employee profile page with edit form."""
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'error')
        return redirect(url_for('index'))
    
    # Get employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Employee profile not found. Please contact administrator.', 'error')
        return redirect(url_for('index'))
    
    form = EmployeeProfileForm()
    if form.validate_on_submit():
        # Update profile
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.date_of_birth = form.date_of_birth.data
        employee.phone_number = form.phone_number.data
        employee.address = form.address.data
        employee.department = form.department.data
        employee.position = form.position.data
        employee.joining_date = form.joining_date.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('employee_profile_page'))
    elif request.method == 'GET':
        # Populate form with current data
        form.first_name.data = employee.first_name
        form.last_name.data = employee.last_name
        form.date_of_birth.data = employee.date_of_birth
        form.phone_number.data = employee.phone_number
        form.address.data = employee.address
        form.department.data = employee.department
        form.position.data = employee.position
        form.joining_date.data = employee.joining_date
    
    return render_template('employee/profile.html', form=form, employee=employee)


@app.route('/employee/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    """Edit employee profile (for admin/employer)."""
    if not current_user.is_admin() and not current_user.is_employer():
        flash('Access denied. This page is for admin and employer users only.', 'error')
        return redirect(url_for('index'))
    
    # Get employee profile
    employee = EmployeeProfile.query.get_or_404(employee_id)
    user = User.query.get(employee.user_id)
    
    form = EmployeeProfileEditForm()
    if form.validate_on_submit():
        # Update user
        user.email = form.email.data
        
        # Update profile
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.date_of_birth = form.date_of_birth.data
        employee.phone_number = form.phone_number.data
        employee.address = form.address.data
        employee.department = form.department.data
        employee.position = form.position.data
        employee.joining_date = form.joining_date.data
        
        # Only admin can change Aadhar/Employee ID
        if current_user.is_admin():
            employee.aadhar_id = form.aadhar_id.data
            employee.employee_id = form.employee_id.data
        
        db.session.commit()
        flash('Employee profile updated successfully!', 'success')
        return redirect(url_for('employer_view_employee', employee_id=employee.employee_id))
    elif request.method == 'GET':
        # Populate form with current data
        form.first_name.data = employee.first_name
        form.last_name.data = employee.last_name
        form.date_of_birth.data = employee.date_of_birth
        form.phone_number.data = employee.phone_number
        form.address.data = employee.address
        form.department.data = employee.department
        form.position.data = employee.position
        form.joining_date.data = employee.joining_date
        form.aadhar_id.data = employee.aadhar_id
        form.employee_id.data = employee.employee_id
        form.email.data = user.email
    
    return render_template('profile_edit.html', form=form, employee=employee, user=user)


# Document routes
@app.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View a document."""
    document = Document.query.get_or_404(document_id)
    
    # Check access permission
    if current_user.is_employee():
        # Employees can only view their own documents
        employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee or document.employee_id != employee.id:
            flash('Access denied. You can only view your own documents.', 'error')
            return redirect(url_for('document_center'))
    
    # Construct path to the document
    document_path = os.path.join(app.root_path, document.file_path)
    
    # Determine content type from file extension
    _, ext = os.path.splitext(document_path)
    content_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png'
    }
    content_type = content_types.get(ext.lower(), 'application/octet-stream')
    
    # Serve the file
    return send_file(document_path, mimetype=content_type)


@app.route('/document/review/<int:document_id>', methods=['GET', 'POST'])
@login_required
def review_document(document_id):
    """Review a document (for employers)."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This page is for employers and admin users only.', 'error')
        return redirect(url_for('index'))
    
    document = Document.query.get_or_404(document_id)
    employee = EmployeeProfile.query.get(document.employee_id)
    
    form = DocumentReviewForm()
    if form.validate_on_submit():
        # Update document status
        document.status = form.status.data
        document.feedback = form.feedback.data
        document.approval_date = datetime.utcnow() if form.status.data == 'approved' else None
        document.approved_by = current_user.id if form.status.data == 'approved' else None
        
        db.session.commit()
        flash(f'Document status updated to {form.status.data.title()}.', 'success')
        return redirect(url_for('employer_view_employee', employee_id=employee.employee_id))
    else:
        # Populate form with current data
        form.status.data = document.status
        form.feedback.data = document.feedback
    
    return render_template('document_review.html', form=form, document=document, employee=employee)


# News/Updates routes
@app.route('/news/create', methods=['GET', 'POST'])
@login_required
def create_news():
    """Create a new news update (for employers and admin)."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This page is for employers and admin users only.', 'error')
        return redirect(url_for('index'))
    
    form = NewsUpdateForm()
    if form.validate_on_submit():
        # Get employer profile for current user (if employer)
        employer_id = None
        if current_user.is_employer():
            employer = EmployerProfile.query.filter_by(user_id=current_user.id).first()
            if employer:
                employer_id = employer.id
        
        # Create news update
        news = NewsUpdate(
            title=form.title.data,
            content=form.content.data,
            is_active=form.is_active.data,
            is_interview_notice=form.is_interview_notice.data,
            employer_id=employer_id,
            link=form.link.data,
            link_text=form.link_text.data
        )
        
        # Set additional fields if this is an interview notice
        if form.is_interview_notice.data:
            news.location_address = form.location_address.data
            news.interview_date = form.interview_date.data
        
        db.session.add(news)
        db.session.commit()
        
        flash('News update created successfully!', 'success')
        return redirect(url_for('employer_dashboard'))
    
    return render_template('create_news.html', form=form)