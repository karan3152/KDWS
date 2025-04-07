
from werkzeug.security import generate_password_hash
from datetime import datetime

from app import app, db
from models import User, ROLE_ADMIN

def create_admin_user():
    """Create an admin user."""
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print("Admin user already exists!")
            return

        # Create admin user
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            role=ROLE_ADMIN,
            first_login=False,
            created_at=datetime.utcnow(),
            is_active=True
        )

        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")

if __name__ == "__main__":
    create_admin_user()
