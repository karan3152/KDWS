"""
Migration script to add aadhar_filename column to family_member table
"""
import os
import sys
import pymysql

# Add the parent directory to the path so we can import from the project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extensions import db
from app import app

def run_migration():
    """Add aadhar_filename column to family_member table if it doesn't exist"""
    with app.app_context():
        try:
            # Check if the column already exists
            check_query = """
            SELECT COUNT(*)
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'family_member'
            AND COLUMN_NAME = 'aadhar_filename'
            """
            result = db.session.execute(check_query)
            column_exists = result.scalar() > 0

            if not column_exists:
                print("Adding aadhar_filename column to family_member table...")
                # Add the column
                alter_query = """
                ALTER TABLE family_member
                ADD COLUMN aadhar_filename VARCHAR(255) NULL AFTER photo_path
                """
                db.session.execute(alter_query)
                db.session.commit()
                print("Column added successfully!")
            else:
                print("Column aadhar_filename already exists in family_member table.")

            print("Migration completed successfully!")

        except Exception as e:
            print(f"Error during migration: {e}")
            db.session.rollback()
        finally:
            db.session.close()

if __name__ == "__main__":
    run_migration()
