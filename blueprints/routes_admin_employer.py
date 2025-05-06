from flask import render_template, abort
from flask_login import login_required
from sqlalchemy import or_
import re
from models import EmployeeProfile
from . import admin_employer
from forms import EmployeeSearchForm
from decorators import employer_required

@admin_employer.route('/search', methods=['GET', 'POST'])
@login_required
@employer_required
def employer_search_employee():
    form = EmployeeSearchForm()
    if form.validate_on_submit():
        query = form.query.data.strip()
        
        # Check if query is an Aadhar number (12 digits)
        if re.match(r'^\d{12}$', query):
            employees = EmployeeProfile.query.filter_by(aadhar_number=query).all()
        # Check if query is an Employee ID (EMP followed by numbers)
        elif re.match(r'^EMP\d+$', query, re.IGNORECASE):
            employees = EmployeeProfile.query.filter_by(employee_id=query.upper()).all()
        # Otherwise search by name
        else:
            employees = EmployeeProfile.query.filter(
                or_(
                    EmployeeProfile.first_name.ilike(f'%{query}%'),
                    EmployeeProfile.last_name.ilike(f'%{query}%')
                )
            ).all()
        
        return render_template('employer/search_employee.html', 
                            form=form, 
                            employees=employees,
                            search_performed=True)
    
    return render_template('employer/search_employee.html', 
                         form=form,
                         search_performed=False)

@admin_employer.route('/view-employee/<string:employee_id>')
@login_required
@employer_required
def employer_view_employee(employee_id):
    employee = EmployeeProfile.query.filter_by(employee_id=employee_id).first_or_404()
    return render_template('employer/view_employee.html', employee=employee) 