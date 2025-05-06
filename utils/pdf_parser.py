"""PDF parsing utilities for employee forms."""

import pdfplumber

def extract_form_data(pdf_path):
    """Extract form data from a PDF file."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            
            # Parse the text into key-value pairs
            data = {}
            lines = text.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    data[key] = value.strip()
            return data
    except Exception as e:
        print(f"Error extracting data from PDF: {str(e)}")
        return {}

def extract_joining_form_data(pdf_path):
    """Extract data from joining form PDF."""
    return extract_form_data(pdf_path)

def extract_pf_form_data(pdf_path):
    """Extract data from PF form PDF."""
    return extract_form_data(pdf_path)

def extract_form1_data(pdf_path):
    """Extract data from Form 1 PDF."""
    return extract_form_data(pdf_path)

def extract_form11_data(pdf_path):
    """Extract data from Form 11 PDF."""
    return extract_form_data(pdf_path) 