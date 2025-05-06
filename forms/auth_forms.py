from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Optional, Regexp
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    role = SelectField('Role', choices=[
        ('employer', 'Employer'),
        ('employee', 'Employee')
    ], validators=[DataRequired()])
    submit = SubmitField('Register')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='First name must be between 2 and 50 characters')
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(),
        Length(min=2, max=50, message='Last name must be between 2 and 50 characters')
    ])
    phone_number = StringField('Phone Number', validators=[
        DataRequired(),
        Length(min=10, max=15, message='Phone number must be between 10 and 15 digits')
    ])
    address = TextAreaField('Address', validators=[
        DataRequired(),
        Length(min=10, max=200, message='Address must be between 10 and 200 characters')
    ])
    photo = FileField('Profile Photo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed')
    ])
    submit = SubmitField('Update Profile')

class DocumentUploadForm(FlaskForm):
    document_type = SelectField('Document Type', validators=[DataRequired()])
    document = FileField('Document', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'], 
                   'Only PDF, Word documents, and images are allowed')
    ])
    submit = SubmitField('Upload Document')

class PasswordResetForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Invalid email address')
    ])
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

class TwoFactorForm(FlaskForm):
    token = StringField('Verification Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Verification code must be 6 digits'),
        Regexp(r'^\d{6}$', message='Verification code must contain exactly 6 digits')
    ])
    submit = SubmitField('Verify')

class Enable2FAForm(FlaskForm):
    token = StringField('Verification Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='Verification code must be 6 digits'),
        Regexp(r'^\d{6}$', message='Verification code must contain exactly 6 digits')
    ])
    submit = SubmitField('Enable 2FA') 