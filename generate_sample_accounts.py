import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import app, db
from models import User, EmployeeProfile, EmployerProfile, ROLE_ADMIN, ROLE_EMPLOYER, ROLE_EMPLOYEE


def generate_sample_accounts():
    """Generate sample user accounts for testing."""
    with app.app_context():
        # Check if we already have users
        if User.query.count() > 0:
            print("Users already exist in the database.")
            return False
        
        # Create admin account
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('Admin@123'),
            role=ROLE_ADMIN,
            first_login=False
        )
        db.session.add(admin)
        
        # Create employers
        employers = [
            {
                'username': 'employer1',
                'email': 'employer1@example.com',
                'password': 'Employer@123',
                'company_name': 'HR Talent Solutions',
                'department': 'Human Resources',
                'contact_number': '9876543210'
            },
            {
                'username': 'employer2',
                'email': 'employer2@example.com',
                'password': 'Employer@123',
                'company_name': 'Tech Innovations Inc.',
                'department': 'IT Department',
                'contact_number': '9876543211'
            }
        ]
        
        for emp_data in employers:
            employer_user = User(
                username=emp_data['username'],
                email=emp_data['email'],
                password_hash=generate_password_hash(emp_data['password']),
                role=ROLE_EMPLOYER,
                first_login=False
            )
            db.session.add(employer_user)
            db.session.flush()
            
            employer_profile = EmployerProfile(
                user_id=employer_user.id,
                company_name=emp_data['company_name'],
                department=emp_data['department'],
                contact_number=emp_data['contact_number']
            )
            db.session.add(employer_profile)
        
        # Create employees
        departments = ['IT', 'Finance', 'Marketing', 'Operations', 'HR']
        positions = ['Junior Developer', 'Senior Developer', 'Manager', 'Analyst', 'Coordinator']
        
        for i in range(1, 10):  # 9 employees
            username = f'employee{i}'
            email = f'employee{i}@example.com'
            password = 'Employee@123'
            
            # Create user
            employee_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password),
                role=ROLE_EMPLOYEE,
                first_login=i > 5  # First 5 have completed first login
            )
            db.session.add(employee_user)
            db.session.flush()
            
            # Generate random profile data
            first_name = random.choice(['John', 'Jane', 'David', 'Sarah', 'Michael', 'Emily', 'Robert', 'Anna'])
            last_name = random.choice(['Smith', 'Johnson', 'Williams', 'Jones', 'Brown', 'Davis', 'Miller', 'Wilson'])
            dob = datetime.now() - timedelta(days=random.randint(8000, 15000))  # 22-41 years old
            department = random.choice(departments)
            position = random.choice(positions)
            joining_date = datetime.now() - timedelta(days=random.randint(30, 1095))  # 1 month to 3 years
            
            # Create profile
            employee_profile = EmployeeProfile(
                user_id=employee_user.id,
                employee_id=f'EMP{1000+i}',
                aadhar_id=f'1234{5678+i}9012',
                first_name=first_name,
                last_name=last_name,
                date_of_birth=dob,
                phone_number=f'987654321{i}',
                address=f'{i} Sample Street, City, State, 12345',
                department=department,
                position=position,
                joining_date=joining_date,
                current_project=f'Project {random.choice(["Alpha", "Beta", "Gamma", "Delta", "Epsilon"])}'
            )
            db.session.add(employee_profile)
        
        db.session.commit()
        print("Sample accounts generated successfully!")
        
        # Print login credentials
        print("\nLogin Credentials:")
        print("------------------")
        print("Admin: admin / Admin@123")
        print("Employer: employer1 / Employer@123")
        print("Employee: employee1 / Employee@123")
        
        return True


if __name__ == "__main__":
    generate_sample_accounts()