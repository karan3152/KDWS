from app import create_app
from models import User, db, ROLE_ADMIN

def update_admin_user():
    """Update or create admin user with specific credentials."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists by username
        admin = User.query.filter_by(username="admin").first()
        
        if admin:
            print(f"Admin user found: {admin.username} / {admin.email}")
            # Update email and password
            admin.email = "admin@hrts.com"
            admin.role = ROLE_ADMIN
            admin.is_active = True
            admin.first_login = False
            admin.is_temporary_password = False
            admin.set_password("Admin@123")
            db.session.commit()
            print(f"Admin user updated successfully!")
            print(f"Username: {admin.username}")
            print(f"Email: admin@hrts.com")
            print(f"Password: Admin@123")
            return
        
        # If no admin user exists, create one
        admin = User(
            username="admin_hrts",  # Use a different username to avoid conflicts
            email="admin@hrts.com",
            role=ROLE_ADMIN,
            is_active=True,
            first_login=False,
            is_temporary_password=False
        )
        admin.set_password("Admin@123")
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Username: admin_hrts")
        print(f"Email: admin@hrts.com")
        print(f"Password: Admin@123")

if __name__ == "__main__":
    update_admin_user()
