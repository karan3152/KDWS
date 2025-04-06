from datetime import datetime, timedelta
from flask_login import UserMixin
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

# User role constants
ROLE_ADMIN = 'admin'
ROLE_EMPLOYER = 'employer'
ROLE_EMPLOYEE = 'employee'


class User(UserMixin, db.Model):
    """User model representing all users in the system."""
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_EMPLOYEE)
    first_login = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    employee_profile = db.relationship('EmployeeProfile', backref='user', uselist=False, lazy=True,
                                      cascade="all, delete-orphan")
    employer_profile = db.relationship('EmployerProfile', backref='user', uselist=False, lazy=True,
                                      cascade="all, delete-orphan")
    
    def set_password(self, password):
        """Set the password hash for the user."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if the user is an admin."""
        return self.role == ROLE_ADMIN
    
    def is_employer(self):
        """Check if the user is an employer."""
        return self.role == ROLE_EMPLOYER
    
    def is_employee(self):
        """Check if the user is an employee."""
        return self.role == ROLE_EMPLOYEE
    
    def get_full_name(self):
        """Get the full name of the user based on their profile."""
        if self.is_employee() and self.employee_profile:
            return f"{self.employee_profile.first_name} {self.employee_profile.last_name}"
        elif self.is_employer() and self.employer_profile:
            return self.employer_profile.company_name
        else:
            return self.username
    
    def __repr__(self):
        return f'<User {self.username}, role={self.role}>'


class EmployeeProfile(db.Model):
    """Profile for employee users."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    employee_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    aadhar_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    phone_number = db.Column(db.String(15), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    department = db.Column(db.String(50), nullable=True)
    position = db.Column(db.String(50), nullable=True)
    joining_date = db.Column(db.Date, nullable=True)
    current_project = db.Column(db.String(100), nullable=True)
    
    # Relationships
    documents = db.relationship('Document', backref='employee', lazy=True, 
                              cascade="all, delete-orphan")
    family_members = db.relationship('FamilyMember', backref='employee', lazy=True,
                                   cascade="all, delete-orphan")
    
    def get_full_name(self):
        """Get the full name of the employee."""
        return f"{self.first_name} {self.last_name}"
    
    def __repr__(self):
        return f'<EmployeeProfile {self.employee_id}, name={self.first_name} {self.last_name}>'


class EmployerProfile(db.Model):
    """Profile for employer/HR users."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    company_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50), nullable=True)
    contact_number = db.Column(db.String(15), nullable=True)
    
    # Relationships
    news_updates = db.relationship('NewsUpdate', backref='employer', lazy=True,
                                 cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<EmployerProfile id={self.id}, company={self.company_name}>'


class DocumentTypes:
    """Constants for document types."""
    
    # Identity documents
    AADHAR_CARD = 'aadhar_card'
    PAN_CARD = 'pan_card'
    PASSPORT = 'passport'
    PHOTO = 'photo'
    
    # Bank details
    BANK_PASSBOOK = 'bank_passbook'
    CANCELLED_CHEQUE = 'cancelled_cheque'
    
    # Education/Professional documents
    RESUME = 'resume'
    EDUCATIONAL_CERTIFICATES = 'educational_certificates'
    EXPERIENCE_CERTIFICATES = 'experience_certificates'
    
    # Employment forms
    NEW_JOINING_FORM = 'new_joining_form'
    PF_FORM = 'pf_form'
    FORM_11 = 'form_11'
    FORM_1_NOMINATION = 'form_1_nomination'
    
    # Other documents
    POLICE_VERIFICATION = 'police_verification'
    MEDICAL_CERTIFICATE = 'medical_certificate'
    FAMILY_DECLARATION = 'family_declaration'
    
    @classmethod
    def all_types(cls):
        """Get all document types."""
        return [
            cls.AADHAR_CARD, cls.PAN_CARD, cls.PASSPORT, cls.PHOTO,
            cls.BANK_PASSBOOK, cls.CANCELLED_CHEQUE,
            cls.RESUME, cls.EDUCATIONAL_CERTIFICATES, cls.EXPERIENCE_CERTIFICATES,
            cls.NEW_JOINING_FORM, cls.PF_FORM, cls.FORM_11, cls.FORM_1_NOMINATION,
            cls.POLICE_VERIFICATION, cls.MEDICAL_CERTIFICATE, cls.FAMILY_DECLARATION
        ]
    
    @classmethod
    def get_required_types(cls):
        """Get required document types."""
        return [
            cls.AADHAR_CARD, cls.PAN_CARD, cls.PHOTO, cls.BANK_PASSBOOK,
            cls.NEW_JOINING_FORM, cls.PF_FORM, cls.FORM_11, cls.FORM_1_NOMINATION
        ]
    
    @classmethod
    def get_identity_types(cls):
        """Get identity document types."""
        return [cls.AADHAR_CARD, cls.PAN_CARD, cls.PASSPORT, cls.PHOTO]
    
    @classmethod
    def get_bank_types(cls):
        """Get bank document types."""
        return [cls.BANK_PASSBOOK, cls.CANCELLED_CHEQUE]
    
    @classmethod
    def get_education_types(cls):
        """Get education/professional document types."""
        return [cls.RESUME, cls.EDUCATIONAL_CERTIFICATES, cls.EXPERIENCE_CERTIFICATES]
    
    @classmethod
    def get_form_types(cls):
        """Get employment form types."""
        return [cls.NEW_JOINING_FORM, cls.PF_FORM, cls.FORM_11, cls.FORM_1_NOMINATION]
    
    @classmethod
    def get_other_types(cls):
        """Get other document types."""
        return [cls.POLICE_VERIFICATION, cls.MEDICAL_CERTIFICATE, cls.FAMILY_DECLARATION]
    
    @classmethod
    def get_type_name(cls, doc_type):
        """Get a human-readable name for a document type."""
        return doc_type.replace('_', ' ').title()


class Document(db.Model):
    """Document model for employee documents."""
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    content_type = db.Column(db.String(100), default='application/pdf')  # MIME type
    
    # Reviewer relationship
    reviewer = db.relationship('User', backref='reviewed_documents', foreign_keys=[reviewed_by])
    
    def __repr__(self):
        return f'<Document id={self.id}, type={self.document_type}, status={self.status}>'


class FamilyMember(db.Model):
    """Family member details for employees."""
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    address = db.Column(db.String(200), nullable=True)
    contact_number = db.Column(db.String(15), nullable=True)
    is_nominee = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f'<FamilyMember id={self.id}, name={self.name}, relationship={self.relationship}>'


class NewsUpdate(db.Model):
    """News and updates for the login page."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    employer_id = db.Column(db.Integer, db.ForeignKey('employer_profile.id'), nullable=False)
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    link = db.Column(db.String(255), nullable=True)
    link_text = db.Column(db.String(100), nullable=True)
    
    def __repr__(self):
        return f'<NewsUpdate id={self.id}, title={self.title}>'


class PasswordResetToken(db.Model):
    """Password reset tokens for users."""
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    
    @classmethod
    def generate_token(cls, user_id, expiration=3600):
        """Generate a new token for the user.
        
        Args:
            user_id: The ID of the user
            expiration: Token expiration time in seconds (default: 1 hour)
        
        Returns:
            A PasswordResetToken instance
        """
        token = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        return cls(user_id=user_id, token=token, expires_at=expires_at)
    
    def is_expired(self):
        """Check if the token has expired."""
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id}, expires={self.expires_at}>'