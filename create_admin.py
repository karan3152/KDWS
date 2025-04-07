import sys
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, ROLE_ADMIN


def create_admin_user(username, email, password):
    """Create an admin user if it doesn't exist."""
    with app.app_context():
        # Check if admin already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        
        if existing_user:
            if existing_user.username == username:
                print(f"User with username '{username}' already exists.")
            else:
                print(f"User with email '{email}' already exists.")
            return False
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=ROLE_ADMIN,
            first_login=False
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user '{username}' created successfully!")
        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    create_admin_user(username, email, password)