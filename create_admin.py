import sys
from werkzeug.security import generate_password_hash
from datetime import datetime

from app import app, db
from models import User, EmployerProfile, ROLE_ADMIN


def create_admin_user():
    """Create an admin user if it doesn't exist."""
    with app.app_context():
        # Create tables
        db.create_all()

        # Check if admin already exists
        existing_user = User.query.filter_by(username='admin').first()
        if existing_user:
            print("Admin user already exists!")
            return False

        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),  # Set default password
            role=ROLE_ADMIN,
            first_login=False,
            created_at=datetime.utcnow(),
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()
        print("Admin user 'admin' created successfully!")
        return True


if __name__ == "__main__":
    create_admin_user()