from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# User roles
ROLE_ADMIN = 'admin'
ROLE_EMPLOYER = 'employer'
ROLE_EMPLOYEE = 'employee'

class User(UserMixin, db.Model):
    """User model for authentication and basic information."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    employee_profile = db.relationship('EmployeeProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    employer_profile = db.relationship('EmployerProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the password matches the stored hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if the user has admin role."""
        return self.role == ROLE_ADMIN
    
    def is_employer(self):
        """Check if the user has employer role."""
        return self.role == ROLE_EMPLOYER
    
    def is_employee(self):
        """Check if the user has employee role."""
        return self.role == ROLE_EMPLOYEE
    
    def __repr__(self):
        return f'<User {self.username}>'

class EmployeeProfile(db.Model):
    """Profile specific to employees."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    aadhar_id = db.Column(db.String(20), unique=True, nullable=False)
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    date_of_birth = db.Column(db.Date)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    joining_date = db.Column(db.Date)
    
    # Relationship with documents
    documents = db.relationship('Document', backref='employee', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<EmployeeProfile {self.first_name} {self.last_name}>'

class EmployerProfile(db.Model):
    """Profile specific to employers/HR."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100))
    company_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50))
    contact_number = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<EmployerProfile {self.company_name}>'

class Document(db.Model):
    """Model for storing uploaded PDFs and other documents."""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'aadhar', 'pan', 'photo', 'passbook', 'joining_form', 'pf_form', 'form1', 'form11'
    document_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    
    # Additional metadata for specific document types
    document_number = db.Column(db.String(50))  # For Aadhar, PAN numbers, Bank account
    bank_name = db.Column(db.String(100))  # For passbook
    ifsc_code = db.Column(db.String(20))   # For passbook
    issue_date = db.Column(db.Date)  # For date of issue if applicable
    expiry_date = db.Column(db.Date)  # For documents with expiry
    
    def __repr__(self):
        return f'<Document {self.document_name}>'
        
# Define constant for document types for consistency across the application
class DocumentTypes:
    AADHAR = 'aadhar'
    PAN = 'pan'
    PHOTO = 'photo'
    PASSBOOK = 'passbook'
    JOINING_FORM = 'joining_form'
    PF_FORM = 'pf_form'
    FORM1 = 'form1'
    FORM11 = 'form11'
    
    @classmethod
    def all_types(cls):
        """Return a list of all document types."""
        return [
            cls.AADHAR, 
            cls.PAN, 
            cls.PHOTO, 
            cls.PASSBOOK,
            cls.JOINING_FORM,
            cls.PF_FORM,
            cls.FORM1,
            cls.FORM11
        ]
    
    @classmethod
    def get_required_types(cls):
        """Return a list of required document types."""
        return [cls.AADHAR, cls.PAN, cls.PHOTO, cls.PASSBOOK]

class PasswordResetToken(db.Model):
    """Model for password reset tokens."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationship with user
    user = db.relationship('User', backref='reset_tokens')
    
    def __repr__(self):
        return f'<PasswordResetToken {self.token}>'

class NewsUpdate(db.Model):
    """Model for company news and updates."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    # For interview notices
    location_address = db.Column(db.Text)
    interview_date = db.Column(db.DateTime)
    # Created by which employer
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profile.id'))
    
    # Relationship
    employer = db.relationship('EmployerProfile', backref='news_updates')
    
    def __repr__(self):
        return f'<NewsUpdate {self.title}>'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
