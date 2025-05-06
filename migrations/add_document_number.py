"""
Migration script to add document_number column to the document table.
"""
from flask import Flask
from extensions import db
import os
import sys

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app
from app import create_app

app = create_app()

with app.app_context():
    # Add the document_number column to the document table
    db.engine.execute('ALTER TABLE document ADD COLUMN document_number VARCHAR(100) NULL')
    print("Added document_number column to document table")
