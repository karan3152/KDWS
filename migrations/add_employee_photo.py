from app import db

def upgrade():
    # Add photo_path column to employee_profile table
    db.engine.execute('ALTER TABLE employee_profile ADD COLUMN photo_path VARCHAR(255)')

def downgrade():
    # Remove photo_path column from employee_profile table
    db.engine.execute('ALTER TABLE employee_profile DROP COLUMN photo_path') 