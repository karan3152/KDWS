from app import create_app
from models import User, db, ROLE_ADMIN

def create_admin_user():
    """Create a specific admin user."""
    app = create_app()
    
    with app.app_context():
        # Check if this admin user already exists
        admin = User.query.filter_by(email="admin@hrts.com").first()
        
        if admin:
            print(f"Admin user already exists: {admin.username} / {admin.email}")
            # Update password just in case
            admin.set_password("Admin@123")
            db.session.commit()
            print(f"Password updated.")
            return
        
        # Create admin user with the specific credentials
        admin = User(
            username="admin",
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
        print(f"Username: admin")
        print(f"Email: admin@hrts.com")
        print(f"Password: Admin@123")

if __name__ == "__main__":
    create_admin_user()
