from app import app
from models import User, db

def list_users():
    """List all users in the database."""
    with app.app_context():
        users = User.query.all()
        
        if not users:
            print("No users found in the database.")
            return
        
        print(f"Found {len(users)} users:")
        for user in users:
            print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}")

if __name__ == "__main__":
    list_users()
