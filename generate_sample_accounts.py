from app import app, db
from models import User, EmployeeProfile, EmployerProfile, ROLE_ADMIN, ROLE_EMPLOYEE, ROLE_EMPLOYER
from werkzeug.security import generate_password_hash
from datetime import datetime

def create_admin():
    """Create a sample admin account."""
    username = "admin"
    email = "admin@hrtalent.com"
    password = "Admin@123"
    
    # Check if the admin user already exists
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Admin user '{username}' already exists.")
            return
        
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
        print(f"Admin password: {password}")

def create_employee():
    """Create a sample employee account."""
    username = "employee1"
    email = "employee1@example.com"
    password = "Employee@123"
    aadhar_id = "123456789012"  # 12 digits
    employee_id = "EMP001"
    
    # Check if the employee user already exists
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Employee user '{username}' already exists.")
            return
        
        # Create new employee user
        employee_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=ROLE_EMPLOYEE,
            first_login=True
        )
        
        db.session.add(employee_user)
        db.session.commit()
        
        # Create employee profile
        employee_profile = EmployeeProfile(
            user_id=employee_user.id,
            aadhar_id=aadhar_id,
            employee_id=employee_id,
            first_name="John",
            last_name="Doe",
            department="Engineering",
            position="Software Developer"
        )
        
        db.session.add(employee_profile)
        db.session.commit()
        
        print(f"Created employee user '{username}' with email '{email}'")
        print(f"Employee password: {password}")
        print(f"Aadhar ID: {aadhar_id}")
        print(f"Employee ID: {employee_id}")

def create_employer():
    """Create a sample employer account."""
    username = "employer1"
    email = "employer1@hrtalent.com"
    password = "Employer@123"
    company_id = "HRT001"
    
    # Check if the employer user already exists
    with app.app_context():
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            print(f"Employer user '{username}' already exists.")
            return
        
        # Create new employer user
        employer_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=ROLE_EMPLOYER,
            first_login=False
        )
        
        db.session.add(employer_user)
        db.session.commit()
        
        # Create employer profile
        employer_profile = EmployerProfile(
            user_id=employer_user.id,
            company_name="HR Talent Solutions",
            company_id=company_id,
            department="Human Resources",
            contact_number="9876543210"
        )
        
        db.session.add(employer_profile)
        db.session.commit()
        
        print(f"Created employer user '{username}' with email '{email}'")
        print(f"Employer password: {password}")
        print(f"Company ID: {company_id}")

if __name__ == "__main__":
    print("Generating sample accounts...")
    create_admin()
    create_employee()
    create_employer()
    print("Sample accounts created successfully!")