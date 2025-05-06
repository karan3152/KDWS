from app import db

def upgrade():
    # Add photo_path column to user table
    db.engine.execute('ALTER TABLE user ADD COLUMN photo_path VARCHAR(255)')

def downgrade():
    # Remove photo_path column from user table
    db.engine.execute('ALTER TABLE user DROP COLUMN photo_path') 