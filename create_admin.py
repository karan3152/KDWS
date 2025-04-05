from app import app, db
from models import User, ROLE_ADMIN
from werkzeug.security import generate_password_hash

def create_admin_user(username, email, password):
    """Create an admin user if it doesn't exist."""
    with app.app_context():
        # Check if the admin user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Admin user '{username}' already exists.")
            return False
        
        # Create new admin user
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=ROLE_ADMIN,
            first_login=False
        )
        
        db.session.add(admin)
        db.session.commit()
        print(f"Created admin user '{username}' with email '{email}'")
        return True

if __name__ == "__main__":
    # Create an admin user with the following credentials
    admin_username = "admin"
    admin_email = "admin@example.com"
    admin_password = "Admin@123"
    
    create_admin_user(admin_username, admin_email, admin_password)
    print("Admin credentials:")
    print(f"Username: {admin_username}")
    print(f"Password: {admin_password}")