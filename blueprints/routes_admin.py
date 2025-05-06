from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from models import User, EmployeeProfile, EmployerProfile, Document
from extensions import db
from functools import wraps
from datetime import datetime
from werkzeug.security import generate_password_hash
import pandas as pd
import os
from werkzeug.utils import secure_filename
import uuid
import string
import random

admin = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_employees = User.query.filter_by(role='employee').count()
    total_employers = User.query.filter_by(role='employer').count()
    pending_documents = Document.query.filter_by(status='pending').count()

    return render_template('admin/dashboard.html',
                         total_employees=total_employees,
                         total_employers=total_employers,
                         pending_documents=pending_documents)

@admin.route('/employers')
@login_required
@admin_required
def employers():
    employers = User.query.filter_by(role='employer').all()
    return render_template('admin/employers.html', employers=employers)

@admin.route('/employees')
@login_required
@admin_required
def employees():
    employees = User.query.filter_by(role='employee').all()
    return render_template('admin/employees.html', employees=employees)

@admin.route('/documents')
@login_required
@admin_required
def documents():
    documents = Document.query.all()
    return render_template('admin/documents.html', documents=documents)

@admin.route('/documents/<int:doc_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    document.status = 'approved'
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash('Document has been approved', 'success')
    return redirect(url_for('admin.documents'))

@admin.route('/documents/<int:doc_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    document.status = 'rejected'
    document.reviewed_by = current_user.id
    document.reviewed_at = datetime.utcnow()
    db.session.commit()
    flash('Document has been rejected', 'success')
    return redirect(url_for('admin.documents'))

@admin.route('/add-employee', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employee():
    """Add a new employee."""
    if request.method == 'POST':
        # Generate a random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create user
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            role='employee',
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        # Create employee profile
        profile = EmployeeProfile(
            user_id=user.id,
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            phone_number=request.form.get('phone_number', ''),
            department=request.form.get('department', ''),
            position=request.form.get('position', '')
        )
        db.session.add(profile)
        db.session.commit()

        flash(f'Employee added successfully! Username: {user.username}, Password: {password}', 'success')
        return redirect(url_for('admin.employees'))

    return render_template('admin/add_employee.html')

@admin.route('/add-employer', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employer():
    """Add a new employer."""
    if request.method == 'POST':
        # Generate a random password
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # Create user
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            role='employer',
            is_active=True
        )
        user.set_password(password)
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
        return redirect(url_for('admin.employers'))

    return render_template('admin/add_employer.html')

@admin.route('/remove-employee/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_employee(user_id):
    """Remove an employee."""
    user = User.query.get_or_404(user_id)
    if user.role != 'employee':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.employees'))

    db.session.delete(user)
    db.session.commit()

    flash('Employee removed successfully!', 'success')
    return redirect(url_for('admin.employees'))

@admin.route('/remove-employer/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def remove_employer(user_id):
    """Remove an employer."""
    user = User.query.get_or_404(user_id)
    if user.role != 'employer':
        flash('Invalid user role.', 'danger')
        return redirect(url_for('admin.employers'))

    db.session.delete(user)
    db.session.commit()

    flash('Employer removed successfully!', 'success')
    return redirect(url_for('admin.employers'))

@admin.route('/bulk-employee-upload', methods=['GET', 'POST'])
@login_required
@admin_required
def bulk_employee_upload():
    """Upload bulk employee data from Excel file."""
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
                            error_count += 1
                            continue

                        # Generate username from email
                        username = row['email'].split('@')[0]
                        # Check if username exists, if so, add random suffix
                        if User.query.filter_by(username=username).first():
                            username = f"{username}_{uuid.uuid4().hex[:6]}"

                        # Generate random password
                        password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

                        # Create user
                        user = User(
                            username=username,
                            email=row['email'],
                            role='employee',
                            is_active=True
                        )
                        user.set_password(password)
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
                return redirect(url_for('admin.employees'))

            except Exception as e:
                flash(f'Error processing Excel file: {str(e)}', 'danger')
                if os.path.exists(file_path):
                    os.remove(file_path)
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'danger')
            return redirect(request.url)

    return render_template('admin/bulk_employee_upload.html')