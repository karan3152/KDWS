import os
import io
import zipfile
from PyPDF2 import PdfMerger, PdfReader
from PIL import Image
from flask import current_app
from models import Document, DocumentTypes

def convert_image_to_pdf(image_path):
    """Convert JPG/PNG image to PDF."""
    pdf_buffer = io.BytesIO()
    
    # Open image
    with Image.open(image_path) as img:
        # Convert to RGB if needed (required for some color modes when saving as PDF)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as PDF to buffer
        img.save(pdf_buffer, format="PDF", resolution=100.0)
    
    pdf_buffer.seek(0)
    return pdf_buffer

def generate_combined_pdf(document_list):
    """Generate a combined PDF from a list of documents."""
    merger = PdfMerger()
    
    try:
        for doc in document_list:
            file_path = doc.file_path
            full_path = os.path.join(current_app.root_path, file_path)
            
            # Check if the file exists
            if not os.path.exists(full_path):
                continue
            
            # If the file is an image, convert it to PDF first
            if any(full_path.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                pdf_buffer = convert_image_to_pdf(full_path)
                merger.append(pdf_buffer)
            else:
                # For PDF files, just add them directly
                merger.append(full_path)
        
        # Create a BytesIO object to store the merged PDF
        output_buffer = io.BytesIO()
        merger.write(output_buffer)
        merger.close()
        
        # Reset the buffer position to the beginning
        output_buffer.seek(0)
        return output_buffer
        
    except Exception as e:
        print(f"Error generating combined PDF: {str(e)}")
        merger.close()
        return None

def create_documents_zip(document_list):
    """Create a ZIP file containing all documents."""
    memory_file = io.BytesIO()
    
    with zipfile.ZipFile(memory_file, 'w') as zf:
        for doc in document_list:
            file_path = doc.file_path
            full_path = os.path.join(current_app.root_path, file_path)
            
            # Check if the file exists
            if not os.path.exists(full_path):
                continue
            
            # Add file to the ZIP with a descriptive name
            filename = f"{doc.document_type}_{doc.document_name}{os.path.splitext(file_path)[1]}"
            # Replace spaces with underscores and remove any special characters
            safe_filename = ''.join(c if c.isalnum() or c in '._- ' else '_' for c in filename)
            safe_filename = safe_filename.replace(' ', '_')
            
            zf.write(full_path, safe_filename)
    
    memory_file.seek(0)
    return memory_file

def add_metadata_to_combined_pdf(pdf_buffer, employee):
    """Add metadata to the combined PDF."""
    reader = PdfReader(pdf_buffer)
    writer = PdfMerger()
    
    for page in reader.pages:
        writer.append(page)
    
    # Add metadata
    metadata = {
        "/Title": f"Employee Documents - {employee.employee_id}",
        "/Author": "HR Talent Solutions",
        "/Subject": f"Combined Documents for {employee.first_name} {employee.last_name}",
        "/Keywords": f"employee documents, {employee.employee_id}, HR Talent Solutions",
        "/Creator": "HR Talent Solutions Document Management System"
    }
    
    writer.add_metadata(metadata)
    
    # Write to a new buffer
    output_buffer = io.BytesIO()
    writer.write(output_buffer)
    writer.close()
    
    output_buffer.seek(0)
    return output_buffer