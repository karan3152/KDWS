from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, DateField, IntegerField, DecimalField, MultipleFileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, ValidationError, Regexp
from datetime import date

from models import User


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')


class RegisterForm(FlaskForm):
    """Form for user registration."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=4, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'.*[A-Z].*', message='Password must contain at least one uppercase letter'),
        Regexp(r'.*[a-z].*', message='Password must contain at least one lowercase letter'),
        Regexp(r'.*\d.*', message='Password must contain at least one number'),
        Regexp(r'.*[!@#$%^&*()].*', message='Password must contain at least one special character (!@#$%^&*())')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    
    def validate_username(self, username):
        """Validate username is unique."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
    
    def validate_email(self, email):
        """Validate email is unique."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one or reset your password.')


class FirstLoginForm(FlaskForm):
    """Form for first-time login verification and password setting."""
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    aadhar_id = StringField('Aadhar Number', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'.*[A-Z].*', message='Password must contain at least one uppercase letter'),
        Regexp(r'.*[a-z].*', message='Password must contain at least one lowercase letter'),
        Regexp(r'.*\d.*', message='Password must contain at least one number'),
        Regexp(r'.*[!@#$%^&*()].*', message='Password must contain at least one special character (!@#$%^&*())')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])


class PasswordResetRequestForm(FlaskForm):
    """Form for requesting a password reset."""
    email = StringField('Email', validators=[DataRequired(), Email()])


class PasswordResetForm(FlaskForm):
    """Form for resetting password with a valid token."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        Regexp(r'.*[A-Z].*', message='Password must contain at least one uppercase letter'),
        Regexp(r'.*[a-z].*', message='Password must contain at least one lowercase letter'),
        Regexp(r'.*\d.*', message='Password must contain at least one number'),
        Regexp(r'.*[!@#$%^&*()].*', message='Password must contain at least one special character (!@#$%^&*())')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])


class EmployeeProfileForm(FlaskForm):
    """Form for employee profile self-edit."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15),
        Regexp(r'^\d+$', message='Phone number must contain only digits')
    ])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    position = StringField('Position', validators=[Optional(), Length(max=50)])
    joining_date = DateField('Date of Joining', validators=[Optional()])
    
    def validate_date_of_birth(self, date_of_birth):
        """Validate date of birth is not in the future."""
        if date_of_birth.data and date_of_birth.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')
    
    def validate_joining_date(self, joining_date):
        """Validate joining date is not in the future."""
        if joining_date.data and joining_date.data > date.today():
            raise ValidationError('Joining date cannot be in the future.')


class EmployeeProfileEditForm(FlaskForm):
    """Form for admin/employer to edit employee profile."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15),
        Regexp(r'^\d+$', message='Phone number must contain only digits')
    ])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    position = StringField('Position', validators=[Optional(), Length(max=50)])
    joining_date = DateField('Date of Joining', validators=[Optional()])
    
    # Only shown to admin
    employee_id = StringField('Employee ID', validators=[Optional(), Length(max=20)])
    aadhar_id = StringField('Aadhar Number', validators=[Optional(), Length(max=20)])
    
    def validate_date_of_birth(self, date_of_birth):
        """Validate date of birth is not in the future."""
        if date_of_birth.data and date_of_birth.data > date.today():
            raise ValidationError('Date of birth cannot be in the future.')
    
    def validate_joining_date(self, joining_date):
        """Validate joining date is not in the future."""
        if joining_date.data and joining_date.data > date.today():
            raise ValidationError('Joining date cannot be in the future.')


class EmployerProfileForm(FlaskForm):
    """Form for employer profile edit."""
    company_name = StringField('Company Name', validators=[DataRequired(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    contact_number = StringField('Contact Number', validators=[
        DataRequired(),
        Length(min=10, max=15),
        Regexp(r'^\d+$', message='Contact number must contain only digits')
    ])


class EmployeeSearchForm(FlaskForm):
    """Form for searching employees."""
    search_term = StringField('Search', validators=[Optional()])
    search_by = SelectField('Search By', choices=[
        ('name', 'Name'),
        ('employee_id', 'Employee ID'),
        ('aadhar_id', 'Aadhar Number'),
        ('department', 'Department')
    ])


class CreateEmployeeForm(FlaskForm):
    """Form for creating a new employee."""
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    employee_id = StringField('Employee ID', validators=[DataRequired(), Length(max=20)])
    aadhar_id = StringField('Aadhar Number', validators=[DataRequired(), Length(max=20)])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15),
        Regexp(r'^\d+$', message='Phone number must contain only digits')
    ])
    department = StringField('Department', validators=[Optional(), Length(max=50)])
    position = StringField('Position', validators=[Optional(), Length(max=50)])
    joining_date = DateField('Date of Joining', validators=[Optional()])
    
    def validate_email(self, email):
        """Validate email is unique."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')
    
    def validate_employee_id(self, employee_id):
        """Validate employee ID is unique."""
        from models import EmployeeProfile
        employee = EmployeeProfile.query.filter_by(employee_id=employee_id.data).first()
        if employee:
            raise ValidationError('Employee ID already exists. Please use a different one.')
    
    def validate_aadhar_id(self, aadhar_id):
        """Validate Aadhar ID is unique."""
        from models import EmployeeProfile
        employee = EmployeeProfile.query.filter_by(aadhar_id=aadhar_id.data).first()
        if employee:
            raise ValidationError('Aadhar number already exists. Please check and try again.')


class DocumentUploadForm(FlaskForm):
    """Form for uploading a document."""
    document_type = SelectField('Document Type', validators=[DataRequired()])
    file = FileField('File', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and image files are allowed.')
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=500)])


class FamilyMemberForm(FlaskForm):
    """Form for adding/editing family member details."""
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    relationship = StringField('Relationship', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    address = TextAreaField('Address', validators=[Optional(), Length(max=200)])
    contact_number = StringField('Contact Number', validators=[
        Optional(),
        Length(min=10, max=15),
        Regexp(r'^\d+$', message='Contact number must contain only digits')
    ])
    is_nominee = BooleanField('Is Nominee', default=False)


class NewsUpdateForm(FlaskForm):
    """Form for creating/editing news updates."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    is_active = BooleanField('Is Active', default=True)
    link = StringField('Link URL', validators=[Optional(), Length(max=255)])
    link_text = StringField('Link Text', validators=[Optional(), Length(max=100)])


class DocumentReviewForm(FlaskForm):
    """Form for reviewing a document."""
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], validators=[DataRequired()])
    feedback = TextAreaField('Feedback', validators=[Optional(), Length(max=500)])