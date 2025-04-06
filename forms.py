from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, FileField, HiddenField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional
from models import User, EmployeeProfile, DocumentTypes

class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField('Username/Employee ID/Aadhar ID', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PasswordResetRequestForm(FlaskForm):
    """Form for requesting a password reset."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class PasswordResetForm(FlaskForm):
    """Form for resetting password with a token."""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

class FirstLoginForm(FlaskForm):
    """Form for employees to set up their account on first login."""
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Update Password')

class CreateEmployeeForm(FlaskForm):
    """Form for admins to create employee accounts."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    aadhar_id = StringField('Aadhar ID', validators=[DataRequired(), Length(min=12, max=12)])
    employee_id = StringField('Employee ID', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])
    temporary_password = PasswordField('Temporary Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
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
        employee = EmployeeProfile.query.filter_by(aadhar_id=aadhar_id.data).first()
        if employee:
            raise ValidationError('Aadhar ID already registered.')
            
    def validate_employee_id(self, employee_id):
        employee = EmployeeProfile.query.filter_by(employee_id=employee_id.data).first()
        if employee:
            raise ValidationError('Employee ID already registered.')

class CreateEmployerForm(FlaskForm):
    """Form for admins to create employer/HR accounts."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    company_name = StringField('Company Name', validators=[DataRequired()])
    company_id = StringField('Company ID', validators=[DataRequired()])
    department = StringField('Department', validators=[DataRequired()])
    contact_number = StringField('Contact Number', validators=[DataRequired()])
    temporary_password = PasswordField('Temporary Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    submit = SubmitField('Create Employer Account')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken. Please choose a different one.')
            
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different one.')

class EmployeeProfileForm(FlaskForm):
    """Form for employees to update their profile information."""
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()], format='%Y-%m-%d')
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Update Profile')

class EmployeeSearchForm(FlaskForm):
    """Form for employers to search for employees."""
    search_type = SelectField('Search By', choices=[
        ('employee_id', 'Employee ID'),
        ('aadhar_id', 'Aadhar ID'),
        ('name', 'Name')
    ], validators=[DataRequired()])
    search_query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class DocumentUploadForm(FlaskForm):
    """Base form for document uploads."""
    document_type = HiddenField('Document Type')
    document_name = StringField('Document Name', validators=[DataRequired()])
    document_file = FileField('Upload Document', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only image files and PDFs are allowed!')
    ])
    document_number = StringField('Document Number', validators=[Optional()])
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[Optional()])
    expiry_date = DateField('Expiry Date', format='%Y-%m-%d', validators=[Optional()])
    submit = SubmitField('Upload Document')

class AadharUploadForm(DocumentUploadForm):
    """Form for uploading Aadhar card."""
    document_type = HiddenField('Document Type', default=DocumentTypes.AADHAR)
    document_name = StringField('Document Name', default='Aadhar Card', validators=[DataRequired()])
    document_number = StringField('Aadhar Number', validators=[
        DataRequired(),
        Length(min=12, max=12, message='Aadhar number must be 12 digits')
    ])
    
class PANUploadForm(DocumentUploadForm):
    """Form for uploading PAN card."""
    document_type = HiddenField('Document Type', default=DocumentTypes.PAN)
    document_name = StringField('Document Name', default='PAN Card', validators=[DataRequired()])
    document_number = StringField('PAN Number', validators=[
        DataRequired(),
        Length(min=10, max=10, message='PAN number must be 10 characters')
    ])

class PhotoUploadForm(DocumentUploadForm):
    """Form for uploading photo."""
    document_type = HiddenField('Document Type', default=DocumentTypes.PHOTO)
    document_name = StringField('Document Name', default='Passport Size Photo', validators=[DataRequired()])
    document_file = FileField('Upload Photo', validators=[
        FileRequired(message='Please select a photo'),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only image files are allowed!')
    ])

class PassbookUploadForm(DocumentUploadForm):
    """Form for uploading passbook."""
    document_type = HiddenField('Document Type', default=DocumentTypes.PASSBOOK)
    document_name = StringField('Document Name', default='Bank Passbook', validators=[DataRequired()])
    document_number = StringField('Account Number', validators=[DataRequired()])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    ifsc_code = StringField('IFSC Code', validators=[DataRequired()])
    
class JoiningFormUploadForm(DocumentUploadForm):
    """Form for uploading joining form."""
    document_type = HiddenField('Document Type', default=DocumentTypes.JOINING_FORM)
    document_name = StringField('Document Name', default='Joining Application Form', validators=[DataRequired()])
    document_file = FileField('Upload Joining Form', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed!')
    ])
    
class PFFormUploadForm(DocumentUploadForm):
    """Form for uploading PF form."""
    document_type = HiddenField('Document Type', default=DocumentTypes.PF_FORM)
    document_name = StringField('Document Name', default='PF Form 2', validators=[DataRequired()])
    document_file = FileField('Upload PF Form', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed!')
    ])
    
class Form1UploadForm(DocumentUploadForm):
    """Form for uploading Form 1."""
    document_type = HiddenField('Document Type', default=DocumentTypes.FORM1)
    document_name = StringField('Document Name', default='Nomination & Declaration Form', validators=[DataRequired()])
    document_file = FileField('Upload Form 1', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed!')
    ])
    
class Form11UploadForm(DocumentUploadForm):
    """Form for uploading Form 11."""
    document_type = HiddenField('Document Type', default=DocumentTypes.FORM11)
    document_name = StringField('Document Name', default='Form 11', validators=[DataRequired()])
    document_file = FileField('Upload Form 11', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed!')
    ])
    
class PoliceVerificationUploadForm(DocumentUploadForm):
    """Form for uploading Police Verification Certificate."""
    document_type = HiddenField('Document Type', default=DocumentTypes.POLICE_VERIFICATION)
    document_name = StringField('Document Name', default='Police Verification Certificate', validators=[DataRequired()])
    document_file = FileField('Upload Certificate', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only image files and PDFs are allowed!')
    ])
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[DataRequired()])
    document_number = StringField('Certificate Number', validators=[Optional()])

class MedicalCertificateUploadForm(DocumentUploadForm):
    """Form for uploading Medical Certificate."""
    document_type = HiddenField('Document Type', default=DocumentTypes.MEDICAL_CERTIFICATE)
    document_name = StringField('Document Name', default='Medical Certificate', validators=[DataRequired()])
    document_file = FileField('Upload Certificate', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only image files and PDFs are allowed!')
    ])
    issue_date = DateField('Issue Date', format='%Y-%m-%d', validators=[DataRequired()])
    expiry_date = DateField('Valid Until', format='%Y-%m-%d', validators=[Optional()])

class FamilyMemberForm(FlaskForm):
    """Form for adding family member details."""
    name = StringField('Name', validators=[DataRequired()])
    relationship = SelectField('Relationship', choices=[
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', format='%Y-%m-%d', validators=[Optional()])
    aadhar_id = StringField('Aadhar Number', validators=[Optional(), Length(min=12, max=12, message='Aadhar number must be 12 digits')])
    contact_number = StringField('Contact Number', validators=[Optional()])
    photo = FileField('Upload Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only image files are allowed!')
    ])
    submit = SubmitField('Add Family Member')

class FamilyDetailsUploadForm(DocumentUploadForm):
    """Form for uploading Family Details Document."""
    document_type = HiddenField('Document Type', default=DocumentTypes.FAMILY_DETAILS)
    document_name = StringField('Document Name', default='Family Details', validators=[DataRequired()])
    document_file = FileField('Upload Document', validators=[
        FileRequired(message='Please select a file'),
        FileAllowed(['pdf'], 'Only PDF files are allowed!')
    ])

class NewsUpdateForm(FlaskForm):
    """Form for employers to create news and updates."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    content = TextAreaField('Content', validators=[DataRequired()])
    is_active = BooleanField('Published', default=True)
    is_interview_notice = BooleanField('This is an interview notice')
    location_address = TextAreaField('Interview Location', validators=[Optional()])
    interview_date = DateTimeField('Interview Date and Time', format='%Y-%m-%d %H:%M', validators=[Optional()])
    submit = SubmitField('Publish Update')
