from flask import render_template, redirect, url_for, flash, request, current_app, send_file, abort, jsonify, session
from flask_login import login_required, current_user, login_user, logout_user
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone
import os
import zipfile
import io
import shutil
import random
import string
import uuid
import pandas as pd

from extensions import db
from models import User, EmployeeProfile, EmployerProfile, NewsUpdate, Document, FamilyMember, DocumentTypes, Image, Client
from models import ROLE_ADMIN, ROLE_EMPLOYER, ROLE_EMPLOYEE  # Add role constants
from utils.path_utils import normalize_path, get_full_path
from forms import (
    LoginForm, RegistrationForm, EmployeeProfileForm, EmployerProfileForm,
    FamilyMemberForm, DocumentUploadForm, JoiningForm, EmployeeSearchForm, NewsUpdateForm
)
from blueprints import main
from extensions import csrf

@main.route('/news/<int:news_id>')
@login_required
def news_detail(news_id):
    """News detail route."""
    news_update = NewsUpdate.query.get_or_404(news_id)
    return render_template('news/detail.html', news_update=news_update)

@main.route('/employee/profile/<int:employee_id>')
@login_required
def view_employee_profile(employee_id):
    """View employee profile route."""
    employee = EmployeeProfile.query.get_or_404(employee_id)

    # Get family members data if available
    family_members = FamilyMember.query.filter_by(employee_id=employee.id).all()

    return render_template('employee/profile_view.html', employee=employee, family_members=family_members)

@main.route('/', methods=['GET', 'POST'])
def index():
    """Home page route."""
    if current_user.is_authenticated:
        if current_user.is_employer():
            return redirect(url_for('main.employer_dashboard'))
        elif current_user.is_employee():
            return redirect(url_for('main.employee_dashboard'))
        elif current_user.is_admin():
            return redirect(url_for('main.admin_dashboard'))

    # Get news updates
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.created_at.desc()).all()

    # Handle login form
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.now()
            db.session.commit()

            next_page = request.args.get('next')
            if not next_page or urlparse(next_page).netloc != '':
                if user.is_employer():
                    next_page = url_for('main.employer_dashboard')
                elif user.is_employee():
                    next_page = url_for('main.employee_dashboard')
                elif user.is_admin():
                    next_page = url_for('main.admin_dashboard')
                else:
                    next_page = url_for('main.index')
            return redirect(next_page)
        else:
            flash('Invalid email or password', 'danger')

    return render_template('home.html', news_updates=news_updates, form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    """Login route."""
    if current_user.is_authenticated:
        if current_user.is_employer():
            return redirect(url_for('main.employer_dashboard'))
        elif current_user.is_employee():
            return redirect(url_for('main.employee_dashboard'))
        elif current_user.is_admin():
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.index'))

    # Fetch latest images for slideshow
    latest_images = Image.query.order_by(Image.upload_date.desc()).limit(10).all()

    # Fetch active news updates from both employers and admins
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.created_at.desc()).limit(5).all()

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_employer():
                return redirect(url_for('main.employer_dashboard'))
            elif user.is_employee():
                return redirect(url_for('main.employee_dashboard'))
            elif user.is_admin():
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.index'))
        flash('Invalid email or password', 'danger')

    # Use the login.html template directly instead of auth/login.html
    return render_template('login.html', form=form, latest_images=latest_images, news_updates=news_updates)

@main.route('/register', methods=['GET', 'POST'])
def register():
    """Registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.email.data.split('@')[0],  # Generate username from email
            email=form.email.data,
            role=form.role.data
        )
        user.set_password(form.password.data)
        db.session.add(user)

        # Create corresponding profile
        if user.role == ROLE_EMPLOYER:
            profile = EmployerProfile(user=user)
            db.session.add(profile)
        elif user.role == ROLE_EMPLOYEE:
            profile = EmployeeProfile(user=user)
            db.session.add(profile)

        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('auth/register.html', form=form)

@main.route('/logout')
@login_required
def logout():
    """Logout route."""
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/extend-session', methods=['POST'])
@login_required
def extend_session():
    """Extend the user's session."""
    # Only allow employees to extend their session
    if current_user.is_employee():
        # Update the session expiry time
        session.modified = True
        # Update the last_login time in the database
        current_user.last_login = datetime.now()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Session extended successfully'})
    return jsonify({'status': 'error', 'message': 'Only employees can extend their session'}), 403

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile route."""
    if current_user.is_employer():
        form = EmployerProfileForm()
        profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()

        if request.method == 'GET' and profile:
            form.company_name.data = profile.company_name
            form.company_address.data = profile.company_address
            form.company_phone.data = profile.company_phone
            form.company_email.data = profile.company_email
            form.industry.data = profile.industry
            form.company_size.data = profile.company_size
            form.company_website.data = profile.company_website
            form.department.data = profile.department

        if form.validate_on_submit():
            if not profile:
                profile = EmployerProfile(user_id=current_user.id)
                db.session.add(profile)

            profile.company_name = form.company_name.data
            profile.company_address = form.company_address.data
            profile.company_phone = form.company_phone.data
            profile.company_email = form.company_email.data
            profile.industry = form.industry.data
            profile.company_size = form.company_size.data
            profile.company_website = form.company_website.data
            profile.department = form.department.data

            if form.photo.data:
                # Generate unique filename with timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"employer_{current_user.id}_{timestamp}_{secure_filename(form.photo.data.filename)}"

                # Create directory for profile photos
                upload_dir = os.path.join('uploads', 'profile_photos')
                os.makedirs(os.path.join(current_app.root_path, 'static', upload_dir), exist_ok=True)

                # Save the file
                filepath = os.path.join(current_app.root_path, 'static', upload_dir, filename)
                form.photo.data.save(filepath)

                # Store the relative path in the database (for url_for)
                profile.photo_path = os.path.join(upload_dir, filename)

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.employer_dashboard'))

        return render_template('employer/profile.html', form=form)

    elif current_user.is_employee():
        form = EmployeeProfileForm()
        profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()

        if request.method == 'GET' and profile:
            form.first_name.data = profile.first_name
            form.last_name.data = profile.last_name
            form.date_of_birth.data = profile.date_of_birth
            # form.gender.data = profile.gender
            form.phone_number.data = profile.phone_number
            form.address.data = profile.address
            # form.emergency_contact_name.data = profile.emergency_contact_name
            # form.emergency_contact_phone.data = profile.emergency_contact_phone
            form.position.data = profile.position
            form.department.data = profile.department
            form.joining_date.data = profile.hire_date
            # form.employment_status.data = profile.employment_status
            # form.bank_account.data = profile.bank_account
            # form.tax_id.data = profile.tax_id

        if form.validate_on_submit():
            if not profile:
                profile = EmployeeProfile(user_id=current_user.id)
                db.session.add(profile)

            profile.first_name = form.first_name.data
            profile.last_name = form.last_name.data
            profile.date_of_birth = form.date_of_birth.data
            # profile.gender = form.gender.data
            profile.phone_number = form.phone_number.data
            profile.address = form.address.data
            # profile.emergency_contact_name = form.emergency_contact_name.data
            # profile.emergency_contact_phone = form.emergency_contact_phone.data
            profile.position = form.position.data
            profile.department = form.department.data
            profile.hire_date = form.joining_date.data
            # profile.employment_status = form.employment_status.data
            # profile.bank_account = form.bank_account.data
            # profile.tax_id = form.tax_id.data

            if form.photo.data:
                # Generate unique filename with timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"profile_{current_user.id}_{timestamp}_{secure_filename(form.photo.data.filename)}"

                # Create directory for profile photos
                upload_dir = os.path.join('uploads', 'profile_photos')
                os.makedirs(os.path.join(current_app.root_path, 'static', upload_dir), exist_ok=True)

                # Save the file
                filepath = os.path.join(current_app.root_path, 'static', upload_dir, filename)
                form.photo.data.save(filepath)

                # Store the relative path in the database (for url_for)
                profile.photo_path = os.path.join(upload_dir, filename)

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.employee_dashboard'))

        return render_template('employee/profile.html', form=form, employee=profile)

    flash('Invalid user role', 'danger')
    return redirect(url_for('main.index'))

@main.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get statistics for the dashboard
    total_employees = EmployeeProfile.query.count()
    total_employers = EmployerProfile.query.count()
    pending_documents = Document.query.filter_by(status='pending').count()

    # Get all active clients for the dropdown
    try:
        clients = Client.query.filter_by(is_active=True).all()
        total_clients = len(clients)
    except Exception as e:
        # Check if the client table exists
        try:
            # Try to create the client table if it doesn't exist
            from migrations.add_client_columns import run_migration
            run_migration()
            # Try again to get clients
            clients = Client.query.filter_by(is_active=True).all()
            total_clients = len(clients)
            flash("Client management is now available. Database has been updated.", "success")
        except Exception as inner_e:
            current_app.logger.error(f"Error creating client table: {str(inner_e)}")
            clients = []
            total_clients = 0

    return render_template('admin/dashboard.html',
                         total_employees=total_employees,
                         total_employers=total_employers,
                         pending_documents=pending_documents,
                         total_clients=total_clients,
                         clients=clients)

@main.route('/admin/news')
@login_required
def admin_news():
    """Admin news management route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all news updates
    news_updates = NewsUpdate.query.filter_by(created_by=current_user.id).order_by(NewsUpdate.created_at.desc()).all()
    return render_template('admin/news_list.html', news_updates=news_updates)

@main.route('/admin/news/create', methods=['GET', 'POST'])
@login_required
def admin_create_news():
    """Admin create news update route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Create form
    form = NewsUpdateForm()

    if form.validate_on_submit():
        # Create new news update
        news_update = NewsUpdate(
            title=form.title.data,
            content=form.content.data,
            created_by=current_user.id,
            is_active=form.is_active.data
        )
        db.session.add(news_update)
        db.session.commit()

        flash('News update created successfully!', 'success')
        return redirect(url_for('main.admin_news'))

    return render_template('admin/create_news.html', form=form)

@main.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_news(news_id):
    """Admin edit news update route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the news update
    news_update = NewsUpdate.query.get_or_404(news_id)

    # Check if the current user is the creator
    if news_update.created_by != current_user.id:
        flash('Access denied. You can only edit your own news updates.', 'danger')
        return redirect(url_for('main.admin_news'))

    # Create form and populate with existing data
    form = NewsUpdateForm(obj=news_update)

    if form.validate_on_submit():
        # Update news update
        news_update.title = form.title.data
        news_update.content = form.content.data
        news_update.is_active = form.is_active.data
        news_update.updated_at = datetime.utcnow()
        db.session.commit()

        flash('News update updated successfully!', 'success')
        return redirect(url_for('main.admin_news'))

    return render_template('admin/edit_news.html', form=form, news=news_update)

@main.route('/admin/news/delete/<int:news_id>', methods=['POST'])
@login_required
def admin_delete_news(news_id):
    """Admin delete news update route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the news update
    news_update = NewsUpdate.query.get_or_404(news_id)

    # Check if the current user is the creator
    if news_update.created_by != current_user.id:
        flash('Access denied. You can only delete your own news updates.', 'danger')
        return redirect(url_for('main.admin_news'))

    # Delete the news update
    db.session.delete(news_update)
    db.session.commit()

    flash('News update deleted successfully!', 'success')
    return redirect(url_for('main.admin_news'))

@main.route('/employee/dashboard')
@login_required
def employee_dashboard():
    if not current_user.is_employee():
        flash('Access denied. This page is for employees only.', 'danger')
        return redirect(url_for('main.index'))

    profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    documents = Document.query.filter_by(user_id=current_user.id).all()

    if not profile:
        flash('Please complete your profile to access the dashboard.', 'warning')
        return redirect(url_for('main.profile'))

    # Create a dictionary with all the fields the template expects
    employee_data = {
        'first_name': profile.first_name,
        'last_name': profile.last_name,
        'position': profile.position,
        'department': profile.department,
        'employee_id': f"EMP{profile.id:06d}",  # Generate a formatted employee ID
        'phone_number': profile.phone_number,
        'joining_date': profile.hire_date  # Map hire_date to joining_date
    }

    return render_template('employee/dashboard.html',
                         employee=employee_data,
                         documents=documents)

@main.route('/employer/dashboard')
@login_required
def employer_dashboard():
    """Employer dashboard route."""
    if not current_user.is_employer():
        abort(403)

    # Get employer profile
    profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Please complete your employer profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Get employee count
    employee_count = EmployeeProfile.query.count()  # In a real app, this would be filtered by company

    # Get recent documents
    recent_documents = Document.query.order_by(Document.uploaded_at.desc()).limit(5).all()

    # Get active news updates
    news_updates = NewsUpdate.query.filter_by(is_active=True).order_by(NewsUpdate.created_at.desc()).limit(5).all()

    # Get all active clients for the dropdown
    try:
        clients = Client.query.filter_by(is_active=True).all()
        total_clients = len(clients)
    except Exception as e:
        # Check if the client table exists
        try:
            # Try to create the client table if it doesn't exist
            from migrations.add_client_columns import run_migration
            run_migration()
            # Try again to get clients
            clients = Client.query.filter_by(is_active=True).all()
            total_clients = len(clients)
            flash("Client management is now available. Database has been updated.", "success")
        except Exception as inner_e:
            current_app.logger.error(f"Error creating client table: {str(inner_e)}")
            clients = []
            total_clients = 0

    return render_template('employer/dashboard.html',
                         profile=profile,
                         employee_count=employee_count,
                         recent_documents=recent_documents,
                         news_updates=news_updates,
                         total_clients=total_clients,
                         clients=clients)

@main.route('/admin/employees')
@login_required
def admin_employees():
    """Admin employees management route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all users with employee role and eager load the employee_profile and client relationships
    employees = User.query.filter_by(role='employee').all()

    # Ensure client relationships are loaded
    for employee in employees:
        if hasattr(employee, 'employee_profile') and employee.employee_profile and employee.employee_profile.client_id:
            # Access the client to ensure it's loaded
            try:
                client = Client.query.get(employee.employee_profile.client_id)
                if client:
                    employee.employee_profile.client = client
            except Exception as e:
                current_app.logger.error(f"Error loading client for employee {employee.id}: {str(e)}")

    # Get all active clients for the dropdown
    try:
        clients = Client.query.filter_by(is_active=True).all()
    except Exception as e:
        # Check if the client table exists
        try:
            # Try to create the client table if it doesn't exist
            from migrations.add_client_columns import run_migration
            run_migration()
            # Try again to get clients
            clients = Client.query.filter_by(is_active=True).all()
            flash("Client management is now available. Database has been updated.", "success")
        except Exception as inner_e:
            current_app.logger.error(f"Error creating client table: {str(inner_e)}")
            clients = []

    return render_template('admin/employees.html', employees=employees, clients=clients)

@main.route('/admin/employers')
@login_required
def admin_employers():
    """Admin employers management route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all users with employer role
    employers = User.query.filter_by(role='employer').all()
    return render_template('admin/employers.html', employers=employers)

@main.route('/admin/documents')
@login_required
def admin_documents():
    """Admin documents management route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    documents = Document.query.all()
    return render_template('admin/documents.html', documents=documents)

@main.route('/admin/view-document/<int:document_id>')
@login_required
def admin_view_document(document_id):
    """View a document."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    document = Document.query.get_or_404(document_id)

    # Redirect to the common view_document route
    return redirect(url_for('main.view_document', document_id=document_id))

@main.route('/admin/approve-document/<int:document_id>')
@login_required
def admin_approve_document(document_id):
    """Approve a document."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    document = Document.query.get_or_404(document_id)
    document.status = 'approved'
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.utcnow()
    db.session.commit()

    flash(f'Document {document.document_type} has been approved.', 'success')

    # Get the employee ID to redirect back to the employee documents page
    employee = None
    if document.employee_id:
        employee = EmployeeProfile.query.get(document.employee_id)
    elif document.user_id:
        user = User.query.get(document.user_id)
        if user and user.role == 'employee':
            employee = EmployeeProfile.query.filter_by(user_id=user.id).first()

    if employee and employee.user_id:
        return redirect(url_for('main.admin_employee_documents', user_id=employee.user_id))
    else:
        # Fallback to the documents list
        return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/reject-document/<int:document_id>')
@login_required
def admin_reject_document(document_id):
    """Reject a document."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    document = Document.query.get_or_404(document_id)
    document.status = 'rejected'
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.utcnow()
    db.session.commit()

    flash(f'Document {document.document_type} has been rejected.', 'success')

    # Get the employee ID to redirect back to the employee documents page
    employee = None
    if document.employee_id:
        employee = EmployeeProfile.query.get(document.employee_id)
    elif document.user_id:
        user = User.query.get(document.user_id)
        if user and user.role == 'employee':
            employee = EmployeeProfile.query.filter_by(user_id=user.id).first()

    if employee and employee.user_id:
        return redirect(url_for('main.admin_employee_documents', user_id=employee.user_id))
    else:
        # Fallback to the documents list
        return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/clients')
@login_required
def admin_clients():
    """Admin clients management route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all clients
    try:
        clients = Client.query.all()

        # Load employee counts for each client
        for client in clients:
            # Add a property to store the employees
            client.employees = EmployeeProfile.query.filter_by(client_id=client.id).all()
    except Exception as e:
        # Try to create the client table if it doesn't exist
        try:
            from migrations.add_client_columns import run_migration
            run_migration()
            # Try again to get clients
            clients = Client.query.all()

            # Load employee counts for each client
            for client in clients:
                # Add a property to store the employees
                client.employees = EmployeeProfile.query.filter_by(client_id=client.id).all()

            flash("Client management is now available. Database has been updated.", "success")
        except Exception as inner_e:
            current_app.logger.error(f"Error creating client table: {str(inner_e)}")
            clients = []
            flash("Client management is not available. Please contact the administrator.", "warning")

    return render_template('admin/clients.html', clients=clients)

@main.route('/admin/add-client', methods=['POST'])
@login_required
def admin_add_client():
    """Add a new client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code', '').upper()
        description = request.form.get('description', '')
        contact_person = request.form.get('contact_person', '')
        contact_email = request.form.get('contact_email', '')
        contact_phone = request.form.get('contact_phone', '')
        is_active = 'is_active' in request.form

        # Check if code already exists
        existing_client = Client.query.filter_by(code=code).first()
        if existing_client:
            flash(f'Client code "{code}" already exists. Please use a different code.', 'danger')
            return redirect(url_for('main.admin_clients'))

        # Create new client
        client = Client(
            name=name,
            code=code,
            description=description,
            contact_person=contact_person,
            contact_email=contact_email,
            contact_phone=contact_phone,
            is_active=is_active,
            created_by=current_user.id
        )
        db.session.add(client)
        db.session.commit()

        flash(f'Client "{name}" added successfully!', 'success')
        return redirect(url_for('main.admin_clients'))

    return redirect(url_for('main.admin_clients'))

@main.route('/admin/edit-client/<int:client_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_client(client_id):
    """Edit a client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)

    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code', '').upper()
        description = request.form.get('description', '')
        contact_person = request.form.get('contact_person', '')
        contact_email = request.form.get('contact_email', '')
        contact_phone = request.form.get('contact_phone', '')
        is_active = 'is_active' in request.form

        # Check if code already exists and is not this client's code
        if code != client.code:
            existing_client = Client.query.filter_by(code=code).first()
            if existing_client:
                flash(f'Client code "{code}" already exists. Please use a different code.', 'danger')
                return render_template('admin/edit_client.html', client=client)

        # Update client
        client.name = name
        client.code = code
        client.description = description
        client.contact_person = contact_person
        client.contact_email = contact_email
        client.contact_phone = contact_phone
        client.is_active = is_active

        db.session.commit()

        flash(f'Client "{name}" updated successfully!', 'success')
        return redirect(url_for('main.admin_clients'))

    return render_template('admin/edit_client.html', client=client)

@main.route('/admin/toggle-client-status/<int:client_id>')
@login_required
def admin_toggle_client_status(client_id):
    """Toggle client active status."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)

    # Toggle the status
    client.is_active = not client.is_active
    db.session.commit()

    status = "activated" if client.is_active else "deactivated"
    flash(f'Client "{client.name}" {status} successfully!', 'success')
    return redirect(url_for('main.admin_clients'))

@main.route('/admin/delete-client/<int:client_id>', methods=['POST'])
@login_required
def admin_delete_client(client_id):
    """Delete a client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)

    # Update all employees with this client to have no client
    employees = EmployeeProfile.query.filter_by(client_id=client_id).all()
    for employee in employees:
        employee.client_id = None

    # Delete the client
    db.session.delete(client)
    db.session.commit()

    flash(f'Client "{client.name}" deleted successfully!', 'success')
    return redirect(url_for('main.admin_clients'))

@main.route('/admin/client/<int:client_id>/employees')
@login_required
def admin_client_employees(client_id):
    """View employees for a specific client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)

    # Get all employee profiles for this client
    employee_profiles = EmployeeProfile.query.filter_by(client_id=client_id).all()

    # Ensure user relationships are loaded
    for profile in employee_profiles:
        if profile.user_id:
            user = User.query.get(profile.user_id)
            if user:
                profile.user = user

    return render_template('admin/client_employees.html', client=client, employees=employee_profiles)

@main.route('/admin/add-employee', methods=['GET', 'POST'])
@main.route('/admin/add-employee/<int:client_id>', methods=['GET', 'POST'])
@login_required
def admin_add_employee(client_id=None):
    """Add a new employee."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all active clients for the dropdown
    try:
        clients = Client.query.filter_by(is_active=True).all()

        # If no clients exist, we'll still allow adding employees but with a warning
        if not clients:
            flash('No clients/projects exist yet. You can create one first or add an employee without a client.', 'warning')
    except Exception as e:
        # Check if the client table exists
        try:
            # Try to create the client table if it doesn't exist
            from migrations.add_client_columns import run_migration
            run_migration()
            # Try again to get clients
            clients = Client.query.filter_by(is_active=True).all()
            flash("Client management is now available. Database has been updated.", "success")
        except Exception as inner_e:
            current_app.logger.error(f"Error creating client table: {str(inner_e)}")
            clients = []
            flash("Client management is not available. Please contact the administrator.", "warning")

    if request.method == 'POST':
        # Check if username already exists
        username = request.form['username']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # Generate a unique username by adding a random suffix
            base_username = username
            username = f"{base_username}_{uuid.uuid4().hex[:6]}"
            flash(f'Username "{base_username}" already exists. Using "{username}" instead.', 'warning')

        # Check if email already exists
        email = request.form['email']
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(f'Email "{email}" is already registered.', 'danger')
            return redirect(url_for('main.admin_add_employee'))

        # Get client information
        client_name = request.form.get('client_name')
        client_code = request.form.get('client_code')

        if not client_name or not client_code:
            flash('Client/Project name and code are required.', 'danger')
            return render_template('admin/add_employee.html', clients=clients)

        # Check if client already exists
        client = Client.query.filter_by(code=client_code).first()

        if not client:
            # Create a new client
            client = Client(
                name=client_name,
                code=client_code.upper(),
                created_by=current_user.id,
                is_active=True
            )
            db.session.add(client)
            db.session.commit()
            flash(f'New client "{client_name}" with code "{client_code.upper()}" created.', 'success')

        # Generate a random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create user
        user = User(
            username=username,
            email=email,
            role='employee',
            is_active=True,
            first_login=True,
            is_temporary_password=True
        )
        user.set_password(password, is_temporary=True)
        db.session.add(user)
        db.session.commit()

        # Generate employee code
        employee_code_suffix = request.form.get('employee_code_suffix', '')
        if employee_code_suffix:
            # Use the provided suffix
            employee_code = f"{client.code}{employee_code_suffix}"
        else:
            # Generate a unique code
            from blueprints.client_routes import generate_employee_code
            employee_code = generate_employee_code(client.code)

        # Create employee profile
        profile = EmployeeProfile(
            user_id=user.id,
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            phone_number=request.form.get('phone_number', ''),
            department=request.form.get('department', ''),
            position=request.form.get('position', ''),
            client_id=client.id,
            employee_code=employee_code
        )
        db.session.add(profile)
        db.session.commit()

        flash(f'Employee added successfully! Username: {user.username}, Password: {password}, Employee Code: {employee_code}', 'success')

        # Redirect based on where the request came from
        if client_id and request.args.get('from') == 'client':
            return redirect(url_for('main.admin_client_employees', client_id=client_id))
        else:
            return redirect(url_for('main.admin_employees'))

    return render_template('admin/add_employee.html', clients=clients, client_id=client_id)

@main.route('/admin/add-employer', methods=['GET', 'POST'])
@login_required
def admin_add_employer():
    """Add a new employer."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Check if username already exists
        username = request.form['username']
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            # Generate a unique username by adding a random suffix
            base_username = username
            username = f"{base_username}_{uuid.uuid4().hex[:6]}"
            flash(f'Username "{base_username}" already exists. Using "{username}" instead.', 'warning')

        # Check if email already exists
        email = request.form['email']
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash(f'Email "{email}" is already registered.', 'danger')
            return redirect(url_for('main.admin_add_employer'))

        # Generate a random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create user
        user = User(
            username=username,
            email=email,
            role='employer',
            is_active=True,
            first_login=True,
            is_temporary_password=True
        )
        user.set_password(password, is_temporary=True)
        db.session.add(user)
        db.session.commit()

        # Create employer profile
        profile = EmployerProfile(
            user_id=user.id,
            company_name=request.form['company_name'],
            company_phone=request.form.get('company_phone', ''),
            company_email=request.form.get('company_email', '')
        )
        db.session.add(profile)
        db.session.commit()

        flash(f'Employer added successfully! Username: {user.username}, Password: {password}', 'success')
        return redirect(url_for('main.admin_employers'))

    return render_template('admin/add_employer.html')

@main.route('/admin/edit-employee/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_employee(user_id):
    """Edit an employee."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employee':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employees'))

    # Get or create employee profile
    profile = EmployeeProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = EmployeeProfile(user_id=user.id, first_name='', last_name='')
        db.session.add(profile)
        db.session.commit()

    # Get all active clients for the dropdown
    try:
        clients = Client.query.filter_by(is_active=True).all()
    except Exception as e:
        # Check if the client table exists
        try:
            # Try to create the client table if it doesn't exist
            from migrations.add_client_columns import run_migration
            run_migration()
            # Try again to get clients
            clients = Client.query.filter_by(is_active=True).all()
            flash("Client management is now available. Database has been updated.", "success")
        except Exception as inner_e:
            current_app.logger.error(f"Error creating client table: {str(inner_e)}")
            clients = []

    if request.method == 'POST':
        # Check if username is being changed and if it already exists
        new_username = request.form['username']
        if new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                # Generate a unique username by adding a random suffix
                base_username = new_username
                new_username = f"{base_username}_{uuid.uuid4().hex[:6]}"
                flash(f'Username "{base_username}" already exists. Using "{new_username}" instead.', 'warning')

        # Check if email is being changed and if it already exists
        new_email = request.form['email']
        if new_email != user.email:
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email:
                flash(f'Email "{new_email}" is already registered. Email not updated.', 'danger')
                new_email = user.email

        # Update user information
        user.username = new_username
        user.email = new_email
        user.is_active = 'is_active' in request.form

        # Reset password if requested
        if request.form.get('reset_password'):
            # Generate a random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(new_password, is_temporary=True)
            password_message = f", New Password: {new_password}"
        else:
            password_message = ""

        # Get client information
        client_name = request.form.get('client_name')
        client_code = request.form.get('client_code')

        if client_name and client_code:
            # Check if client already exists
            client = Client.query.filter_by(code=client_code).first()

            if not client:
                # Create a new client
                client = Client(
                    name=client_name,
                    code=client_code.upper(),
                    created_by=current_user.id,
                    is_active=True
                )
                db.session.add(client)
                db.session.commit()
                flash(f'New client "{client_name}" with code "{client_code.upper()}" created.', 'success')

            # Check if client is changing
            if not profile.client_id or profile.client_id != client.id:
                # If employee code is not set or client is changing, generate a new one
                employee_code_suffix = request.form.get('employee_code_suffix', '')
                if employee_code_suffix:
                    # Use the provided suffix
                    employee_code = f"{client.code}{employee_code_suffix}"
                else:
                    # Generate a unique code
                    from blueprints.client_routes import generate_employee_code
                    employee_code = generate_employee_code(client.code)
                profile.employee_code = employee_code

            # Update client ID
            profile.client_id = client.id

        # Update profile information
        profile.first_name = request.form['first_name']
        profile.last_name = request.form['last_name']
        profile.phone_number = request.form.get('phone_number', '')
        profile.department = request.form.get('department', '')
        profile.position = request.form.get('position', '')

        db.session.commit()

        flash(f'Employee updated successfully!{password_message}', 'success')

        # Redirect based on where the request came from
        if request.args.get('from') == 'client' and profile.client_id:
            return redirect(url_for('main.admin_client_employees', client_id=profile.client_id))
        else:
            return redirect(url_for('main.admin_employees'))

    return render_template('admin/edit_employee.html', user=user, profile=profile, clients=clients)

@main.route('/admin/reset-password/<int:user_id>')
@login_required
def admin_reset_password(user_id):
    """Reset a user's password."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)

    # Generate a random password
    new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    user.set_password(new_password, is_temporary=True)
    db.session.commit()

    flash(f'Password reset successfully! New password: {new_password}', 'success')

    # Redirect based on user role
    if user.role == 'employee':
        return redirect(url_for('main.admin_employees'))
    elif user.role == 'employer':
        return redirect(url_for('main.admin_employers'))
    else:
        return redirect(url_for('main.admin_dashboard'))

@main.route('/admin/toggle-employee-status/<int:user_id>')
@login_required
def admin_toggle_employee_status(user_id):
    """Toggle employee active status."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employee':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employees'))

    # Toggle the active status
    user.is_active = not user.is_active
    db.session.commit()

    status = 'activated' if user.is_active else 'deactivated'
    flash(f'Employee {user.username} has been {status}.', 'success')
    return redirect(url_for('main.admin_employees'))

@main.route('/admin/employee-documents/<int:user_id>')
@login_required
def admin_employee_documents(user_id):
    """View employee documents."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employee':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employees'))

    # Get the employee's profile
    employee_profile = EmployeeProfile.query.filter_by(user_id=user.id).first()
    if not employee_profile:
        flash('Employee profile not found.', 'danger')
        return redirect(url_for('main.admin_employees'))

    # Get documents for this specific employee
    # Try both employee_id and user_id to ensure we get all documents
    documents_by_employee_id = Document.query.filter_by(employee_id=employee_profile.id).all()
    documents_by_user_id = Document.query.filter_by(user_id=user.id).all()

    # Combine the documents, avoiding duplicates
    documents = []
    doc_ids = set()

    # First add documents by employee_id
    for doc in documents_by_employee_id:
        if doc.id not in doc_ids:
            documents.append(doc)
            doc_ids.add(doc.id)

    # Then add documents by user_id if not already added
    for doc in documents_by_user_id:
        if doc.id not in doc_ids:
            documents.append(doc)
            doc_ids.add(doc.id)

    current_app.logger.info(f"Found {len(documents)} documents for employee {employee_profile.id}")

    # Define status colors
    status_colors = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'not_uploaded': 'secondary'
    }

    # Create a dictionary to map document types for easier access in the template
    document_dict = {}

    # Map all documents to their respective keys
    for doc in documents:
        # Map document types to standardized keys
        if doc.document_type == 'new_joining_form' or doc.document_type == 'new_joining_application':
            document_dict['new_joining_form'] = doc
        elif doc.document_type == 'pf_form' or doc.document_type == 'pf_form_2':
            document_dict['pf_form'] = doc
        elif doc.document_type == 'form_1_nomination' or doc.document_type == 'form_1':
            document_dict['form_1_nomination'] = doc
        elif doc.document_type == 'form_11' or doc.document_type == 'form_11_revised':
            document_dict['form_11'] = doc
        elif doc.document_type == 'aadhar_card':
            document_dict['aadhar_card'] = doc
        elif doc.document_type == 'pan_card':
            document_dict['pan_card'] = doc
        elif doc.document_type == 'photo':
            document_dict['photo'] = doc
        elif doc.document_type == 'police_verification':
            document_dict['police_verification'] = doc
        elif doc.document_type == 'medical_certificate':
            document_dict['medical_certificate'] = doc

    # Get family members for this employee
    family_members = FamilyMember.query.filter_by(employee_id=employee_profile.id).all()
    current_app.logger.info(f"Found {len(family_members)} family members for employee {employee_profile.id}")

    # Find family details document if it exists
    family_document = Document.query.filter_by(
        employee_id=employee_profile.id,
        document_type='family_declaration'
    ).first()

    return render_template('admin/employee_documents.html',
                          employee=employee_profile,
                          documents=documents,
                          document_dict=document_dict,
                          status_colors=status_colors,
                          family_members=family_members,
                          family_document=family_document)

@main.route('/admin/remove-employee/<int:user_id>', methods=['POST'])
@login_required
def admin_remove_employee(user_id):
    """Remove an employee."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employee':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employees'))

    db.session.delete(user)
    db.session.commit()

    flash('Employee removed successfully!', 'success')
    return redirect(url_for('main.admin_employees'))

@main.route('/admin/edit-employer/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_employer(user_id):
    """Edit an employer."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employer':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employers'))

    # Get or create employer profile
    profile = EmployerProfile.query.filter_by(user_id=user.id).first()
    if not profile:
        profile = EmployerProfile(user_id=user.id, company_name='')
        db.session.add(profile)
        db.session.commit()

    if request.method == 'POST':
        # Check if username is being changed and if it already exists
        new_username = request.form['username']
        if new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                # Generate a unique username by adding a random suffix
                base_username = new_username
                new_username = f"{base_username}_{uuid.uuid4().hex[:6]}"
                flash(f'Username "{base_username}" already exists. Using "{new_username}" instead.', 'warning')

        # Check if email is being changed and if it already exists
        new_email = request.form['email']
        if new_email != user.email:
            existing_email = User.query.filter_by(email=new_email).first()
            if existing_email:
                flash(f'Email "{new_email}" is already registered. Email not updated.', 'danger')
                new_email = user.email

        # Update user information
        user.username = new_username
        user.email = new_email
        user.is_active = 'is_active' in request.form

        # Reset password if requested
        if request.form.get('reset_password'):
            # Generate a random password
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(new_password, is_temporary=True)
            password_message = f", New Password: {new_password}"
        else:
            password_message = ""

        # Update profile information
        profile.company_name = request.form['company_name']
        profile.company_phone = request.form.get('company_phone', '')
        profile.company_email = request.form.get('company_email', '')
        profile.company_address = request.form.get('company_address', '')

        db.session.commit()

        flash(f'Employer updated successfully!{password_message}', 'success')
        return redirect(url_for('main.admin_employers'))

    return render_template('admin/edit_employer.html', user=user, profile=profile)

@main.route('/admin/toggle-employer-status/<int:user_id>')
@login_required
def admin_toggle_employer_status(user_id):
    """Toggle employer active status."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employer':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employers'))

    # Toggle the active status
    user.is_active = not user.is_active
    db.session.commit()

    status = 'activated' if user.is_active else 'deactivated'
    flash(f'Employer {user.username} has been {status}.', 'success')
    return redirect(url_for('main.admin_employers'))

@main.route('/admin/remove-employer/<int:user_id>', methods=['POST'])
@login_required
def admin_remove_employer(user_id):
    """Remove an employer."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    user = User.query.get_or_404(user_id)
    if user.role != 'employer':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('main.admin_employers'))

    db.session.delete(user)
    db.session.commit()

    flash('Employer removed successfully!', 'success')
    return redirect(url_for('main.admin_employers'))

@main.route('/admin/bulk-employee-upload', methods=['GET', 'POST'])
@login_required
def admin_bulk_employee_upload():
    """Upload bulk employee data from Excel file."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        if 'excel_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)

        file = request.files['excel_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and file.filename.endswith(('.xlsx', '.xls')):
            # Create a secure filename
            filename = secure_filename(file.filename)
            file_path = os.path.join('temp', filename)
            os.makedirs('temp', exist_ok=True)
            file.save(file_path)

            # Process the Excel file
            try:
                df = pd.read_excel(file_path)
                required_columns = ['name', 'email', 'phone_number']

                # Check if required columns exist
                if not all(col in df.columns for col in required_columns):
                    flash('Excel file must contain columns: name, email, phone_number', 'danger')
                    os.remove(file_path)
                    return redirect(request.url)

                # Process each row
                success_count = 0
                error_count = 0
                for _, row in df.iterrows():
                    try:
                        # Check if user with this email already exists
                        existing_user = User.query.filter_by(email=row['email']).first()
                        if existing_user:
                            current_app.logger.warning(f"Skipping duplicate email: {row['email']}")
                            error_count += 1
                            continue

                        # Generate username from email
                        base_username = row['email'].split('@')[0]
                        username = base_username

                        # Check if username exists, if so, add random suffix
                        counter = 1
                        while User.query.filter_by(username=username).first():
                            # Try adding a number first for cleaner usernames
                            if counter <= 5:
                                username = f"{base_username}{counter}"
                            else:
                                # If still colliding after 5 attempts, use UUID
                                username = f"{base_username}_{uuid.uuid4().hex[:6]}"
                                break
                            counter += 1

                        # Generate random password
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

                        # Create user
                        user = User(
                            username=username,
                            email=row['email'],
                            role='employee',
                            is_active=True,
                            first_login=True,
                            is_temporary_password=True
                        )
                        user.set_password(password, is_temporary=True)
                        db.session.add(user)
                        db.session.flush()  # Get user ID without committing

                        # Split name into first and last name
                        name_parts = row['name'].split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(name_parts) > 1 else ''

                        # Create employee profile
                        profile = EmployeeProfile(
                            user_id=user.id,
                            first_name=first_name,
                            last_name=last_name,
                            phone_number=str(row['phone_number'])
                        )
                        db.session.add(profile)
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                        print(f"Error processing row: {e}")

                db.session.commit()
                os.remove(file_path)

                flash(f'Bulk upload completed. {success_count} employees added successfully, {error_count} errors.', 'success')
                return redirect(url_for('main.admin_employees'))

            except Exception as e:
                flash(f'Error processing Excel file: {str(e)}', 'danger')
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'danger')
            return redirect(request.url)

    return render_template('admin/bulk_employee_upload.html')

@main.route('/employer/employees', methods=['GET', 'POST'])
@login_required
def employer_employees():
    if not current_user.is_employer():
        flash('Access denied. You are not an employer.', 'danger')
        return redirect(url_for('main.dashboard'))

    # Get employer profile
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer_profile:
        flash('Please complete your employer profile first.', 'warning')
        return redirect(url_for('main.edit_employer_profile'))

    # Initialize search form
    search_form = EmployeeSearchForm()

    # Get the query from form or request args
    search_query = None
    if request.method == 'POST' and search_form.validate_on_submit():
        search_query = search_form.query.data
        # Redirect to GET with query parameter to avoid form resubmission issues
        return redirect(url_for('main.employer_employees', query=search_query))
    elif request.args.get('query'):
        search_query = request.args.get('query')
        search_form.query.data = search_query

    # Base query - filter by employees associated with this employer
    # Here we assume there's a relationship between employees and employers
    # This might need adjustment based on your exact data model
    query = EmployeeProfile.query

    # Apply search filter if query exists
    if search_query:
        search_term = f"%{search_query}%"

        # Check if the search query looks like an employee ID (EMP followed by numbers)
        emp_id_match = None
        if search_query.upper().startswith('EMP') and search_query[3:].isdigit():
            try:
                # Extract the numeric part after 'EMP'
                emp_id_num = int(search_query[3:])
                emp_id_match = EmployeeProfile.id == emp_id_num
            except ValueError:
                pass

        # Build the search filter
        if emp_id_match:
            query = query.filter(emp_id_match)
        else:
            query = query.filter(db.or_(
                EmployeeProfile.first_name.ilike(search_term),
                EmployeeProfile.last_name.ilike(search_term),
                EmployeeProfile.department.ilike(search_term),
                EmployeeProfile.position.ilike(search_term)
            ))

    # Get all employees
    employees = query.all()

    return render_template('employer/employees.html',
                          employees=employees,
                          employer=employer_profile,
                          search_form=search_form)

@main.route('/employer/documents')
@main.route('/employer/documents/<int:employee_id>')
@login_required
def employer_documents(employee_id=None):
    """Employer documents management route."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employer's profile
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer_profile:
        flash('Please complete your employer profile first.', 'warning')
        return redirect(url_for('main.profile'))

    if not employee_id:
        flash('Employee ID is required to view documents.', 'warning')
        return redirect(url_for('main.employer_employees'))

    # Get the employee's profile
    employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # TODO: Add authorization check to ensure employee belongs to employer

    # Get documents for this specific employee
    # Try both employee_id and user_id to ensure we get all documents
    documents_by_employee_id = Document.query.filter_by(employee_id=employee_id).all()
    documents_by_user_id = Document.query.filter_by(user_id=employee_profile.user_id).all()

    # Combine the documents, avoiding duplicates
    documents = []
    doc_ids = set()

    # First add documents by employee_id
    for doc in documents_by_employee_id:
        if doc.id not in doc_ids:
            documents.append(doc)
            doc_ids.add(doc.id)

    # Then add documents by user_id if not already added
    for doc in documents_by_user_id:
        if doc.id not in doc_ids:
            documents.append(doc)
            doc_ids.add(doc.id)

    current_app.logger.info(f"Found {len(documents_by_employee_id)} documents by employee_id and {len(documents_by_user_id)} by user_id, total unique: {len(documents)}")

    # Log document count for debugging
    current_app.logger.info(f"Found {len(documents)} documents for employee {employee_id}")
    for doc in documents:
        current_app.logger.info(f"Document: {doc.id}, Type: {doc.document_type}, Status: {doc.status}, File path: {doc.file_path}")

    # Define status colors
    status_colors = {
        'pending': 'warning',
        'approved': 'success',
        'rejected': 'danger',
        'not_uploaded': 'secondary'
    }

    # Create a dictionary to map document types for easier access in the template
    document_dict = {}

    # Map all documents to their respective keys
    for doc in documents:
        current_app.logger.info(f"Checking document: {doc.id}, Type: {doc.document_type}, Status: {doc.status}")

        # Map document types to standardized keys
        if doc.document_type == 'new_joining_form' or doc.document_type == 'new_joining_application':
            document_dict['new_joining_form'] = doc
            current_app.logger.info(f"Mapped joining form: {doc.id}, Type: {doc.document_type} to 'new_joining_form'")

        elif doc.document_type == 'pf_form' or doc.document_type == 'pf_form_2':
            document_dict['pf_form'] = doc
            current_app.logger.info(f"Mapped PF form: {doc.id}, Type: {doc.document_type} to 'pf_form'")

        elif doc.document_type == 'form_1_nomination' or doc.document_type == 'form_1':
            document_dict['form_1_nomination'] = doc
            current_app.logger.info(f"Mapped Form 1: {doc.id}, Type: {doc.document_type} to 'form_1_nomination'")

        elif doc.document_type == 'form_11' or doc.document_type == 'form_11_revised':
            document_dict['form_11'] = doc
            current_app.logger.info(f"Mapped Form 11: {doc.id}, Type: {doc.document_type} to 'form_11'")

        # Map other document types
        elif doc.document_type == 'aadhar_card':
            document_dict['aadhar_card'] = doc
            current_app.logger.info(f"Mapped Aadhar Card: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'pan_card':
            document_dict['pan_card'] = doc
            current_app.logger.info(f"Mapped PAN Card: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'photo':
            document_dict['photo'] = doc
            current_app.logger.info(f"Mapped Photo: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'police_verification':
            document_dict['police_verification'] = doc
            current_app.logger.info(f"Mapped Police Verification: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'medical_certificate':
            document_dict['medical_certificate'] = doc
            current_app.logger.info(f"Mapped Medical Certificate: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'bank_passbook':
            document_dict['bank_passbook'] = doc
            current_app.logger.info(f"Mapped Bank Passbook: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'family_declaration':
            document_dict['family_declaration'] = doc
            current_app.logger.info(f"Mapped Family Declaration: {doc.id}, Type: {doc.document_type}")

        elif doc.document_type == 'passport':
            document_dict['passport'] = doc
            current_app.logger.info(f"Mapped Passport: {doc.id}, Type: {doc.document_type}")

        # For any other document types
        else:
            document_dict[doc.document_type] = doc
            current_app.logger.info(f"Mapped document: {doc.id}, Type: {doc.document_type} to '{doc.document_type}'")

    # Add the document_dict to the template context
    current_app.logger.info(f"Document dictionary keys: {list(document_dict.keys())}")

    # Get family members for this employee
    family_members = FamilyMember.query.filter_by(employee_id=employee_profile.id).all()
    current_app.logger.info(f"Found {len(family_members)} family members for employee {employee_profile.id}")

    # Find family details document if it exists
    family_document = None
    if 'family_declaration' in document_dict:
        family_document = document_dict['family_declaration']

    # Pass the document_dict and family_members to the template
    return render_template('employer/employee_documents.html',
                          employee=employee_profile,
                          documents=documents,
                          document_dict=document_dict,
                          status_colors=status_colors,
                          family_members=family_members,
                          family_document=family_document)

@main.route('/employee/document-center')
@login_required
def document_center():
    """Employee document center route."""
    if not (current_user.is_employee() or current_user.is_employer() or current_user.is_admin()):
        flash('Access denied. Employee, employer, or admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    if current_user.is_employee():
        employee_profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee_profile:
            flash('Please complete your employee profile first.', 'warning')
            return redirect(url_for('main.profile'))
    else:  # Employer or Admin accessing employee data
        employee_id = request.args.get('employee_id')
        if not employee_id:
            if current_user.is_employer():
                flash('Employee ID is required.', 'warning')
                return redirect(url_for('main.employer_employees'))
            else:  # Admin
                flash('Employee ID is required.', 'warning')
                return redirect(url_for('main.admin_employees'))
        employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # Get all documents for this employee
    documents = Document.query.filter_by(user_id=employee_profile.user_id).all()

    # Log document count for debugging
    current_app.logger.info(f"Document center: Found {len(documents)} documents for user {employee_profile.user_id}")
    for doc in documents:
        current_app.logger.info(f"Document center: Document: {doc.id}, Type: {doc.document_type}, Status: {doc.status}, File path: {doc.file_path}")

    # Organize documents by type for easier access in template
    document_dict = {}

    # First, log all documents for debugging
    current_app.logger.info("Document types in document_center:")
    for doc in documents:
        current_app.logger.info(f"Document: {doc.id}, Type: {doc.document_type}")

    # Then organize them
    for doc in documents:
        # Handle different document type variations
        if doc.document_type == 'new_joining_application' or doc.document_type == 'new_joining_form':
            document_dict['new_joining_form'] = doc
            current_app.logger.info(f"Mapped joining form: {doc.id}, Type: {doc.document_type} to 'new_joining_form'")
        elif doc.document_type == 'pf_form_2' or doc.document_type == 'pf_form':
            document_dict['pf_form'] = doc
            current_app.logger.info(f"Mapped PF form: {doc.id}, Type: {doc.document_type} to 'pf_form'")
        elif doc.document_type == 'form_1' or doc.document_type == 'form_1_nomination':
            document_dict['form_1_nomination'] = doc
            current_app.logger.info(f"Mapped Form 1: {doc.id}, Type: {doc.document_type} to 'form_1_nomination'")
        elif doc.document_type == 'form_11_revised' or doc.document_type == 'form_11':
            document_dict['form_11'] = doc
            current_app.logger.info(f"Mapped Form 11: {doc.id}, Type: {doc.document_type} to 'form_11'")
        else:
            document_dict[doc.document_type] = doc
            current_app.logger.info(f"Mapped document: {doc.id}, Type: {doc.document_type} to '{doc.document_type}'")

    # Get completion percentage
    completion_percentage = 0
    if documents:
        completed_docs = sum(1 for doc in documents if doc.status == 'approved')
        completion_percentage = (completed_docs / len(documents)) * 100 if documents else 0

    # Check if combined PDF exists
    from flask import session
    has_combined_pdf = bool(session.get('combined_pdf_path') and
                          os.path.exists(session.get('combined_pdf_path')))

    # Initialize document upload form with document type choices
    upload_form = DocumentUploadForm()
    upload_form.document_type.choices = [(doc_type, doc_type.replace('_', ' ').title())
                                       for doc_type in DocumentTypes.all_types()]

    # Get all document types for display
    document_types = DocumentTypes.all_types()

    # Get family members for this employee
    family_members = FamilyMember.query.filter_by(employee_id=employee_profile.id).all()
    current_app.logger.info(f"Found {len(family_members)} family members for employee {employee_profile.id}")

    return render_template('employee/document_center.html',
                         employee=employee_profile,
                         documents=document_dict,
                         document_types=document_types,
                         completion_percentage=completion_percentage,
                         has_combined_pdf=has_combined_pdf,
                         upload_form=upload_form,
                         family_members=family_members)

@main.route('/delete-all-documents', methods=['POST'])
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

@main.route('/employer/news')
@login_required
def employer_news():
    """Employer news management route."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employer's profile
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer_profile:
        flash('Please complete your employer profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Get news updates for the employer
    news_updates = NewsUpdate.query.filter_by(created_by=current_user.id).order_by(NewsUpdate.created_at.desc()).all()
    return render_template('employer/news_list.html', news_updates=news_updates)

@main.route('/employer/news/create', methods=['GET', 'POST'])
@login_required
def create_news_update():
    """Create a new news update."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employer's profile
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not employer_profile:
        flash('Please complete your employer profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Create form
    form = NewsUpdateForm()

    if form.validate_on_submit():
        # Create new news update
        news_update = NewsUpdate(
            title=form.title.data,
            content=form.content.data,
            created_by=current_user.id,
            is_active=form.is_active.data
        )
        db.session.add(news_update)
        db.session.commit()

        flash('News update created successfully!', 'success')
        return redirect(url_for('main.employer_news'))

    return render_template('employer/create_news.html', form=form)

@main.route('/employer/news/edit/<int:news_id>', methods=['GET', 'POST'])
@login_required
def edit_news_update(news_id):
    """Edit a news update."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the news update
    news_update = NewsUpdate.query.get_or_404(news_id)

    # Check if the current user is the creator
    if news_update.created_by != current_user.id:
        flash('Access denied. You can only edit your own news updates.', 'danger')
        return redirect(url_for('main.employer_news'))

    # Create form and populate with existing data
    form = NewsUpdateForm(obj=news_update)

    if form.validate_on_submit():
        # Update news update
        news_update.title = form.title.data
        news_update.content = form.content.data
        news_update.is_active = form.is_active.data
        news_update.updated_at = datetime.utcnow()
        db.session.commit()

        flash('News update updated successfully!', 'success')
        return redirect(url_for('main.employer_news'))

    return render_template('employer/edit_news.html', form=form, news=news_update)

@main.route('/employer/news/delete/<int:news_id>', methods=['POST'])
@login_required
def delete_news_update(news_id):
    """Delete a news update."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the news update
    news_update = NewsUpdate.query.get_or_404(news_id)

    # Check if the current user is the creator
    if news_update.created_by != current_user.id:
        flash('Access denied. You can only delete your own news updates.', 'danger')
        return redirect(url_for('main.employer_news'))

    # Delete the news update
    db.session.delete(news_update)
    db.session.commit()

    flash('News update deleted successfully!', 'success')
    return redirect(url_for('main.employer_news'))

@main.route('/document/<int:document_id>')
@login_required
def view_document(document_id):
    """View document route."""
    document = Document.query.get_or_404(document_id)

    # Check if user has permission to view the document
    if not (current_user.is_admin() or
            current_user.is_employer() or
            (current_user.is_employee() and document.user_id == current_user.id)):
        flash('Access denied. You do not have permission to view this document.', 'danger')
        return redirect(url_for('main.index'))

    # Get file path using multiple methods to ensure we find it
    file_path = None

    # Method 1: Check the file_path attribute directly
    if hasattr(document, 'file_path') and document.file_path:
        file_path = document.file_path
        current_app.logger.info(f"Found file_path attribute: {file_path}")

    # Method 2: Check if description contains a path to the file
    elif document.description and ('uploads' in document.description or document.description.startswith('uploads/')):
        file_path = document.description
        # Save the file path to the database for future use
        document.file_path = file_path
        db.session.commit()
        current_app.logger.info(f"Updated document {document_id} file_path from description: {file_path}")

    # Method 3: Use the get_file_path_from_description method
    elif hasattr(document, 'get_file_path_from_description'):
        file_path = document.get_file_path_from_description()
        if file_path:
            current_app.logger.info(f"Found file path from get_file_path_from_description: {file_path}")

    # Log document details for debugging
    current_app.logger.info(f"Viewing document {document_id}: {document.document_type}, Status: {document.status}, File path: {file_path}")

    # Special handling for joining forms - check in the joining_forms directory
    if (document.document_type == DocumentTypes.NEW_JOINING_FORM or document.document_type == 'new_joining_application') and not file_path:
        joining_forms_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'joining_forms')
        if os.path.exists(joining_forms_dir):
            # Look for files that match the employee ID
            matching_files = [f for f in os.listdir(joining_forms_dir)
                             if f.startswith(f"joining_form_{document.employee_id}_")]
            if matching_files:
                # Use the most recent file
                matching_files.sort(reverse=True)
                file_path = os.path.join('uploads', 'joining_forms', matching_files[0])
                # Update the document with the found file path
                document.file_path = file_path
                db.session.commit()
                current_app.logger.info(f"Found joining form in directory: {file_path}")

    # If we still don't have a file path, check if there are any files in the user's upload directory that match the document type
    if not file_path:
        # Try to find a file in the user's upload directory that matches the document type
        user_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(document.user_id))
        if os.path.exists(user_upload_dir):
            # Look for files that start with the document type
            matching_files = [f for f in os.listdir(user_upload_dir) if f.startswith(document.document_type)]
            if matching_files:
                # Use the most recent file (assuming the files have timestamps in their names)
                matching_files.sort(reverse=True)
                file_path = os.path.join('uploads', str(document.user_id), matching_files[0])
                # Update the document with the found file path
                document.file_path = file_path
                db.session.commit()
                current_app.logger.info(f"Found matching file in user directory: {file_path}")

    # If we still don't have a file path, render the template with a flag indicating no file
    if not file_path:
        current_app.logger.error(f"Document {document_id} has no file path. Description: {document.description}")
        return render_template('view_document.html', document=document, file_not_found=True)

    # Normalize the file path for consistent handling
    relative_path = normalize_path(file_path)
    current_app.logger.info(f"Normalized path: {relative_path}")

    # Get the full path and check if the file exists
    full_path, file_exists = get_full_path(relative_path)
    current_app.logger.info(f"Full path: {full_path}, File exists: {file_exists}")

    # Add debug information to the template context
    debug_info = {
        'document_id': document.id,
        'document_type': document.document_type,
        'file_path': file_path,
        'relative_path': relative_path,
        'full_path': full_path,
        'file_exists': file_exists,
        'description': document.description
    }

    # Pass both the document and file information to the template
    return render_template('document_fullpage_view.html',
                          document=document,
                          file_path=relative_path,
                          file_exists=file_exists)

@main.route('/employee/manage-family-members', methods=['GET', 'POST'])
@login_required
def manage_family_members():
    """Add, edit, or remove family members."""
    if not (current_user.is_employee() or current_user.is_employer()):
        flash('Access denied. Employee or employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    if current_user.is_employee():
        employee_profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee_profile:
            flash('Please complete your employee profile first.', 'warning')
            return redirect(url_for('main.profile'))
    else:  # Employer accessing employee data
        employee_id = request.args.get('employee_id')
        if not employee_id:
            flash('Employee ID is required.', 'warning')
            return redirect(url_for('main.employer_employees'))
        employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # Fix any absolute paths in the database
    from utils.path_utils import fix_family_member_paths
    fix_family_member_paths()

    # Get existing family members
    family_members = FamilyMember.query.filter_by(employee_id=employee_profile.id).all()

    # Check if maximum limit reached
    max_members_reached = len(family_members) >= 10

    # Only employees can modify family members
    form = None
    if current_user.is_employee() and not max_members_reached:
        form = FamilyMemberForm()
        if form.validate_on_submit():
            # Check if maximum limit reached
            if len(family_members) >= 10:
                flash('Maximum limit of 10 family members reached. Please remove an existing member first.', 'warning')
                return redirect(url_for('main.manage_family_members'))

            # Create a new family member
            member = FamilyMember(
                employee_id=employee_profile.id,
                name=form.name.data,
                relationship=form.relationship.data,
                date_of_birth=form.date_of_birth.data,
                aadhar_id=form.aadhar_id.data,
                contact_number=form.contact_number.data
            )

            # Handle photo upload if provided
            if form.photo.data:
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"photo_{employee_profile.id}_{timestamp}_{secure_filename(form.photo.data.filename)}"

                # Create directory for family photos - use a simpler path structure
                static_dir = os.path.join(current_app.root_path, 'static')
                upload_folder = os.path.join(static_dir, 'uploads', 'family_photos')
                os.makedirs(upload_folder, exist_ok=True)

                # Save the file to the absolute path
                abs_filepath = os.path.join(upload_folder, filename)
                form.photo.data.save(abs_filepath)

                # Store the relative path in the family member record (for URL generation)
                # Use a simple path that works directly with url_for
                rel_filepath = f"uploads/family_photos/{filename}"
                member.photo_path = rel_filepath

                # Log the normalized path
                current_app.logger.info(f"Normalized photo path: {rel_filepath}")

                # Also store the filename separately for easier access
                # Check if the column exists in the model
                if hasattr(member, 'photo_filename'):
                    member.photo_filename = filename

                # Log the path for debugging
                current_app.logger.info(f"Saved family member photo at: {abs_filepath}")
                current_app.logger.info(f"Relative path stored: {rel_filepath}")

            # Handle Aadhar card upload if provided
            aadhar_card = request.files.get('aadhar_card')
            if aadhar_card:
                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"aadhar_{employee_profile.id}_{timestamp}_{secure_filename(aadhar_card.filename)}"

                # Create directory for family documents - use a simpler path structure
                static_dir = os.path.join(current_app.root_path, 'static')
                upload_folder = os.path.join(static_dir, 'uploads', 'family_documents')
                os.makedirs(upload_folder, exist_ok=True)

                # Save the file to the absolute path
                abs_filepath = os.path.join(upload_folder, filename)
                aadhar_card.save(abs_filepath)

                # Store the relative path in the family member record (for URL generation)
                # Use a simple path that works directly with url_for
                rel_filepath = f"uploads/family_documents/{filename}"
                member.aadhar_card_path = rel_filepath

                # Log the normalized path
                current_app.logger.info(f"Normalized aadhar card path: {rel_filepath}")

                # Log the path for debugging
                current_app.logger.info(f"Saved Aadhar card at: {abs_filepath}")
                current_app.logger.info(f"Relative path stored: {rel_filepath}")

                # Also store the filename separately for easier access
                # Check if the column exists in the model
                if hasattr(member, 'aadhar_filename'):
                    member.aadhar_filename = filename

                # Create a document record for the Aadhar card
                aadhar_doc = Document(
                    user_id=current_user.id,
                    employee_id=employee_profile.id,
                    document_type='family_aadhar_card',
                    title=f"{member.name} - Aadhar Card",
                    description=f"Aadhar card for family member: {member.name}",
                    file_path=rel_filepath,
                    status='approved'
                )
                db.session.add(aadhar_doc)

            db.session.add(member)
            db.session.commit()

            flash(f'Family member {member.name} added successfully!', 'success')
            return redirect(url_for('main.manage_family_members'))

    return render_template('employee/manage_family_members.html',
                         form=form,
                         family_members=family_members,
                         employee=employee_profile,
                         is_employer=current_user.is_employer())

@main.route('/employee/download-all-documents')
@login_required
def download_all_documents():
    """Download all documents as a ZIP file."""
    if not (current_user.is_employee() or current_user.is_employer()):
        flash('Access denied. Employee or employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    if current_user.is_employee():
        employee_profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee_profile:
            flash('Please complete your employee profile first.', 'warning')
            return redirect(url_for('main.document_center'))
    else:  # Employer
        employee_id = request.args.get('employee_id')
        if not employee_id:
            flash('Employee ID is required.', 'warning')
            return redirect(url_for('main.employer_employees'))
        employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # Get all documents for this employee
    documents = Document.query.filter_by(user_id=employee_profile.user_id).all()
    if not documents:
        flash('No documents found to download.', 'warning')
        return redirect(url_for('main.document_center'))

    # Create a ZIP file in memory
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for doc in documents:
            # Get file path using dedicated field or fallback method
            file_path = doc.file_path or doc.get_file_path_from_description()
            if file_path:
                # Construct full path
                full_path = os.path.join(current_app.root_path, 'static', file_path)
                if os.path.exists(full_path):
                    # Add file to ZIP with a clean filename
                    file_ext = os.path.splitext(file_path)[1][1:] or 'pdf'
                    clean_filename = f"{doc.document_type}_{doc.uploaded_at.strftime('%Y%m%d')}.{file_ext}"
                    zf.write(full_path, clean_filename)

    # Seek to the beginning of the file
    memory_file.seek(0)

    # Create the response
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'documents_{employee_profile.first_name}_{employee_profile.last_name}_{datetime.now().strftime("%Y%m%d")}.zip'
    )

@main.route('/employee/generate-combined-documents')
@login_required
def generate_combined_documents():
    """Generate a combined PDF of all documents."""
    if not (current_user.is_employee() or current_user.is_employer()):
        flash('Access denied. Employee or employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    if current_user.is_employee():
        employee_profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
        if not employee_profile:
            flash('Please complete your employee profile first.', 'warning')
            return redirect(url_for('main.profile'))
    else:  # Employer
        employee_id = request.args.get('employee_id')
        if not employee_id:
            flash('Employee ID is required.', 'warning')
            return redirect(url_for('main.employer_employees'))
        employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # Get all documents for this employee
    documents = Document.query.filter_by(user_id=employee_profile.user_id).all()
    if not documents:
        flash('No documents found to combine.', 'warning')
        return redirect(url_for('main.document_center'))

    try:
        from PyPDF2 import PdfMerger
        import os

        # Create a PDF merger object
        merger = PdfMerger()

        # Track if we added any documents
        documents_added = False

        # Add each PDF document to the merger
        for doc in documents:
            if doc.path and os.path.exists(doc.path) and doc.path.lower().endswith('.pdf'):
                merger.append(doc.path)
                documents_added = True

        if not documents_added:
            flash('No PDF documents found to combine.', 'warning')
            return redirect(url_for('main.document_center'))

        # Create the output directory if it doesn't exist
        output_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'combined_documents')
        os.makedirs(output_dir, exist_ok=True)

        # Generate the output filename
        output_filename = f'combined_docs_{employee_profile.first_name}_{employee_profile.last_name}_{datetime.now().strftime("%Y%m%d")}.pdf'
        output_path = os.path.join(output_dir, output_filename)

        # Write the combined PDF
        merger.write(output_path)
        merger.close()

        # Store the combined PDF path in the session for preview
        from flask import session
        session['combined_pdf_path'] = output_path

        flash('Documents combined successfully!', 'success')
        return redirect(url_for('main.document_center', employee_id=employee_profile.id, has_combined_pdf=True))

    except Exception as e:
        flash(f'Error combining documents: {str(e)}', 'danger')
        return redirect(url_for('main.document_center'))

@main.route('/employee/preview-combined-pdf')
@login_required
def preview_combined_pdf():
    """Preview the combined PDF document."""
    if not (current_user.is_employee() or current_user.is_employer()):
        flash('Access denied. Employee or employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    from flask import session, send_file

    # Check if we have a combined PDF path in the session
    pdf_path = session.get('combined_pdf_path')
    if not pdf_path or not os.path.exists(pdf_path):
        flash('No combined PDF available. Please generate one first.', 'warning')
        return redirect(url_for('main.document_center'))

    # Send the file for preview
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=os.path.basename(pdf_path)
    )

@main.route('/employee/forms/joining', methods=['GET', 'POST'])
@login_required
def fill_joining_form():
    """Fill or edit joining form."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Check if form already exists
    existing_doc = Document.query.filter_by(
        user_id=current_user.id,
        document_type=DocumentTypes.NEW_JOINING_FORM
    ).first()

    # Create form instance
    form = JoiningForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Process form submission
            form_data = request.form.to_dict()

            # Generate PDF from form data
            from utils.pdf_generator import generate_joining_form_pdf
            pdf_path = generate_joining_form_pdf(form_data, employee)

            if existing_doc:
                # Update existing document
                existing_doc.file_path = pdf_path  # Store path in file_path field
                existing_doc.status = 'pending'
                existing_doc.updated_at = datetime.utcnow()
                flash('Joining form updated successfully!', 'success')
            else:
                # Create new document
                new_doc = Document(
                    user_id=current_user.id,
                    employee_id=employee.id,
                    document_type=DocumentTypes.NEW_JOINING_FORM,
                    title=DocumentTypes.NEW_JOINING_FORM.replace('_', ' ').title(),
                    file_path=pdf_path,  # Store filepath in file_path field
                    status='pending'
                )
                db.session.add(new_doc)
                flash('Joining form submitted successfully!', 'success')

            db.session.commit()
            # Redirect to form1 after joining form submission
            return redirect(url_for('main.fill_form1'))

    # Pre-fill form with existing data if available
    if existing_doc:
        # Load data from existing PDF if possible
        from utils.pdf_parser import extract_joining_form_data
        form_data = extract_joining_form_data(existing_doc.file_path)  # Use file_path as file path
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('employee/forms/joining_form.html',
                         employee=employee,
                         form=form)

from forms.employee_forms import PFForm

@main.route('/employee/forms/pf', methods=['GET', 'POST'])
@login_required
def fill_pf_form():
    """Fill or edit PF form."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Check if form already exists
    existing_doc = Document.query.filter_by(
        user_id=current_user.id,
        document_type=DocumentTypes.PF_FORM
    ).first()

    form = PFForm()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Process form submission
            form_data = form.data

            # Generate PDF from form data
            from utils.pdf_generator import generate_pf_form_pdf
            pdf_path = generate_pf_form_pdf(form_data, employee)

            if existing_doc:
                # Update existing document
                existing_doc.description = pdf_path  # Store path in description
                existing_doc.status = 'pending'
                existing_doc.updated_at = datetime.utcnow()
                flash('PF form updated successfully!', 'success')
            else:
                # Create new document
                new_doc = Document(
                    user_id=current_user.id,
                    employee_id=employee.id,
                    document_type=DocumentTypes.PF_FORM,
                    title=DocumentTypes.PF_FORM.replace('_', ' ').title(),
                    description=pdf_path,  # Store filepath in description
                    status='pending'
                )
                db.session.add(new_doc)
                flash('PF form submitted successfully!', 'success')

            db.session.commit()
            # Redirect to document center after PF form submission
            return redirect(url_for('main.document_center'))

    # Pre-fill form with existing data if available
    if existing_doc:
        # Load data from existing PDF if possible
        from utils.pdf_parser import extract_pf_form_data
        form_data = extract_pf_form_data(existing_doc.description)  # Use description as file path
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('employee/forms/pf_form.html',
                         employee=employee,
                         form=form)

@main.route('/employee/forms/form1', methods=['GET', 'POST'])
@login_required
def fill_form1():
    """Fill or edit Form 1 (Nomination & Declaration)."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    from forms.form1_form import Form1

    form = Form1()

    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Check if form already exists
    existing_doc = Document.query.filter_by(
        user_id=current_user.id,
        document_type=DocumentTypes.FORM_1_NOMINATION
    ).first()

    if form.validate_on_submit():
        from utils.pdf_generator import generate_form1_pdf
        pdf_path = generate_form1_pdf(form.data, employee)

        if existing_doc:
            existing_doc.description = pdf_path
            existing_doc.status = 'pending'
            existing_doc.updated_at = datetime.utcnow()
            flash('Form 1 updated successfully!', 'success')
        else:
            new_doc = Document(
                user_id=current_user.id,
                employee_id=employee.id,
                document_type=DocumentTypes.FORM_1_NOMINATION,
                title=DocumentTypes.FORM_1_NOMINATION.replace('_', ' ').title(),
                description=pdf_path,
                status='pending'
            )
            db.session.add(new_doc)
            flash('Form 1 submitted successfully!', 'success')

        db.session.commit()
        # Redirect to form11 after form1 submission
        return redirect(url_for('main.fill_form11'))

    # Pre-populate form with existing data if available
    if existing_doc:
        from utils.pdf_parser import extract_form1_data
        form_data = extract_form1_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('employee/forms/form1.html', form=form, employee=employee)

@main.route('/admin/forms/joining/<int:employee_id>', methods=['GET'])
@login_required
def admin_view_joining_form(employee_id):
    """Admin view of joining form."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.NEW_JOINING_FORM
    ).first()

    form = JoiningForm()

    if existing_doc:
        from utils.pdf_parser import extract_joining_form_data
        form_data = extract_joining_form_data(existing_doc.file_path)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_joining_form.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.file_path if existing_doc else None)

@main.route('/admin/forms/form1/<int:employee_id>', methods=['GET'])
@login_required
def admin_view_form1(employee_id):
    """Admin view of Form 1."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    from forms.form1_form import Form1
    form = Form1()

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.FORM_1_NOMINATION
    ).first()

    if existing_doc:
        from utils.pdf_parser import extract_form1_data
        form_data = extract_form1_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_form1.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.description if existing_doc else None)

@main.route('/admin/forms/form11/<int:employee_id>', methods=['GET'])
@login_required
def admin_view_form11(employee_id):
    """Admin view of Form 11."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    from forms.form11_form import Form11
    form = Form11()

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.FORM_11
    ).first()

    if existing_doc:
        from utils.pdf_parser import extract_form11_data
        form_data = extract_form11_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_form11.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.description if existing_doc else None)

@main.route('/admin/forms/pf/<int:employee_id>', methods=['GET'])
@login_required
def admin_view_pf_form(employee_id):
    """Admin view of PF form."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    form = PFForm()

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.PF_FORM
    ).first()

    if existing_doc:
        from utils.pdf_parser import extract_pf_form_data
        form_data = extract_pf_form_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_pf_form.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.description if existing_doc else None)

@main.route('/employer/forms/joining/<int:employee_id>', methods=['GET'])
@login_required
def employer_view_joining_form(employee_id):
    """Employer view of joining form."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.NEW_JOINING_FORM
    ).first()

    form = JoiningForm()

    if existing_doc:
        from utils.pdf_parser import extract_joining_form_data
        form_data = extract_joining_form_data(existing_doc.file_path)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_joining_form.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.file_path if existing_doc else None)

@main.route('/employer/forms/form1/<int:employee_id>', methods=['GET'])
@login_required
def employer_view_form1(employee_id):
    """Employer view of Form 1."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    from forms.form1_form import Form1
    form = Form1()

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.FORM_1_NOMINATION
    ).first()

    if existing_doc:
        from utils.pdf_parser import extract_form1_data
        form_data = extract_form1_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_form1.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.description if existing_doc else None)

@main.route('/employer/forms/form11/<int:employee_id>', methods=['GET'])
@login_required
def employer_view_form11(employee_id):
    """Employer view of Form 11."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    from forms.form11_form import Form11
    form = Form11()

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.FORM_11
    ).first()

    if existing_doc:
        from utils.pdf_parser import extract_form11_data
        form_data = extract_form11_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('shared/view_form11.html',
                          form=form,
                          employee=employee,
                          document=existing_doc,
                          pdf_path=existing_doc.description if existing_doc else None)

@main.route('/employer/forms/pf/<int:employee_id>', methods=['GET'])
@login_required
def employer_view_pf_form(employee_id):
    """Employer view of PF form."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    form = PFForm()

    existing_doc = Document.query.filter_by(
        employee_id=employee.id,
        document_type=DocumentTypes.PF_FORM
    ).first()

    if existing_doc:
        from utils.pdf_parser import extract_pf_form_data
        form_data = extract_pf_form_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('employee/forms/pf_form.html', form=form, employee=employee, view_only=True, pdf_path=existing_doc.description if existing_doc else None)

@main.route('/employer/family-details/<int:employee_id>', methods=['GET'])
@login_required
def employer_view_family_details(employee_id):
    """Employer view of family details."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    # Get family members for this employee
    family_members = FamilyMember.query.filter_by(employee_id=employee.id).all()

    # Find family details document if it exists
    family_document = Document.query.filter_by(
        employee_id=employee.id,
        document_type='family_declaration'
    ).first()

    return render_template('shared/family_details_view.html',
                          employee=employee,
                          family_members=family_members,
                          family_document=family_document,
                          view_type='employer')

@main.route('/employer/view-form/<string:form_type>/<int:employee_id>')
@login_required
def employer_view_form(form_type, employee_id):
    """View a specific form for an employee (employer view)."""
    if not current_user.is_authenticated or not current_user.is_employer():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.login'))

    # Get the employee profile
    employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # Check if this employee belongs to the current employer
    if employee_profile.employer_id != current_user.employer_profile.id:
        flash('You do not have permission to view this employee.', 'danger')
        return redirect(url_for('main.employer_dashboard'))

    # Map form types to document types and titles
    form_mapping = {
        'pf_form': {'document_type': 'pf_form', 'title': 'PF Form'},
        'form1': {'document_type': 'form1_nomination', 'title': 'Form 1 Nomination'},
        'form11': {'document_type': 'form11', 'title': 'Form 11'},
        'joining_form': {'document_type': 'joining_form', 'title': 'New Joining Form'}
    }

    if form_type not in form_mapping:
        flash('Invalid form type.', 'danger')
        return redirect(url_for('main.employer_documents', employee_id=employee_id))

    # Find the document
    document = Document.query.filter_by(
        employee_id=employee_profile.id,
        document_type=form_mapping[form_type]['document_type']
    ).first()

    if not document:
        flash(f"{form_mapping[form_type]['title']} not found for this employee.", 'warning')
        return redirect(url_for('main.employer_documents', employee_id=employee_id))

    # Get the form data
    form = None
    if document.form_data:
        import json
        form = json.loads(document.form_data)

    return render_template('shared/form_view.html',
                          employee=employee_profile,
                          document=document,
                          form=form,
                          form_type=form_type,
                          form_title=form_mapping[form_type]['title'],
                          view_type='employer')

@main.route('/admin/family-details/<int:employee_id>', methods=['GET'])
@login_required
def admin_view_family_details(employee_id):
    """Admin view of family details."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    employee = EmployeeProfile.query.get_or_404(employee_id)

    # Get family members for this employee
    family_members = FamilyMember.query.filter_by(employee_id=employee.id).all()

    # Find family details document if it exists
    family_document = Document.query.filter_by(
        employee_id=employee.id,
        document_type='family_declaration'
    ).first()

    return render_template('shared/family_details_view.html',
                          employee=employee,
                          family_members=family_members,
                          family_document=family_document,
                          view_type='admin')

@main.route('/admin/view-form/<string:form_type>/<int:employee_id>')
@login_required
def admin_view_form(form_type, employee_id):
    """View a specific form for an employee (admin view)."""
    if not current_user.is_authenticated or not current_user.is_admin():
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('main.login'))

    # Get the employee profile
    employee_profile = EmployeeProfile.query.get_or_404(employee_id)

    # Map form types to document types and titles
    form_mapping = {
        'pf_form': {'document_type': 'pf_form', 'title': 'PF Form'},
        'form1': {'document_type': 'form1_nomination', 'title': 'Form 1 Nomination'},
        'form11': {'document_type': 'form11', 'title': 'Form 11'},
        'joining_form': {'document_type': 'joining_form', 'title': 'New Joining Form'}
    }

    if form_type not in form_mapping:
        flash('Invalid form type.', 'danger')
        return redirect(url_for('main.admin_employee_documents', user_id=employee_profile.user_id))

    # Find the document
    document = Document.query.filter_by(
        employee_id=employee_profile.id,
        document_type=form_mapping[form_type]['document_type']
    ).first()

    if not document:
        flash(f"{form_mapping[form_type]['title']} not found for this employee.", 'warning')
        return redirect(url_for('main.admin_employee_documents', user_id=employee_profile.user_id))

    # Get the form data
    form = None
    if document.form_data:
        import json
        form = json.loads(document.form_data)

    return render_template('shared/form_view.html',
                          employee=employee_profile,
                          document=document,
                          form=form,
                          form_type=form_type,
                          form_title=form_mapping[form_type]['title'],
                          view_type='admin')

@main.route('/employee/forms/form11', methods=['GET', 'POST'])
@login_required
def fill_form11():
    """Fill or edit Form 11."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    from forms.form11_form import Form11

    form = Form11()

    # Get the employee profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Check if form already exists
    existing_doc = Document.query.filter_by(
        user_id=current_user.id,
        document_type=DocumentTypes.FORM_11
    ).first()

    if form.validate_on_submit():
        from utils.pdf_generator import generate_form11_pdf
        pdf_path = generate_form11_pdf(form.data, employee)

        if existing_doc:
            existing_doc.description = pdf_path
            existing_doc.status = 'pending'
            existing_doc.updated_at = datetime.utcnow()
            flash('Form 11 updated successfully!', 'success')
        else:
            new_doc = Document(
                user_id=current_user.id,
                employee_id=employee.id,
                document_type=DocumentTypes.FORM_11,
                title=DocumentTypes.FORM_11.replace('_', ' ').title(),
                description=pdf_path,
                status='pending'
            )
            db.session.add(new_doc)
            flash('Form 11 submitted successfully!', 'success')

        db.session.commit()
        # Redirect to pf_form after form11 submission
        return redirect(url_for('main.fill_pf_form'))

    # Pre-populate form with existing data if available
    if existing_doc:
        from utils.pdf_parser import extract_form11_data
        form_data = extract_form11_data(existing_doc.description)
        if form_data:
            for field, value in form_data.items():
                if hasattr(form, field):
                    getattr(form, field).data = value

    return render_template('employee/forms/form11.html', form=form, employee=employee)

@main.route('/employee/upload-document', methods=['POST'])
@login_required
def upload_document():
    """Handle document upload."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    # Debug: Log the request files and form data
    current_app.logger.info(f"Upload document request files: {list(request.files.keys())}")
    current_app.logger.info(f"Upload document request form: {list(request.form.keys())}")

    # Check if we're using the form with document_type and document fields
    if 'document_type' in request.form and 'document' in request.files:
        # This is the modal form submission
        doc_type = request.form['document_type']
        file = request.files['document']

        # Check if a file was actually selected
        if file and file.filename:
            current_app.logger.info(f"Processing file upload from modal form for {doc_type}: {file.filename}")

            # Secure the filename
            filename = secure_filename(file.filename)

            # Create directory structure for user uploads
            user_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
            os.makedirs(user_upload_dir, exist_ok=True)

            # Generate unique filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{doc_type}_{timestamp}_{filename}"

            # Save the file to static folder for easy access
            relative_path = os.path.join('uploads', str(current_user.id), unique_filename)
            # Convert backslashes to forward slashes for web URL compatibility
            relative_path = relative_path.replace('\\', '/')
            full_path = os.path.join(current_app.root_path, 'static', relative_path)
            file.save(full_path)

            # Log file save for debugging
            current_app.logger.info(f"Saved file to {full_path}")

            # Determine content type
            content_type = file.content_type or 'application/octet-stream'

            # Check if document of this type already exists
            existing_doc = Document.query.filter_by(
                employee_id=employee.id,
                document_type=doc_type
            ).first()

            if existing_doc:
                # Update existing document
                existing_doc.description = f"Document uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                existing_doc.status = 'pending'
                existing_doc.uploaded_at = datetime.now()
                existing_doc.content_type = content_type
                existing_doc.file_path = relative_path
                current_app.logger.info(f"Updated document {existing_doc.id} with file path {relative_path}")
            else:
                # Create new document record
                new_doc = Document(
                    user_id=current_user.id,
                    employee_id=employee.id,
                    document_type=doc_type,
                    title=doc_type.replace('_', ' ').title(),
                    description=f"Document uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    status='pending',
                    content_type=content_type,
                    file_path=relative_path
                )
                db.session.add(new_doc)
                current_app.logger.info(f"Created new document for {doc_type} with file path {relative_path}")

            db.session.commit()
            flash('Document uploaded successfully! It is now pending approval.', 'success')
            return redirect(url_for('main.document_center'))
        else:
            flash('No file was selected for upload.', 'warning')
            return redirect(url_for('main.document_center'))

    # If we get here, we're using the old method with multiple file inputs
    files_uploaded = False

    # Process each document type
    for doc_type in DocumentTypes.all_types():
        # Check if the document type is in the request files
        if doc_type in request.files:
            file = request.files[doc_type]
            # Check if a file was actually selected (has a filename)
            if file and file.filename:
                files_uploaded = True
                current_app.logger.info(f"Processing file upload for {doc_type}: {file.filename}")

                # Secure the filename
                filename = secure_filename(file.filename)
                document_number = request.form.get(f'{doc_type}_number', '')

                # Create directory structure for user uploads
                user_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
                os.makedirs(user_upload_dir, exist_ok=True)

                # Generate unique filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{doc_type}_{timestamp}_{filename}"

                # Save the file to static folder for easy access
                relative_path = os.path.join('uploads', str(current_user.id), unique_filename)
                # Convert backslashes to forward slashes for web URL compatibility
                relative_path = relative_path.replace('\\', '/')
                full_path = os.path.join(current_app.root_path, 'static', relative_path)
                file.save(full_path)

                # Log file save for debugging
                current_app.logger.info(f"Saved file to {full_path}")

                # Determine content type
                content_type = file.content_type or 'application/octet-stream'

                # Check if document of this type already exists
                existing_doc = Document.query.filter_by(
                    employee_id=employee.id,
                    document_type=doc_type
                ).first()

                if existing_doc:
                    # Update existing document
                    # Don't set document_name directly as it's a property without a setter
                    existing_doc.description = f"Document uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    existing_doc.status = 'pending'
                    existing_doc.uploaded_at = datetime.now()
                    existing_doc.content_type = content_type

                    # Store the file path in the dedicated field
                    existing_doc.file_path = relative_path

                    # Update document number if provided
                    # We're now using a property for document_number, so this won't cause errors

                    current_app.logger.info(f"Updated document {existing_doc.id} with file path {relative_path}")
                else:
                    # Create new document record
                    new_doc = Document(
                        user_id=current_user.id,
                        employee_id=employee.id,
                        document_type=doc_type,
                        # Don't set document_name directly as it's a property without a setter
                        title=doc_type.replace('_', ' ').title(),
                        description=f"Document uploaded on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        status='pending',
                        content_type=content_type,
                        file_path=relative_path,  # Store path in dedicated field
                        # document_number is now handled via property
                    )
                    db.session.add(new_doc)
                    current_app.logger.info(f"Created new document for {doc_type} with file path {relative_path}")

    if files_uploaded:
        db.session.commit()
        flash('Documents uploaded successfully! They are now pending approval.', 'success')
    else:
        flash('No files were selected for upload.', 'warning')

    return redirect(url_for('main.document_center'))

@main.route('/employee/replace-document', methods=['POST'])
@login_required
def replace_document():
    """Handle document replacement."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    document_id = request.form.get('document_id')
    document_type = request.form.get('document_type')

    if not document_id or not document_type:
        flash('Invalid request parameters. Document ID and type are required.', 'danger')
        current_app.logger.error(f"Replace document called with invalid parameters: id={document_id}, type={document_type}")
        return redirect(url_for('main.document_center'))

    # Get the existing document
    document = Document.query.filter_by(
        id=document_id,
        user_id=current_user.id,
        document_type=document_type
    ).first()

    if not document:
        flash(f'Document not found with ID {document_id} and type {document_type}.', 'danger')
        current_app.logger.error(f"Document not found for replacement: id={document_id}, type={document_type}, user={current_user.id}")
        return redirect(url_for('main.document_center'))

    # Check if file was included in the request
    if 'document' not in request.files:
        flash('No file was included in the request. Please select a file to upload.', 'danger')
        current_app.logger.error(f"No file in request for document replacement: id={document_id}")
        return redirect(url_for('main.document_center'))

    file = request.files['document']

    # Check if a file was selected
    if file.filename == '':
        flash('No file selected. Please choose a file to upload.', 'danger')
        current_app.logger.error(f"Empty filename in document replacement: id={document_id}")
        return redirect(url_for('main.document_center'))

    # Check file type
    allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

    if file_ext not in allowed_extensions:
        flash(f'Invalid file type. Allowed types are: {", ".join(allowed_extensions)}', 'danger')
        current_app.logger.error(f"Invalid file type ({file_ext}) for document replacement: id={document_id}")
        return redirect(url_for('main.document_center'))

    try:
        # Secure the filename
        filename = secure_filename(file.filename)

        # Create directory structure for user uploads
        user_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(current_user.id))
        os.makedirs(user_upload_dir, exist_ok=True)

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{document_type}_{timestamp}_{filename}"

        # Save the file to static folder for easy access
        relative_path = os.path.join('uploads', str(current_user.id), unique_filename)
        # Convert backslashes to forward slashes for web URL compatibility
        relative_path = relative_path.replace('\\', '/')
        full_path = os.path.join(current_app.root_path, 'static', relative_path)

        # Save the file
        file.save(full_path)

        # Verify the file was saved successfully
        if not os.path.exists(full_path):
            raise Exception(f"File was not saved successfully at {full_path}")

        # Get file size for logging
        file_size = os.path.getsize(full_path)

        # Log file save for debugging
        current_app.logger.info(f"Replaced document {document_id} with file at {full_path} (size: {file_size} bytes)")

        # Determine content type
        content_type = file.content_type or 'application/octet-stream'

        # Store the old file path for potential cleanup later
        old_file_path = document.file_path

        # Update document record
        document.file_path = relative_path  # Store in dedicated field
        document.status = 'pending'
        document.updated_at = datetime.now()
        document.content_type = content_type
        document.description = f"Document replaced on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        # Commit the changes
        db.session.commit()

        # Log the successful update
        current_app.logger.info(f"Document record {document_id} updated with new file path: {relative_path}")

        flash('Document replaced successfully! It is now pending approval.', 'success')

        # Optionally, clean up the old file if it exists and is different from the new one
        if old_file_path and old_file_path != relative_path:
            try:
                old_full_path = os.path.join(current_app.root_path, 'static', old_file_path.replace('static/', ''))
                if os.path.exists(old_full_path):
                    # Uncomment the following line if you want to delete old files
                    # os.remove(old_full_path)
                    current_app.logger.info(f"Old file could be removed: {old_full_path}")
            except Exception as e:
                current_app.logger.error(f"Error handling old file: {str(e)}")

    except Exception as e:
        # Log the error
        current_app.logger.error(f"Error replacing document {document_id}: {str(e)}")
        flash(f'An error occurred while replacing the document: {str(e)}', 'danger')

        # Rollback the transaction if needed
        db.session.rollback()

    return redirect(url_for('main.document_center'))

@main.route('/employee/document-preview/<int:document_id>')
@login_required
def employee_document_preview(document_id):
    """Return JSON with preview URL for document."""
    document = Document.query.get_or_404(document_id)

    # Check permission: employee can view own documents, employer/admin can view all
    if not (current_user.is_admin() or current_user.is_employer() or (current_user.is_employee() and document.user_id == current_user.id)):
        return {"error": "Access denied"}, 403

    # Get file path using multiple methods to ensure we find it
    file_path = None

    # Method 1: Check the file_path attribute directly
    if hasattr(document, 'file_path') and document.file_path:
        file_path = document.file_path
        current_app.logger.info(f"Found file_path attribute: {file_path}")

    # Method 2: Check if description contains a path to the file
    elif document.description and ('uploads' in document.description or document.description.startswith('uploads/')):
        file_path = document.description
        # Save the file path to the database for future use
        document.file_path = file_path
        db.session.commit()
        current_app.logger.info(f"Updated document {document_id} file_path from description: {file_path}")

    # Method 3: Use the get_file_path_from_description method
    elif hasattr(document, 'get_file_path_from_description'):
        file_path = document.get_file_path_from_description()
        if file_path:
            current_app.logger.info(f"Found file path from get_file_path_from_description: {file_path}")

    # If we still don't have a file path, check if there are any files in the user's upload directory that match the document type
    if not file_path:
        # Try to find a file in the user's upload directory that matches the document type
        user_upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', str(document.user_id))
        if os.path.exists(user_upload_dir):
            # Look for files that start with the document type
            matching_files = [f for f in os.listdir(user_upload_dir) if f.startswith(document.document_type)]
            if matching_files:
                # Use the most recent file (assuming the files have timestamps in their names)
                matching_files.sort(reverse=True)
                file_path = os.path.join('uploads', str(document.user_id), matching_files[0])
                # Update the document with the found file path
                document.file_path = file_path
                db.session.commit()
                current_app.logger.info(f"Found matching file in user directory: {file_path}")

    if not file_path:
        current_app.logger.error(f"No file path available for document {document_id}")
        return {
            "error": "No file path available",
            "document_id": document_id,
            "document_type": document.document_type,
            "status": document.status
        }, 404

    # Clean up the file path to ensure it's relative to static
    if 'static/' in file_path:
        relative_path = file_path.split('static/')[-1]
    else:
        relative_path = file_path

    # Replace backslashes with forward slashes for URL consistency
    relative_path = relative_path.replace('\\', '/')

    # Construct the full path and check if the file exists
    full_path = os.path.join(current_app.root_path, 'static', relative_path)

    # Log file path for debugging
    current_app.logger.info(f"Document {document_id} file path: {relative_path}, full path: {full_path}")

    # Check if the file exists
    file_exists = os.path.exists(full_path)
    if not file_exists:
        current_app.logger.error(f"File not found at {full_path}")
        return {
            "error": "File not found on server",
            "document_id": document_id,
            "document_type": document.document_type,
            "status": document.status
        }, 404

    # Generate URL for file_path relative to static folder
    # Ensure forward slashes for URL
    file_url = url_for('static', filename=relative_path.replace('\\', '/'))

    # Log preview URL for debugging
    current_app.logger.info(f"Document {document_id} preview URL: {file_url}")

    # Get file extension to determine content type
    file_ext = relative_path.split('.')[-1].lower() if '.' in relative_path else ''
    content_type = 'application/pdf'
    if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
        content_type = f'image/{file_ext}'

    # Get file size for additional information
    file_size = os.path.getsize(full_path)

    # Get document name from property or fallback to basename
    document_name = document.document_name or os.path.basename(relative_path)

    return {
        "preview_url": file_url,
        "content_type": content_type,
        "document_name": document_name,
        "status": document.status,
        "file_size": file_size,
        "last_modified": datetime.fromtimestamp(os.path.getmtime(full_path)).strftime('%Y-%m-%d %H:%M:%S')
    }

@main.route('/employee/remove-family-member', methods=['POST'])
@login_required
def remove_family_member():
    """Remove a family member from the employee's profile."""
    if not current_user.is_employee():
        flash('Access denied. Employee privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get the employee's profile
    employee = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not employee:
        flash('Please complete your profile first.', 'warning')
        return redirect(url_for('main.profile'))

    member_id = request.form.get('member_id')
    if not member_id:
        flash('Invalid request parameters.', 'danger')
        return redirect(url_for('main.manage_family_members'))

    # Get the family member
    family_member = FamilyMember.query.filter_by(
        id=member_id,
        employee_id=employee.id
    ).first()

    if not family_member:
        flash('Family member not found.', 'danger')
        return redirect(url_for('main.manage_family_members'))

    try:
        # Delete associated documents if they exist
        if family_member.photo_path:
            try:
                photo_path = os.path.join(current_app.root_path, 'static', family_member.photo_path)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
            except Exception as e:
                current_app.logger.error(f"Error removing photo file: {str(e)}")

        if family_member.aadhar_card_path:
            try:
                aadhar_path = os.path.join(current_app.root_path, 'static', family_member.aadhar_card_path)
                if os.path.exists(aadhar_path):
                    os.remove(aadhar_path)
            except Exception as e:
                current_app.logger.error(f"Error removing aadhar card file: {str(e)}")

        # Delete any associated document records
        aadhar_docs = Document.query.filter_by(
            user_id=current_user.id,
            document_type='family_aadhar_card',
            title=f"{family_member.name} - Aadhar Card"
        ).all()

        for doc in aadhar_docs:
            db.session.delete(doc)

        # Delete the family member
        db.session.delete(family_member)
        db.session.commit()
        flash(f'Family member {family_member.name} removed successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error removing family member: {str(e)}")
        flash('Error removing family member. Please try again.', 'danger')

    return redirect(url_for('main.manage_family_members'))

@main.route('/employer/view-employee/')
@main.route('/employer/view-employee/<int:employee_id>')
@login_required
def employer_view_employee(employee_id=None):
    """Employer route to view employee profiles."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    if not employee_id:
        flash('Employee ID is required.', 'warning')
        return redirect(url_for('main.employer_employees'))

    # Redirect to the employee profile view
    return redirect(url_for('main.view_employee_profile', employee_id=employee_id))

@main.route('/employer/approve-document/<int:document_id>')
@login_required
def approve_document(document_id):
    """Approve a document."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    document = Document.query.get_or_404(document_id)
    document.status = 'approved'
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.now()

    # Log approval for debugging
    current_app.logger.info(f"Document {document_id} approved by employer {current_user.id}")

    db.session.commit()

    flash('Document approved successfully!', 'success')

    # Get the employee_id to redirect back to document center
    employee_id = document.employee_id
    return redirect(url_for('main.document_center', employee_id=employee_id))

@main.route('/employer/reject-document/<int:document_id>')
@login_required
def reject_document(document_id):
    """Reject a document."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    document = Document.query.get_or_404(document_id)
    document.status = 'rejected'
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.now()

    # Optionally add feedback (could be expanded with a form)
    document.feedback = "Document was rejected. Please resubmit."

    # Log rejection for debugging
    current_app.logger.info(f"Document {document_id} rejected by employer {current_user.id}")

    db.session.commit()

    flash('Document rejected successfully!', 'success')

    # Get the employee_id to redirect back to document center
    employee_id = document.employee_id
    return redirect(url_for('main.document_center', employee_id=employee_id))
