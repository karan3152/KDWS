"""
Migration script to add photo_path and aadhar_card_path columns to the family_member table.
"""
import os
import sys
from sqlalchemy import text

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the app and extensions
from app import create_app
from extensions import db

def run_migration():
    """Run the migration to add the new columns."""
    app = create_app()

    with app.app_context():
        # Check if the columns already exist
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('family_member')]

        # Add photo_path column if it doesn't exist
        if 'photo_path' not in columns:
            print("Adding photo_path column to family_member table...")
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE family_member ADD COLUMN photo_path VARCHAR(255)'))
            print("Added photo_path column successfully.")
        else:
            print("photo_path column already exists.")

        # Add aadhar_card_path column if it doesn't exist
        if 'aadhar_card_path' not in columns:
            print("Adding aadhar_card_path column to family_member table...")
            with db.engine.begin() as conn:
                conn.execute(text('ALTER TABLE family_member ADD COLUMN aadhar_card_path VARCHAR(255)'))
            print("Added aadhar_card_path column successfully.")
        else:
            print("aadhar_card_path column already exists.")

        print("Migration completed successfully.")

if __name__ == '__main__':
    run_migration()
