import os
from fpdf import FPDF
from datetime import datetime
from flask import current_app
from utils.path_utils import normalize_path

def generate_joining_form_pdf(form_data, employee):
    """
    Generate a PDF for the joining form using form data and employee info.
    Saves the PDF under static/uploads/joining_forms and returns the relative file path.
    """
    # Create directory for joining forms
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'joining_forms')
    os.makedirs(upload_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"joining_form_{employee.id}_{timestamp}.pdf"
    filepath = os.path.join(upload_dir, filename)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.cell(0, 10, "New Joining Application Form", ln=True, align='C')
    pdf.ln(10)

    # Employee info
    pdf.cell(0, 10, f"Employee: {employee.first_name} {employee.last_name}", ln=True)
    pdf.cell(0, 10, f"Employee ID: {employee.id}", ln=True)
    pdf.ln(10)

    # Form data
    for key, value in form_data.items():
        pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Save PDF
    pdf.output(filepath)

    # Return normalized relative path for storage in DB and URL generation
    relative_path = normalize_path(filepath)

    # Log the file creation for debugging
    current_app.logger.info(f"Generated joining form PDF at: {filepath}")
    current_app.logger.info(f"Normalized path for storage: {relative_path}")

    return relative_path

def generate_form1_pdf(form_data, employee):
    """
    Generate a PDF for Form 1 (Nomination & Declaration) using form data and employee info.
    Saves the PDF under static/uploads/form1 and returns the relative file path.
    """
    # Create directory for form1
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'form1')
    os.makedirs(upload_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"form1_{employee.id}_{timestamp}.pdf"
    filepath = os.path.join(upload_dir, filename)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.cell(0, 10, "Form 1 - Nomination & Declaration", ln=True, align='C')
    pdf.ln(10)

    # Employee info
    pdf.cell(0, 10, f"Employee: {employee.first_name} {employee.last_name}", ln=True)
    pdf.cell(0, 10, f"Employee ID: {employee.id}", ln=True)
    pdf.ln(10)

    # Form data
    for key, value in form_data.items():
        if key not in ['csrf_token', 'submit']:
            pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Save PDF
    pdf.output(filepath)

    # Return normalized relative path for storage in DB and URL generation
    relative_path = normalize_path(filepath)

    # Log the file creation for debugging
    current_app.logger.info(f"Generated Form 1 PDF at: {filepath}")
    current_app.logger.info(f"Normalized path for storage: {relative_path}")

    return relative_path

def generate_form11_pdf(form_data, employee):
    """
    Generate a PDF for Form 11 (Revised) using form data and employee info.
    Saves the PDF under static/uploads/form11 and returns the relative file path.
    """
    # Create directory for form11
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'form11')
    os.makedirs(upload_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"form11_{employee.id}_{timestamp}.pdf"
    filepath = os.path.join(upload_dir, filename)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.cell(0, 10, "Form 11 - Declaration Form (Revised)", ln=True, align='C')
    pdf.ln(10)

    # Employee info
    pdf.cell(0, 10, f"Employee: {employee.first_name} {employee.last_name}", ln=True)
    pdf.cell(0, 10, f"Employee ID: {employee.id}", ln=True)
    pdf.ln(10)

    # Form data
    for key, value in form_data.items():
        if key not in ['csrf_token', 'submit']:
            pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Save PDF
    pdf.output(filepath)

    # Return normalized relative path for storage in DB and URL generation
    relative_path = normalize_path(filepath)

    # Log the file creation for debugging
    current_app.logger.info(f"Generated Form 11 PDF at: {filepath}")
    current_app.logger.info(f"Normalized path for storage: {relative_path}")

    return relative_path

def generate_pf_form_pdf(form_data, employee):
    """
    Generate a PDF for PF Form using form data and employee info.
    Saves the PDF under static/uploads/pf_form and returns the relative file path.
    """
    # Create directory for pf_form
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'pf_form')
    os.makedirs(upload_dir, exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"pf_form_{employee.id}_{timestamp}.pdf"
    filepath = os.path.join(upload_dir, filename)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.cell(0, 10, "PF Form 2 (Revised)", ln=True, align='C')
    pdf.ln(10)

    # Employee info
    pdf.cell(0, 10, f"Employee: {employee.first_name} {employee.last_name}", ln=True)
    pdf.cell(0, 10, f"Employee ID: {employee.id}", ln=True)
    pdf.ln(10)

    # Form data
    for key, value in form_data.items():
        if key not in ['csrf_token', 'submit']:
            pdf.cell(0, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Save PDF
    pdf.output(filepath)

    # Return normalized relative path for storage in DB and URL generation
    relative_path = normalize_path(filepath)

    # Log the file creation for debugging
    current_app.logger.info(f"Generated PF Form PDF at: {filepath}")
    current_app.logger.info(f"Normalized path for storage: {relative_path}")

    return relative_path
