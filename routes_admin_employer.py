from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import re
import uuid

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, Document, NewsUpdate, ROLE_ADMIN, ROLE_EMPLOYER, ROLE_EMPLOYEE
from forms import EmployeeSearchForm, CreateEmployeeForm, EmployeeProfileEditForm, NewsUpdateForm, RegisterForm
from utils import DocumentTypes


# Admin search functionality
@app.route('/admin/search', methods=['GET', 'POST'])
@login_required
def admin_search():
    """Search for employees or employers by various criteria."""
    if not current_user.is_admin():
        flash('Access denied. This feature is for admin users only.', 'error')
        return redirect(url_for('index'))

    form = EmployeeSearchForm()
    results = []
    search_performed = False

    if form.validate_on_submit() or request.args.get('query'):
        search_performed = True
        query = form.query.data or request.args.get('query', '')
        search_type = form.search_type.data or request.args.get('search_type', 'all')

        # Determine search type based on query format
        if not search_type or search_type == 'auto':
            if re.match(r'^\d{12}$', query):  # 12 digit Aadhar number
                search_type = 'aadhar'
            elif query.startswith('EMP'):  # Employee ID starts with EMP
                search_type = 'employee_id'
            elif '@' in query:  # Email contains @
                search_type = 'email'
            else:
                search_type = 'name'  # Default to name search

        # Perform the search based on type
        if search_type == 'aadhar':
            # Search by Aadhar ID
            employee_profiles = EmployeeProfile.query.filter(EmployeeProfile.aadhar_id.like(f'%{query}%')).all()
            for profile in employee_profiles:
                user = User.query.get(profile.user_id)
                if user:
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': profile.employee_id,
                        'aadhar_id': profile.aadhar_id,
                        'name': f"{profile.first_name} {profile.last_name}",
                        'profile_type': 'employee'
                    })

        elif search_type == 'employee_id':
            # Search by Employee ID
            employee_profiles = EmployeeProfile.query.filter(EmployeeProfile.employee_id.like(f'%{query}%')).all()
            for profile in employee_profiles:
                user = User.query.get(profile.user_id)
                if user:
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': profile.employee_id,
                        'aadhar_id': profile.aadhar_id,
                        'name': f"{profile.first_name} {profile.last_name}",
                        'profile_type': 'employee'
                    })

        elif search_type == 'email':
            # Search by email
            users = User.query.filter(User.email.like(f'%{query}%')).all()
            for user in users:
                # Check if employee or employer
                employee_profile = EmployeeProfile.query.filter_by(user_id=user.id).first()
                employer_profile = EmployerProfile.query.filter_by(user_id=user.id).first()

                if employee_profile:
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': employee_profile.employee_id,
                        'aadhar_id': employee_profile.aadhar_id,
                        'name': f"{employee_profile.first_name} {employee_profile.last_name}",
                        'profile_type': 'employee'
                    })
                elif employer_profile:
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'company_name': employer_profile.company_name,
                        'profile_type': 'employer'
                    })
                else:
                    # User with no profile (possibly admin)
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'profile_type': 'admin'
                    })

        elif search_type == 'name':
            # Search by name in both employee and employer profiles
            # First search employee profiles
            employee_profiles = EmployeeProfile.query.filter(
                db.or_(
                    EmployeeProfile.first_name.like(f'%{query}%'),
                    EmployeeProfile.last_name.like(f'%{query}%')
                )
            ).all()

            for profile in employee_profiles:
                user = User.query.get(profile.user_id)
                if user:
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': profile.employee_id,
                        'aadhar_id': profile.aadhar_id,
                        'name': f"{profile.first_name} {profile.last_name}",
                        'profile_type': 'employee'
                    })

            # Then search employer profiles by company name
            employer_profiles = EmployerProfile.query.filter(
                EmployerProfile.company_name.like(f'%{query}%')
            ).all()

            for profile in employer_profiles:
                user = User.query.get(profile.user_id)
                if user:
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'company_name': profile.company_name,
                        'profile_type': 'employer'
                    })

        elif search_type == 'all':
            # Search across all fields
            # Email search
            users = User.query.filter(User.email.like(f'%{query}%')).all()
            for user in users:
                employee_profile = EmployeeProfile.query.filter_by(user_id=user.id).first()
                employer_profile = EmployerProfile.query.filter_by(user_id=user.id).first()

                if employee_profile:
                    if not any(r['id'] == user.id for r in results):  # Avoid duplicates
                        results.append({
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'role': user.role,
                            'employee_id': employee_profile.employee_id,
                            'aadhar_id': employee_profile.aadhar_id,
                            'name': f"{employee_profile.first_name} {employee_profile.last_name}",
                            'profile_type': 'employee'
                        })
                elif employer_profile:
                    if not any(r['id'] == user.id for r in results):  # Avoid duplicates
                        results.append({
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'role': user.role,
                            'company_name': employer_profile.company_name,
                            'profile_type': 'employer'
                        })
                else:
                    if not any(r['id'] == user.id for r in results):  # Avoid duplicates
                        results.append({
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                            'role': user.role,
                            'profile_type': 'admin'
                        })

            # Employee ID search
            employee_profiles = EmployeeProfile.query.filter(EmployeeProfile.employee_id.like(f'%{query}%')).all()
            for profile in employee_profiles:
                user = User.query.get(profile.user_id)
                if user and not any(r['id'] == user.id for r in results):  # Avoid duplicates
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': profile.employee_id,
                        'aadhar_id': profile.aadhar_id,
                        'name': f"{profile.first_name} {profile.last_name}",
                        'profile_type': 'employee'
                    })

            # Aadhar ID search
            employee_profiles = EmployeeProfile.query.filter(EmployeeProfile.aadhar_id.like(f'%{query}%')).all()
            for profile in employee_profiles:
                user = User.query.get(profile.user_id)
                if user and not any(r['id'] == user.id for r in results):  # Avoid duplicates
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': profile.employee_id,
                        'aadhar_id': profile.aadhar_id,
                        'name': f"{profile.first_name} {profile.last_name}",
                        'profile_type': 'employee'
                    })

            # Name search for employees
            employee_profiles = EmployeeProfile.query.filter(
                db.or_(
                    EmployeeProfile.first_name.like(f'%{query}%'),
                    EmployeeProfile.last_name.like(f'%{query}%')
                )
            ).all()

            for profile in employee_profiles:
                user = User.query.get(profile.user_id)
                if user and not any(r['id'] == user.id for r in results):  # Avoid duplicates
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'employee_id': profile.employee_id,
                        'aadhar_id': profile.aadhar_id,
                        'name': f"{profile.first_name} {profile.last_name}",
                        'profile_type': 'employee'
                    })

            # Company name search for employers
            employer_profiles = EmployerProfile.query.filter(
                EmployerProfile.company_name.like(f'%{query}%')
            ).all()

            for profile in employer_profiles:
                user = User.query.get(profile.user_id)
                if user and not any(r['id'] == user.id for r in results):  # Avoid duplicates
                    results.append({
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role,
                        'company_name': profile.company_name,
                        'profile_type': 'employer'
                    })

    return render_template('admin/search.html', 
                          form=form, 
                          results=results, 
                          search_performed=search_performed,
                          query=form.query.data if form.validate_on_submit() else request.args.get('query', ''))


# API endpoint for quick search (used in admin dashboard)
@app.route('/api/search', methods=['GET'])
@login_required
def api_search():
    """API endpoint for quick search in the admin dashboard."""
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    query = request.args.get('q', '')
    results = []

    if len(query) >= 3:  # Only search if at least 3 characters
        # Search users
        users = User.query.filter(
            db.or_(
                User.username.like(f'%{query}%'),
                User.email.like(f'%{query}%')
            )
        ).limit(10).all()

        # Search employee profiles
        employee_profiles = EmployeeProfile.query.filter(
            db.or_(
                EmployeeProfile.employee_id.like(f'%{query}%'),
                EmployeeProfile.aadhar_id.like(f'%{query}%'),
                EmployeeProfile.first_name.like(f'%{query}%'),
                EmployeeProfile.last_name.like(f'%{query}%')
            )
        ).limit(10).all()

        # Search employer profiles
        employer_profiles = EmployerProfile.query.filter(
            db.or_(
                EmployerProfile.company_name.like(f'%{query}%')
            )
        ).limit(10).all()

        # Combine results
        for user in users:
            results.append({
                'id': user.id,
                'text': f"{user.username} ({user.email})",
                'url': url_for('view_user', user_id=user.id)
            })

        for profile in employee_profiles:
            user = User.query.get(profile.user_id)
            if user:
                results.append({
                    'id': user.id,
                    'text': f"{profile.first_name} {profile.last_name} - {profile.employee_id}",
                    'url': url_for('view_employee', employee_id=profile.id)
                })

        for profile in employer_profiles:
            user = User.query.get(profile.user_id)
            if user:
                results.append({
                    'id': user.id,
                    'text': f"{profile.company_name}",
                    'url': url_for('view_employer', employer_id=profile.id)
                })

    return jsonify(results)


# Employer functionality to create employee IDs
@app.route('/employer/create-employee', methods=['GET', 'POST'])
@login_required
def create_employee():
    """Create a new employee account with generated Employee ID."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    form = CreateEmployeeForm()

    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                flash(f'Username {form.username.data} is already taken.', 'error')
            else:
                flash(f'Email {form.email.data} is already registered.', 'error')
            return redirect(url_for('create_employee'))

        # Check if Aadhar ID already exists
        existing_profile = EmployeeProfile.query.filter_by(aadhar_id=form.aadhar_id.data).first()
        if existing_profile:
            flash(f'Aadhar ID {form.aadhar_id.data} is already registered.', 'error')
            return redirect(url_for('create_employee'))

        # Generate employee ID (format: EMP-YYMMDD-XXXX where XXXX is random)
        today = datetime.now().strftime('%y%m%d')
        random_suffix = str(uuid.uuid4().int)[:4]  # Get first 4 digits of a UUID
        employee_id = f"EMP-{today}-{random_suffix}"

        # Create the user with Employee role
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=ROLE_EMPLOYEE,
            first_login=True
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()  # Flush to get the user ID

        # Create the employee profile
        employee_profile = EmployeeProfile(
            user_id=user.id,
            aadhar_id=form.aadhar_id.data,
            employee_id=employee_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            date_of_birth=form.date_of_birth.data,
            phone_number=form.phone_number.data
        )
        db.session.add(employee_profile)
        db.session.commit()

        flash(f'Employee account created successfully! Employee ID: {employee_id}', 'success')
        return redirect(url_for('employer_dashboard'))

    return render_template('employer/create_employee.html', form=form)


# View/Edit Employee Profile as Employer
@app.route('/employer/view-employee/<string:employee_id>', methods=['GET'])
@login_required
def employer_view_employee(employee_id):
    """View employee details as an employer."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    # Find the employee by their employee ID
    employee_profile = EmployeeProfile.query.filter_by(employee_id=employee_id).first()

    if not employee_profile:
        flash('Employee not found.', 'error')
        return redirect(url_for('employer_dashboard'))

    # Get user data
    user = User.query.get(employee_profile.user_id)

    # Get documents
    documents = Document.query.filter_by(employee_id=employee_profile.id).all()

    # Group documents by type
    document_groups = {
        'identity': [],
        'financial': [],
        'forms': [],
        'verification': []
    }

    for doc in documents:
        if doc.document_type in [DocumentTypes.AADHAR_CARD, DocumentTypes.PAN_CARD, DocumentTypes.PHOTO]:
            document_groups['identity'].append(doc)
        elif doc.document_type == DocumentTypes.BANK_PASSBOOK:
            document_groups['financial'].append(doc)
        elif doc.document_type in [DocumentTypes.NEW_JOINING_FORM, DocumentTypes.PF_FORM, DocumentTypes.FORM_1_NOMINATION, DocumentTypes.FORM_11]:
            document_groups['forms'].append(doc)
        elif doc.document_type in [DocumentTypes.POLICE_VERIFICATION, DocumentTypes.MEDICAL_CERTIFICATE, DocumentTypes.FAMILY_DECLARATION]:
            document_groups['verification'].append(doc)

    return render_template('employer/view_employee.html', 
                          employee=employee_profile, 
                          user=user, 
                          document_groups=document_groups)


# Search Employees by Aadhar or Employee ID
@app.route('/employer/search-employee', methods=['GET', 'POST'])
@login_required
def employer_search_employee():
    """Search for employees by Aadhar or Employee ID."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    form = EmployeeSearchForm()
    results = []
    search_performed = False

    if form.validate_on_submit() or request.args.get('query'):
        search_performed = True
        query = form.query.data or request.args.get('query', '')
        search_type = form.search_type.data or request.args.get('search_type', 'auto')

        # Determine search type based on query format
        if search_type == 'auto':
            if re.match(r'^\d{12}$', query):  # 12 digit Aadhar number
                search_type = 'aadhar'
            elif query.startswith('EMP'):  # Employee ID starts with EMP
                search_type = 'employee_id'
            else:
                search_type = 'name'  # Default to name search

        # Perform the search based on type
        if search_type == 'aadhar':
            # Search by Aadhar ID
            employee_profiles = EmployeeProfile.query.filter(EmployeeProfile.aadhar_id.like(f'%{query}%')).all()
        elif search_type == 'employee_id':
            # Search by Employee ID
            employee_profiles = EmployeeProfile.query.filter(EmployeeProfile.employee_id.like(f'%{query}%')).all()
        else:  # name search
            # Search by name
            employee_profiles = EmployeeProfile.query.filter(
                db.or_(
                    EmployeeProfile.first_name.like(f'%{query}%'),
                    EmployeeProfile.last_name.like(f'%{query}%')
                )
            ).all()

        # Process results
        for profile in employee_profiles:
            user = User.query.get(profile.user_id)
            if user:
                # Get document completion percentage
                from utils import get_document_completion_percentage
                completion = get_document_completion_percentage(profile.id)

                results.append({
                    'id': profile.id,
                    'employee_id': profile.employee_id,
                    'aadhar_id': profile.aadhar_id,
                    'name': f"{profile.first_name} {profile.last_name}",
                    'email': user.email,
                    'phone': profile.phone_number,
                    'department': profile.department,
                    'position': profile.position,
                    'joining_date': profile.joining_date,
                    'document_completion': completion
                })

    return render_template('employer/search_employee.html', 
                          form=form, 
                          results=results, 
                          search_performed=search_performed,
                          query=form.query.data if form.validate_on_submit() else request.args.get('query', ''))


# Employer news management routes
@app.route('/employer/news', methods=['GET'])
@login_required
def employer_news_list():
    """List all news updates for an employer."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    # Get the employer profile
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()

    if employer_profile:
        # Get news updates created by this employer
        news_updates = NewsUpdate.query.filter_by(employer_id=employer_profile.id).order_by(NewsUpdate.published_date.desc()).all()
    else:
        # Admin view - get all news updates
        news_updates = NewsUpdate.query.order_by(NewsUpdate.published_date.desc()).all()

    return render_template('employer/news_list.html', 
                           news_updates=news_updates,
                           employer_profile=employer_profile)


@app.route('/employer/news/create', methods=['GET', 'POST'])
@login_required
def create_news_update():
    """Create a new news update."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    form = NewsUpdateForm()

    if form.validate_on_submit():
        # Get employer profile
        employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()

        if not employer_profile and not current_user.is_admin():
            flash('Cannot create a news update without an employer profile.', 'error')
            return redirect(url_for('employer_dashboard'))

        # Create news update
        news = NewsUpdate(
            title=form.title.data,
            content=form.content.data,
            employer_id=employer_profile.id if employer_profile else 1,  # Use ID 1 for admin
            is_active=form.is_active.data,
            link=form.link.data,
            link_text=form.link_text.data,
            is_interview_notice=form.is_interview_notice.data
        )

        if form.is_interview_notice.data:
            news.location_address = form.location_address.data
            news.interview_date = form.interview_date.data

        db.session.add(news)
        db.session.commit()

        flash('News update created successfully!', 'success')
        return redirect(url_for('employer_news_list'))

    return render_template('employer/create_news.html', form=form)


@app.route('/employer/news/<int:news_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_news_update(news_id):
    """Edit an existing news update."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    news = NewsUpdate.query.get_or_404(news_id)

    # Check if the current user is the employer who created this news or an admin
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not current_user.is_admin() and (not employer_profile or employer_profile.id != news.employer_id):
        flash('You do not have permission to edit this news update.', 'error')
        return redirect(url_for('employer_news_list'))

    form = NewsUpdateForm(obj=news)

    if form.validate_on_submit():
        # Update the news
        news.title = form.title.data
        news.content = form.content.data
        news.is_active = form.is_active.data
        news.link = form.link.data
        news.link_text = form.link_text.data
        news.is_interview_notice = form.is_interview_notice.data

        if form.is_interview_notice.data:
            news.location_address = form.location_address.data
            news.interview_date = form.interview_date.data
        else:
            news.location_address = None
            news.interview_date = None

        db.session.commit()

        flash('News update edited successfully!', 'success')
        return redirect(url_for('employer_news_list'))

    return render_template('employer/edit_news.html', form=form, news=news)


@app.route('/employer/news/<int:news_id>/delete', methods=['POST'])
@login_required
def delete_news_update(news_id):
    """Delete a news update."""
    if not current_user.is_employer() and not current_user.is_admin():
        flash('Access denied. This feature is for employers and admin users only.', 'error')
        return redirect(url_for('index'))

    news = NewsUpdate.query.get_or_404(news_id)

    # Check if the current user is the employer who created this news or an admin
    employer_profile = EmployerProfile.query.filter_by(user_id=current_user.id).first()
    if not current_user.is_admin() and (not employer_profile or employer_profile.id != news.employer_id):
        flash('You do not have permission to delete this news update.', 'error')
        return redirect(url_for('employer_news_list'))

    db.session.delete(news)
    db.session.commit()

    flash('News update deleted successfully!', 'success')
    return redirect(url_for('employer_news_list'))


@app.route('/news/<int:news_id>', methods=['GET'])
def news_detail(news_id):
    """View a specific news update."""
    news = NewsUpdate.query.get_or_404(news_id)

    return render_template('news/detail.html', news=news)


# Admin functionality to create new employer accounts
@app.route('/admin/create-employer', methods=['GET', 'POST'])
@login_required
def create_employer():
    """Create a new employer account."""
    if not current_user.is_admin():
        flash('Access denied. This feature is for admin users only.', 'error')
        return redirect(url_for('index'))

    form = RegisterForm()  # Using the standard registration form

    if form.validate_on_submit():
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()

        if existing_user:
            if existing_user.username == form.username.data:
                form.username.errors.append('Username already exists. Please choose a different one.')
            if existing_user.email == form.email.data:
                form.email.errors.append('Email already exists. Please use a different one.')
            return render_template('admin/create_employer.html', form=form)

        # Generate a unique company ID
        company_id = f"EMP{uuid.uuid4().hex[:8].upper()}"

        # Create user
        user = User(
            username=form.username.data, 
            email=form.email.data,
            role=ROLE_EMPLOYER
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.flush()  # Flush to get the user.id without committing

        # Create employer profile
        employer_profile = EmployerProfile(
            user_id=user.id,
            company_name=form.username.data,  # Default company name is the username
            company_id=company_id,
            department='HR',  # Default department
            contact_email=form.email.data
        )

        db.session.add(employer_profile)
        db.session.commit()

        flash(f'Employer account created successfully! Company ID: {company_id}', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin/create_employer.html', form=form)