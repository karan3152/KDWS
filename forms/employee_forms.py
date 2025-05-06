from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, FileField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Optional, Regexp
from flask_wtf.file import FileAllowed

class EmployeeProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Phone number must be between 10 and 15 digits'),
        Regexp(r'^\+?\d+$', message='Invalid phone number format')
    ])
    address = TextAreaField('Address', validators=[
        DataRequired(),
        Length(min=10, max=200, message='Address must be between 10 and 200 characters')
    ])
    department = StringField('Department', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Department must be between 2 and 50 characters')
    ])
    position = StringField('Position', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Position must be between 2 and 50 characters')
    ])
    joining_date = DateField('Joining Date', validators=[DataRequired()])
    photo = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed')
    ])
    submit = SubmitField('Update Profile')

class EmployeeProfileEditForm(EmployeeProfileForm):
    pass

class DocumentUploadForm(FlaskForm):
    document_type = SelectField('Document Type', validators=[DataRequired()], choices=[
        ('id_proof', 'ID Proof'),
        ('address_proof', 'Address Proof'),
        ('qualification', 'Qualification'),
        ('experience', 'Experience'),
        ('other', 'Other')
    ])
    document = FileField('Document', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'jpg', 'jpeg', 'png'], 'Only PDF and image files are allowed')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    submit = SubmitField('Upload Document')

class FamilyMemberForm(FlaskForm):
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Name must be between 2 and 100 characters')
    ])
    relationship = SelectField('Relationship', validators=[DataRequired()], choices=[
        ('spouse', 'Spouse'),
        ('child', 'Child'),
        ('parent', 'Parent'),
        ('sibling', 'Sibling'),
        ('other', 'Other')
    ])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    aadhar_id = StringField('Aadhar ID', validators=[
        Optional(),
        Length(min=12, max=12, message='Aadhar ID must be exactly 12 digits'),
        Regexp(r'^\d{12}$', message='Aadhar ID must contain exactly 12 digits')
    ])
    contact_number = StringField('Contact Number', validators=[
        Optional(),
        Length(min=10, max=15, message='Contact number must be between 10 and 15 digits'),
        Regexp(r'^\+?\d+$', message='Invalid contact number format')
    ])
    photo = FileField('Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed')
    ])
    submit = SubmitField('Add Family Member')

class JoiningForm(FlaskForm):
    surname = StringField('Surname', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Surname must be between 2 and 50 characters')
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    middle_name = StringField('Middle Name', validators=[
        Optional(),
        Length(max=50, message='Middle name must be at most 50 characters')
    ])
    parent_name = StringField('Father/Mother/Spouse Name', validators=[
        Optional(),
        Length(max=100, message='Name must be at most 100 characters')
    ])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    age = StringField('Age', validators=[Optional()])
    place_of_birth = StringField('Place of Birth', validators=[Optional()])
    sex = SelectField('Sex', validators=[Optional()], choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ])
    marital_status = SelectField('Marital Status', validators=[DataRequired()], choices=[
        ('single', 'Single'),
        ('married', 'Married'),
        ('divorced', 'Divorced'),
        ('widowed', 'Widowed')
    ])
    nationality = StringField('Nationality', validators=[Optional()])
    religion = StringField('Religion', validators=[Optional()])
    blood_group = SelectField('Blood Group', validators=[Optional()], choices=[
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-')
    ])
    category = SelectField('Category', validators=[Optional()], choices=[
        ('general', 'General'),
        ('obc', 'OBC'),
        ('sc', 'SC'),
        ('st', 'ST'),
        ('other', 'Other')
    ])
    correspondence_address = TextAreaField('Correspondence Address', validators=[Optional()])
    correspondence_pin = StringField('Correspondence PIN Code', validators=[Optional()])
    permanent_address = TextAreaField('Permanent Address', validators=[Optional()])
    permanent_pin = StringField('Permanent PIN Code', validators=[Optional()])
    mobile_number = StringField('Mobile Number', validators=[Optional()])
    emergency_contact = StringField('Emergency Contact Number', validators=[Optional()])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    aadhar_no = StringField('AADHAR Number', validators=[Optional()])
    pan_no = StringField('PAN Number', validators=[Optional()])
    voter_id = StringField('Voter ID Number', validators=[Optional()])
    esi_no = StringField('ESI Number', validators=[Optional()])
    bank_name = StringField('Bank Name', validators=[Optional()])
    account_no = StringField('Account Number', validators=[Optional()])
    ifsc_code = StringField('IFSC Code', validators=[Optional()])
    branch_name = StringField('Branch Name', validators=[Optional()])
    photo = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed')
    ])
    declaration = SelectField('Declaration', validators=[Optional()], choices=[
        ('yes', 'Yes'),
        ('no', 'No')
    ])
    place = StringField('Place', validators=[Optional()])
    date = DateField('Date', validators=[Optional()])
    submit = SubmitField('Submit Form')

class EmployeeSearchForm(FlaskForm):
    query = StringField('Search', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Search query must be between 2 and 100 characters')
    ])
    submit = SubmitField('Search')

class PFForm(FlaskForm):
    pf_number = StringField('PF Number', validators=[
        DataRequired(),
        Length(min=5, max=20, message='PF Number must be between 5 and 20 characters')
    ])
    uan_number = StringField('UAN Number', validators=[
        Optional(),
        Length(min=5, max=20, message='UAN Number must be between 5 and 20 characters')
    ])
    establishment_name = StringField('Establishment Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Establishment Name must be between 2 and 100 characters')
    ])
    establishment_code = StringField('Establishment Code', validators=[
        Optional(),
        Length(max=20, message='Establishment Code must be at most 20 characters')
    ])
    establishment_address = TextAreaField('Establishment Address', validators=[
        Optional(),
        Length(max=200, message='Establishment Address must be at most 200 characters')
    ])
    submit = SubmitField('Submit Form')
