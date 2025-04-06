from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, DateField, SelectField, TextAreaField, SubmitField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, Regexp
from datetime import datetime

from models import User, EmployeeProfile, EmployerProfile


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=128)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class FirstLoginForm(FlaskForm):
    """Form for first-time login with Aadhar and Employee ID verification."""
    aadhar_id = StringField('Aadhar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message='Aadhar must be exactly 12 digits'),
        Regexp('^\d{12}$', message='Aadhar must contain only digits')
    ])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=5, max=20)])
    new_password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp('^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', 
               message='Password must include letters, numbers, and special characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Verify and Set Password')


class RegisterForm(FlaskForm):
    """Form for user registration (used by admin to create accounts)."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp('^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', 
               message='Password must include letters, numbers, and special characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[('employee', 'Employee'), ('employer', 'Employer'), ('admin', 'Admin')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')


class PasswordResetRequestForm(FlaskForm):
    """Form to request a password reset."""
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Request Password Reset')


class PasswordResetForm(FlaskForm):
    """Form to reset password with token."""
    password = PasswordField('New Password', validators=[
        DataRequired(), 
        Length(min=8, message='Password must be at least 8 characters'),
        Regexp('^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', 
               message='Password must include letters, numbers, and special characters')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(), 
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')


class EmployeeProfileForm(FlaskForm):
    """Form for employee to update their profile information."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(min=10, max=20),
        Regexp('^\+?[0-9]{10,15}$', message='Enter a valid phone number')
    ])
    address = TextAreaField('Address', validators=[DataRequired()])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    position = StringField('Position/Designation', validators=[Optional(), Length(max=50)])
    joining_date = DateField('Joining Date', validators=[Optional()])
    submit = SubmitField('Update Profile')


class EmployeeProfileEditForm(FlaskForm):
    """Form for admin/employer to edit employee profile (more fields)."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(min=10, max=20),
        Regexp('^\+?[0-9]{10,15}$', message='Enter a valid phone number')
    ])
    address = TextAreaField('Address', validators=[DataRequired()])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    position = StringField('Position/Designation', validators=[Optional(), Length(max=50)])
    joining_date = DateField('Joining Date', validators=[Optional()])
    aadhar_id = StringField('Aadhar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message='Aadhar must be exactly 12 digits'),
        Regexp('^\d{12}$', message='Aadhar must contain only digits')
    ])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(min=5, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    submit = SubmitField('Update Profile')


class EmployerProfileForm(FlaskForm):
    """Form for employer to update their profile information."""
    company_name = StringField('Company/Organization Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    contact_number = StringField('Contact Number', validators=[
        DataRequired(), 
        Length(min=10, max=20),
        Regexp('^\+?[0-9]{10,15}$', message='Enter a valid phone number')
    ])
    submit = SubmitField('Update Profile')


class EmployeeSearchForm(FlaskForm):
    """Form for searching employees."""
    query = StringField('Search', validators=[DataRequired(), Length(min=3, max=100)])
    search_type = SelectField('Search Type', choices=[
        ('auto', 'Auto-detect'), 
        ('aadhar', 'Aadhar ID'), 
        ('employee_id', 'Employee ID'), 
        ('email', 'Email'),
        ('name', 'Name'),
        ('all', 'All Fields')
    ])
    submit = SubmitField('Search')


class CreateEmployeeForm(FlaskForm):
    """Form for employers to create new employee accounts."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Temporary Password', validators=[DataRequired(), Length(min=8)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(), 
        Length(min=10, max=20),
        Regexp('^\+?[0-9]{10,15}$', message='Enter a valid phone number')
    ])
    aadhar_id = StringField('Aadhar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message='Aadhar must be exactly 12 digits'),
        Regexp('^\d{12}$', message='Aadhar must contain only digits')
    ])
    submit = SubmitField('Create Employee Account')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_aadhar_id(self, aadhar_id):
        profile = EmployeeProfile.query.filter_by(aadhar_id=aadhar_id.data).first()
        if profile:
            raise ValidationError('This Aadhar ID is already registered.')


class FamilyMemberForm(FlaskForm):
    """Form for adding family members."""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    relationship = SelectField('Relationship', choices=[
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other')
    ])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    aadhar_id = StringField('Aadhar Number (optional)', validators=[
        Optional(),
        Length(min=12, max=12, message='Aadhar must be exactly 12 digits'),
        Regexp('^\d{12}$', message='Aadhar must contain only digits')
    ])
    contact_number = StringField('Contact Number (optional)', validators=[
        Optional(),
        Length(min=10, max=20),
        Regexp('^\+?[0-9]{10,15}$', message='Enter a valid phone number')
    ])
    photo = FileField('Photo (optional)', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Add Family Member')


class NewsUpdateForm(FlaskForm):
    """Form for creating company news and updates."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    is_interview_notice = BooleanField('Is this an interview notice?')
    location_address = TextAreaField('Location/Address (for interview notices)', validators=[Optional()])
    interview_date = DateField('Interview Date', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Post Update')


# Document Upload Forms

class AadharUploadForm(FlaskForm):
    """Form for uploading Aadhar card."""
    document_number = StringField('Aadhar Number', validators=[
        DataRequired(), 
        Length(min=12, max=12, message='Aadhar must be exactly 12 digits'),
        Regexp('^\d{12}$', message='Aadhar must contain only digits')
    ])
    document_file = FileField('Aadhar Card Scan/Image', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')
    ])
    submit = SubmitField('Upload Aadhar Card')


class PANUploadForm(FlaskForm):
    """Form for uploading PAN card."""
    document_number = StringField('PAN Number', validators=[
        DataRequired(), 
        Length(min=10, max=10, message='PAN must be exactly 10 characters'),
        Regexp('^[A-Z]{5}[0-9]{4}[A-Z]{1}$', message='Enter a valid PAN number (e.g., ABCDE1234F)')
    ])
    document_file = FileField('PAN Card Scan/Image', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')
    ])
    submit = SubmitField('Upload PAN Card')


class PhotoUploadForm(FlaskForm):
    """Form for uploading passport size photo."""
    document_file = FileField('Passport Size Photo', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')
    ])
    submit = SubmitField('Upload Photo')


class PassbookUploadForm(FlaskForm):
    """Form for uploading bank passbook/statement."""
    document_number = StringField('Account Number', validators=[
        DataRequired(), 
        Length(min=5, max=30),
        Regexp('^\d+$', message='Account number must contain only digits')
    ])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(max=100)])
    ifsc_code = StringField('IFSC Code', validators=[
        DataRequired(), 
        Length(min=11, max=11, message='IFSC code must be exactly 11 characters'),
        Regexp('^[A-Z]{4}0[A-Z0-9]{6}$', message='Enter a valid IFSC code (e.g., SBIN0123456)')
    ])
    document_file = FileField('Bank Passbook/Statement Scan', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')
    ])
    submit = SubmitField('Upload Bank Details')


class JoiningFormUploadForm(FlaskForm):
    """Form for uploading joining form."""
    document_file = FileField('New Joining Application Form', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload Joining Form')


class PFFormUploadForm(FlaskForm):
    """Form for uploading PF form."""
    document_file = FileField('PF Form 2 (Revised)', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload PF Form')


class Form1UploadForm(FlaskForm):
    """Form for uploading Form 1 (Nomination & Declaration)."""
    document_file = FileField('Form 1 (Nomination & Declaration)', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload Form 1')


class Form11UploadForm(FlaskForm):
    """Form for uploading Form 11 (Revised)."""
    document_file = FileField('Form 11 (Revised)', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload Form 11')


class PoliceVerificationUploadForm(FlaskForm):
    """Form for uploading police verification document."""
    document_number = StringField('Certificate/Reference Number (if any)', validators=[Optional(), Length(max=50)])
    issue_date = DateField('Issue Date', validators=[Optional()])
    document_file = FileField('Police Verification Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')
    ])
    submit = SubmitField('Upload Police Verification')


class MedicalCertificateUploadForm(FlaskForm):
    """Form for uploading medical certificate."""
    issue_date = DateField('Issue Date', validators=[Optional()])
    expiry_date = DateField('Valid Until', validators=[Optional()])
    document_file = FileField('Medical Certificate', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')
    ])
    submit = SubmitField('Upload Medical Certificate')


class FamilyDetailsUploadForm(FlaskForm):
    """Form for uploading family details document."""
    document_file = FileField('Family Details Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'PDF or images only!')
    ])
    submit = SubmitField('Upload Family Details')


# Document Review Form (for employers)
class DocumentReviewForm(FlaskForm):
    """Form for employers to review and approve/reject documents."""
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ])
    feedback = TextAreaField('Feedback/Comments', validators=[Optional()])
    submit = SubmitField('Update Status')