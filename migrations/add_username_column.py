from app import db

def upgrade():
    # Add username column to user table
    db.engine.execute('ALTER TABLE user ADD COLUMN username VARCHAR(64) UNIQUE NOT NULL')

def downgrade():
    # Remove username column from user table
    db.engine.execute('ALTER TABLE user DROP COLUMN username') 