from datetime import datetime, timedelta
from flask_login import UserMixin
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

# Define user roles
ROLE_EMPLOYEE = 'employee'
ROLE_EMPLOYER = 'employer'
ROLE_ADMIN = 'admin'


class User(UserMixin, db.Model):
    """User model for authentication and basic information."""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
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
        """String representation of the user."""
        return f'<User {self.username}, role: {self.role}>'


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
    photo_url = db.Column(db.String(255))
    
    # Relationships
    documents = db.relationship('Document', backref='employee', cascade='all, delete-orphan')
    
    def __repr__(self):
        """String representation of the employee profile."""
        return f'<EmployeeProfile {self.employee_id}: {self.first_name} {self.last_name}>'


class EmployerProfile(db.Model):
    """Profile specific to employers/HR."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100))
    company_id = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(50))
    contact_number = db.Column(db.String(20))
    
    def __repr__(self):
        """String representation of the employer profile."""
        return f'<EmployerProfile {self.company_id}: {self.company_name}>'


class Document(db.Model):
    """Model for storing uploaded PDFs and other documents."""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # 'aadhar', 'pan', 'photo', 'passbook', 'joining_form', 'pf_form', 'form1', 'form11'
    document_name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approval_date = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    feedback = db.Column(db.Text)
    
    # Additional document metadata
    document_number = db.Column(db.String(50))  # For Aadhar, PAN numbers, Bank account
    bank_name = db.Column(db.String(100))  # For passbook
    ifsc_code = db.Column(db.String(20))   # For passbook
    issue_date = db.Column(db.Date)  # For date of issue if applicable
    expiry_date = db.Column(db.Date)  # For documents with expiry
    
    # Relationships
    approver = db.relationship('User', backref='approved_documents')
    
    def __repr__(self):
        """String representation of the document."""
        return f'<Document {self.document_type}: {self.document_name}, status: {self.status}>'


class DocumentTypes:
    """Constants for document types."""
    AADHAR = 'aadhar'
    PAN = 'pan'
    PHOTO = 'photo'
    PASSBOOK = 'passbook'
    JOINING_FORM = 'joining_form'
    PF_FORM = 'pf_form'
    FORM1 = 'form1'
    FORM11 = 'form11'
    POLICE_VERIFICATION = 'police_verification'
    MEDICAL_CERTIFICATE = 'medical_certificate'
    FAMILY_DETAILS = 'family_details'
    
    @classmethod
    def all_types(cls):
        """Return a list of all document types."""
        return [
            cls.AADHAR, cls.PAN, cls.PHOTO, cls.PASSBOOK,
            cls.JOINING_FORM, cls.PF_FORM, cls.FORM1, cls.FORM11,
            cls.POLICE_VERIFICATION, cls.MEDICAL_CERTIFICATE, cls.FAMILY_DETAILS
        ]
    
    @classmethod
    def get_required_types(cls):
        """Return a list of required document types."""
        return [
            cls.AADHAR, cls.PAN, cls.PHOTO, cls.PASSBOOK,
            cls.JOINING_FORM, cls.PF_FORM, cls.FORM1, cls.FORM11
        ]


class PasswordResetToken(db.Model):
    """Model for password reset tokens."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='reset_tokens')
    
    @classmethod
    def generate_token(cls, user_id, expires_in=3600):
        """Generate a new token for the user."""
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        return cls(user_id=user_id, token=token, expires_at=expires_at)
    
    def is_expired(self):
        """Check if the token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        """String representation of the token."""
        return f'<PasswordResetToken for user_id={self.user_id}, expires={self.expires_at}>'


class FamilyMember(db.Model):
    """Model for storing family member details."""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    aadhar_id = db.Column(db.String(20))
    photo_path = db.Column(db.String(255))
    contact_number = db.Column(db.String(20))
    
    # Relationships
    employee = db.relationship('EmployeeProfile', backref='family_members')
    
    def __repr__(self):
        """String representation of the family member."""
        return f'<FamilyMember {self.name}, {self.relationship} of employee_id={self.employee_id}>'


class NewsUpdate(db.Model):
    """Model for company news and updates."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # For interview notices
    is_interview_notice = db.Column(db.Boolean, default=False)
    location_address = db.Column(db.Text)
    interview_date = db.Column(db.DateTime)
    
    # Who created this news
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profile.id'))
    
    # Relationships
    employer = db.relationship('EmployerProfile', backref='news_updates')
    
    def __repr__(self):
        """String representation of the news update."""
        return f'<NewsUpdate "{self.title}", published={self.published_date}>'


# User loader for Flask-Login
from app import login_manager

@login_manager.user_loader
def load_user(user_id):
    """Load a user by ID for Flask-Login."""
    return User.query.get(int(user_id))