from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from datetime import datetime
import uuid
import random
import string

from extensions import db
from models import Client, EmployeeProfile, User
from forms import ClientForm
from blueprints import clients

@clients.route('/admin/clients')
@login_required
def admin_clients():
    """Admin clients management route."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all clients
    all_clients = Client.query.all()
    return render_template('admin/clients.html', clients=all_clients)

@clients.route('/admin/add-client', methods=['GET', 'POST'])
@login_required
def admin_add_client():
    """Add a new client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    form = ClientForm()
    if form.validate_on_submit():
        # Create new client
        client = Client(
            name=form.name.data,
            code=form.code.data.upper(),  # Store code in uppercase
            description=form.description.data,
            contact_person=form.contact_person.data,
            contact_email=form.contact_email.data,
            contact_phone=form.contact_phone.data,
            address=form.address.data,
            created_by=current_user.id,
            is_active=form.is_active.data
        )
        db.session.add(client)
        db.session.commit()

        flash(f'Client "{client.name}" added successfully!', 'success')
        return redirect(url_for('clients.admin_clients'))

    return render_template('admin/add_client.html', form=form)

@clients.route('/admin/edit-client/<int:client_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_client(client_id):
    """Edit a client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)

    # Remove validation for code field when editing
    del form.code.validators_

    if form.validate_on_submit():
        # Update client information
        client.name = form.name.data
        # Don't update the code as it's used for employee IDs
        client.description = form.description.data
        client.contact_person = form.contact_person.data
        client.contact_email = form.contact_email.data
        client.contact_phone = form.contact_phone.data
        client.address = form.address.data
        client.is_active = form.is_active.data

        db.session.commit()

        flash(f'Client "{client.name}" updated successfully!', 'success')
        return redirect(url_for('clients.admin_clients'))

    return render_template('admin/edit_client.html', form=form, client=client)

@clients.route('/admin/toggle-client-status/<int:client_id>')
@login_required
def admin_toggle_client_status(client_id):
    """Toggle client active status."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)

    # Toggle the active status
    client.is_active = not client.is_active
    db.session.commit()

    status = 'activated' if client.is_active else 'deactivated'
    flash(f'Client "{client.name}" has been {status}.', 'success')
    return redirect(url_for('clients.admin_clients'))

@clients.route('/admin/remove-client/<int:client_id>', methods=['POST'])
@login_required
def admin_remove_client(client_id):
    """Remove a client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)

    # Check if client has employees
    if client.employees:
        flash(f'Cannot delete client "{client.name}" because it has associated employees. Please reassign or delete the employees first.', 'danger')
        return redirect(url_for('clients.admin_clients'))

    db.session.delete(client)
    db.session.commit()

    flash(f'Client "{client.name}" removed successfully!', 'success')
    return redirect(url_for('clients.admin_clients'))

@clients.route('/admin/client-employees/<int:client_id>')
@login_required
def admin_client_employees(client_id):
    """View employees for a specific client."""
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)
    employees = EmployeeProfile.query.filter_by(client_id=client_id).all()

    return render_template('admin/client_employees.html', client=client, employees=employees)

@clients.route('/employer/clients')
@login_required
def employer_clients():
    """Employer clients management route."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    # Get all clients
    all_clients = Client.query.filter_by(is_active=True).all()
    return render_template('employer/clients.html', clients=all_clients)

@clients.route('/employer/client-employees/<int:client_id>')
@login_required
def employer_client_employees(client_id):
    """View employees for a specific client (employer view)."""
    if not current_user.is_employer():
        flash('Access denied. Employer privileges required.', 'danger')
        return redirect(url_for('main.index'))

    client = Client.query.get_or_404(client_id)
    employees = EmployeeProfile.query.filter_by(client_id=client_id).all()

    # Ensure user relationships are loaded
    for profile in employees:
        if profile.user_id:
            user = User.query.get(profile.user_id)
            if user:
                profile.user = user

    return render_template('employer/client_employees.html', client=client, employees=employees)

def generate_employee_code(client_code):
    """Generate a unique employee code based on client code."""
    # Get the highest employee code for this client
    highest_code = db.session.query(
        db.func.max(EmployeeProfile.employee_code)
    ).filter(
        EmployeeProfile.employee_code.like(f"{client_code}%")
    ).scalar()

    if highest_code:
        # Extract the numeric part and increment
        try:
            numeric_part = int(highest_code[len(client_code):])
            new_numeric_part = numeric_part + 1
        except ValueError:
            # If parsing fails, start with 1
            new_numeric_part = 1
    else:
        # No existing codes, start with 1
        new_numeric_part = 1

    # Format with leading zeros (e.g., ABC001)
    return f"{client_code}{new_numeric_part:03d}"
