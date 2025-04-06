import os
import io
import zipfile
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from flask import current_app

from app import app
from models import Document


def generate_combined_pdf(documents):
    """
    Generate a combined PDF from multiple documents.
    
    Args:
        documents: List of Document objects to combine
    
    Returns:
        An IO buffer containing the combined PDF
    """
    merger = PdfMerger()
    
    # Sort documents by type to ensure a consistent order
    sorted_docs = sorted(documents, key=lambda d: d.document_type)
    
    for document in sorted_docs:
        if document and document.file_path and document.file_path.lower().endswith('.pdf'):
            # Get the absolute path to the document
            doc_path = os.path.join(app.root_path, document.file_path)
            if os.path.exists(doc_path):
                try:
                    # Add the document to the merger
                    merger.append(doc_path)
                except Exception as e:
                    print(f"Error adding {doc_path} to merged PDF: {e}")
    
    # Create a buffer to store the combined PDF
    output_buffer = io.BytesIO()
    merger.write(output_buffer)
    merger.close()
    
    # Reset the position to the beginning of the buffer
    output_buffer.seek(0)
    
    return output_buffer


def add_metadata_to_combined_pdf(pdf_buffer, employee):
    """
    Add metadata to a combined PDF.
    
    Args:
        pdf_buffer: IO buffer containing the PDF
        employee: EmployeeProfile object for the employee
    
    Returns:
        An IO buffer containing the PDF with added metadata
    """
    # Read the PDF from buffer
    pdf_reader = PdfReader(pdf_buffer)
    pdf_writer = PdfWriter()
    
    # Copy pages from the reader to the writer
    for page in pdf_reader.pages:
        pdf_writer.add_page(page)
    
    # Add metadata
    metadata = {
        '/Title': f'Employee Documents - {employee.get_full_name()}',
        '/Author': 'HR Talent Solutions',
        '/Subject': f'Combined documents for {employee.employee_id}',
        '/Creator': 'Document Management System',
        '/Producer': 'PyPDF2',
        '/Keywords': f'employee documents, HR, {employee.employee_id}, {employee.aadhar_id}'
    }
    pdf_writer.add_metadata(metadata)
    
    # Create a new buffer for the output
    output_buffer = io.BytesIO()
    pdf_writer.write(output_buffer)
    
    # Reset the position to the beginning of the buffer
    output_buffer.seek(0)
    
    return output_buffer


def create_documents_zip(documents):
    """
    Create a ZIP file containing all documents.
    
    Args:
        documents: List of Document objects to include
    
    Returns:
        An IO buffer containing the ZIP file
    """
    # Create a buffer to store the ZIP file
    output_buffer = io.BytesIO()
    
    # Create a ZIP file
    with zipfile.ZipFile(output_buffer, 'w') as zip_file:
        for document in documents:
            if document and document.file_path:
                # Get the absolute path to the document
                doc_path = os.path.join(app.root_path, document.file_path)
                if os.path.exists(doc_path):
                    # Get the filename without the path
                    filename = os.path.basename(doc_path)
                    # Add a prefix to avoid name collisions
                    zip_filename = f"{document.document_type}_{filename}"
                    # Add the document to the ZIP file
                    zip_file.write(doc_path, zip_filename)
    
    # Reset the position to the beginning of the buffer
    output_buffer.seek(0)
    
    return output_buffer


def extract_pdf_form_data(pdf_file_path):
    """
    Extract form field data from a PDF form.
    
    Args:
        pdf_file_path: Path to the PDF file
    
    Returns:
        A dictionary of form field data
    """
    reader = PdfReader(pdf_file_path)
    form_data = {}
    
    if reader.get_fields():
        for field_name, field in reader.get_fields().items():
            if hasattr(field, 'value'):
                form_data[field_name] = field.value
    
    return form_data


def fill_pdf_form(template_path, output_path, data):
    """
    Fill a PDF form with data.
    
    Args:
        template_path: Path to the template PDF form
        output_path: Path where the filled form should be saved
        data: Dictionary of form field data
    
    Returns:
        Boolean indicating success or failure
    """
    try:
        reader = PdfReader(template_path)
        writer = PdfWriter()
        
        # Copy pages from the reader to the writer
        for page in reader.pages:
            writer.add_page(page)
        
        # Update form fields with the provided data
        writer.update_page_form_field_values(writer.pages[0], data)
        
        # Write the output file
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        return True
    except Exception as e:
        print(f"Error filling PDF form: {e}")
        return False