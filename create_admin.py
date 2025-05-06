from app import create_app
from models import User, db, ROLE_ADMIN

def create_admin_user():
    """Create an admin user if one doesn't exist."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin = User.query.filter_by(role=ROLE_ADMIN).first()
        
        if admin:
            print(f"Admin user already exists: {admin.username} / {admin.email}")
            return
        
        # Create admin user
        admin = User(
            username="admin",
            email="admin@example.com",
            role=ROLE_ADMIN,
            is_active=True,
            first_login=False,
            is_temporary_password=False
        )
        admin.set_password("admin123")
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Username: admin")
        print(f"Email: admin@example.com")
        print(f"Password: admin123")

if __name__ == "__main__":
    create_admin_user()
