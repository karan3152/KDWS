from datetime import datetime, timedelta
from flask_login import UserMixin
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import random
from extensions import db, Base
import pyotp
import qrcode
import io
import base64
import os

# User role constants
ROLE_ADMIN = 'admin'
ROLE_EMPLOYER = 'employer'
ROLE_EMPLOYEE = 'employee'


class User(UserMixin, db.Model):
    """User model representing all users in the system."""

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'employer', 'employee'
    is_active = db.Column(db.Boolean, default=True)
    two_factor_enabled = db.Column(db.Boolean, default=False)
    two_factor_secret = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    photo_path = db.Column(db.String(255))
    first_login = db.Column(db.Boolean, default=True)
    is_temporary_password = db.Column(db.Boolean, default=True)
    initial_password = db.Column(db.String(64), nullable=True)

    # Relationships
    employee_profile = db.relationship('EmployeeProfile', back_populates='user', uselist=False, lazy=True,
                                      cascade="all, delete-orphan")
    employer_profile = db.relationship('EmployerProfile', back_populates='user', uselist=False, lazy=True,
                                      cascade="all, delete-orphan")

    def set_password(self, password, is_temporary=False):
        """Set the password hash for the user.

        Args:
            password: The plain text password to hash
            is_temporary: Whether this is a temporary password (default: False)
        """
        self.password_hash = generate_password_hash(password)

        # If this is a temporary password, store it and mark as temporary
        if is_temporary:
            self.initial_password = password
            self.is_temporary_password = True
        else:
            # If user is changing their password, mark it as not temporary
            # and clear the initial password for security
            self.is_temporary_password = False
            self.initial_password = None

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
            return self.email

    def enable_2fa(self):
        if not self.two_factor_secret:
            self.two_factor_secret = pyotp.random_base32()
        self.two_factor_enabled = True
        return self.two_factor_secret

    def disable_2fa(self):
        self.two_factor_enabled = False
        self.two_factor_secret = None

    def verify_2fa(self, token):
        if not self.two_factor_enabled or not self.two_factor_secret:
            return False
        totp = pyotp.TOTP(self.two_factor_secret)
        return totp.verify(token)

    def get_2fa_qr_code(self):
        if not self.two_factor_secret:
            return None
        totp = pyotp.TOTP(self.two_factor_secret)
        provisioning_uri = totp.provisioning_uri(self.email, issuer_name="WorkforceHive")

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode()

    def create_reset_token(self, custom_token=None):
        """Create a password reset token for the user.

        Args:
            custom_token: Optional custom token for testing

        Returns:
            The token string
        """
        # Delete any existing tokens for this user
        PasswordResetToken.query.filter_by(user_id=self.id).delete()

        # Create a new token
        if custom_token:
            token_obj = PasswordResetToken(
                user_id=self.id,
                token=custom_token,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
        else:
            token_obj = PasswordResetToken.generate_token(self.id)

        db.session.add(token_obj)
        db.session.commit()

        return token_obj.token

    def __repr__(self):
        return f'<User {self.email}>'


class Client(db.Model):
    """Client/Project model for organizing employees."""

    __tablename__ = 'client'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(10), nullable=False, unique=True)  # Short code for ID generation
    description = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    contact_email = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    address = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    creator = db.relationship('User', backref='created_clients', foreign_keys=[created_by])

    def __repr__(self):
        return f'<Client {self.name} ({self.code})>'


class EmployeeProfile(db.Model):
    """Employee profile model."""

    __tablename__ = 'employee_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10))
    phone_number = db.Column(db.String(15))
    address = db.Column(db.String(255))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(15))
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    employment_status = db.Column(db.String(20))  # full-time, part-time, contractor
    salary = db.Column(db.Float)
    bank_account = db.Column(db.String(50))
    tax_id = db.Column(db.String(50))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    employee_code = db.Column(db.String(20), unique=True)  # Custom employee code based on client
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='employee_profile')
    client = db.relationship('Client', backref='employees')
    family_members = db.relationship('FamilyMember', backref='employee', lazy=True)

    def get_full_name(self):
        """Get the full name of the employee."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f'<EmployeeProfile {self.first_name} {self.last_name}>'


class EmployerProfile(db.Model):
    """Profile for employer/HR users."""

    __tablename__ = 'employer_profile'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    company_address = db.Column(db.String(200))
    company_phone = db.Column(db.String(20))
    company_email = db.Column(db.String(120))
    industry = db.Column(db.String(100))
    company_size = db.Column(db.String(50))
    company_website = db.Column(db.String(200))
    department = db.Column(db.String(100))
    photo_path = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='employer_profile')

    def __repr__(self):
        return f'<EmployerProfile {self.company_name}>'


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
        """Return a list of all document types."""
        return [
            cls.AADHAR_CARD,
            cls.PAN_CARD,
            cls.PASSPORT,
            cls.PHOTO,
            cls.BANK_PASSBOOK,
            cls.CANCELLED_CHEQUE,
            cls.RESUME,
            cls.EDUCATIONAL_CERTIFICATES,
            cls.EXPERIENCE_CERTIFICATES,
            cls.NEW_JOINING_FORM,
            cls.PF_FORM,
            cls.FORM_11,
            cls.FORM_1_NOMINATION,
            cls.POLICE_VERIFICATION,
            cls.MEDICAL_CERTIFICATE,
            cls.FAMILY_DECLARATION
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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    title = db.Column(db.String(100))
    description = db.Column(db.Text)
    document_type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(255))  # Dedicated column for file path
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    content_type = db.Column(db.String(100), default='application/pdf')  # MIME type

    # These properties will be used instead of columns until migration is complete
    @property
    def document_name(self):
        """Get document name from file path."""
        if self.file_path:
            return os.path.basename(self.file_path)
        return None

    @property
    def document_number(self):
        """Placeholder for document number until migration is complete."""
        return None

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='documents')
    reviewer = db.relationship('User', backref='reviewed_documents', foreign_keys=[reviewed_by])
    employee = db.relationship('EmployeeProfile', foreign_keys=[employee_id], backref='documents')

    # For backward compatibility
    def get_file_path_from_description(self):
        """Get the file path from description field for backward compatibility."""
        if self.file_path:
            return self.file_path
        elif self.description and (self.description.startswith('D:') or self.description.startswith('uploads/')):
            return self.description
        return None

    def __repr__(self):
        return f'<Document id={self.id}, type={self.document_type}, status={self.status}>'


class FamilyMember(db.Model):
    """Family member details for employees."""

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee_profile.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    aadhar_id = db.Column(db.String(12))
    contact_number = db.Column(db.String(15))
    photo_filename = db.Column(db.String(255))
    photo_path = db.Column(db.String(255))  # Path to the photo file
    aadhar_filename = db.Column(db.String(255))
    aadhar_card_path = db.Column(db.String(255))  # Path to the Aadhar card document
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FamilyMember {self.name} ({self.relationship})>'


class NewsUpdate(db.Model):
    """News and updates for the login page."""

    __tablename__ = 'news_update'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    creator = db.relationship('User', backref=db.backref('news_updates', lazy=True))

    def __repr__(self):
        return f'<NewsUpdate {self.title}>'


class PasswordResetToken(db.Model):
    """Password reset tokens for users."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Relationship
    user = db.relationship('User', backref=db.backref('reset_tokens', lazy=True))

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


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<Image {self.title}>'


class OTP(db.Model):
    """One-time password model for verification."""

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), nullable=False)  # 'password_reset', 'account_activation'
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)

    # Relationship
    user = db.relationship('User', backref=db.backref('otps', lazy=True, cascade="all, delete-orphan"))

    @classmethod
    def generate_otp(cls, user_id, purpose, expiration=300):
        """Generate a new OTP for the user.

        Args:
            user_id: The ID of the user
            purpose: The purpose of the OTP ('password_reset', 'account_activation')
            expiration: OTP expiration time in seconds (default: 5 minutes)

        Returns:
            An OTP instance
        """
        # Delete any existing OTPs for this user and purpose
        cls.query.filter_by(user_id=user_id, purpose=purpose).delete()

        # Generate a random 6-digit OTP
        otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)

        otp = cls(
            user_id=user_id,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=expires_at
        )

        db.session.add(otp)
        db.session.commit()

        return otp

    def is_expired(self):
        """Check if the OTP has expired."""
        return datetime.utcnow() > self.expires_at

    def verify(self, entered_otp):
        """Verify the entered OTP.

        Args:
            entered_otp: The OTP entered by the user

        Returns:
            True if the OTP is valid, False otherwise
        """
        if self.is_expired() or self.is_verified:
            return False

        if self.otp_code == entered_otp:
            self.is_verified = True
            db.session.commit()
            return True

        return False

    def __repr__(self):
        return f'<OTP user_id={self.user_id}, purpose={self.purpose}, expires={self.expires_at}>'