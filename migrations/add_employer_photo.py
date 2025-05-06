from app import db

def upgrade():
    # Add photo_path column to employer_profile table
    db.engine.execute('ALTER TABLE employer_profile ADD COLUMN photo_path VARCHAR(255)')

def downgrade():
    # Remove photo_path column from employer_profile table
    db.engine.execute('ALTER TABLE employer_profile DROP COLUMN photo_path') 