from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FileField, SubmitField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Optional, Regexp, URL
from flask_wtf.file import FileAllowed

class EmployerProfileForm(FlaskForm):
    company_name = StringField('Company Name', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Company name must be between 2 and 100 characters')
    ])
    company_address = TextAreaField('Company Address', validators=[
        DataRequired(),
        Length(min=10, max=200, message='Address must be between 10 and 200 characters')
    ])
    company_phone = StringField('Company Phone', validators=[
        DataRequired(),
        Length(min=10, max=20, message='Phone number must be between 10 and 20 digits'),
        Regexp(r'^\+?\d+$', message='Invalid phone number format')
    ])
    company_email = StringField('Company Email', validators=[
        DataRequired(),
        Email(message='Invalid email address'),
        Length(max=120)
    ])
    industry = StringField('Industry', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Industry must be between 2 and 100 characters')
    ])
    company_size = SelectField('Company Size', choices=[
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('501-1000', '501-1000 employees'),
        ('1000+', '1000+ employees')
    ], validators=[DataRequired()])
    company_website = StringField('Company Website', validators=[
        Optional(),
        URL(message='Invalid URL format'),
        Length(max=200)
    ])
    department = StringField('Department', validators=[
        DataRequired(),
        Length(min=2, max=100, message='Department must be between 2 and 100 characters')
    ])
    photo = FileField('Company Logo', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Only JPEG and PNG images are allowed')
    ])
    submit = SubmitField('Update Profile')

class EmployerProfileEditForm(EmployerProfileForm):
    pass

class EmployeeSearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    search_type = SelectField('Search Type', choices=[
        ('auto', 'Auto Detect'),
        ('name', 'Name'),
        ('aadhar', 'Aadhar ID'),
        ('employee_id', 'Employee ID')
    ], default='auto')
    submit = SubmitField('Search')

class NewsUpdateForm(FlaskForm):
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=5, max=100, message='Title must be between 5 and 100 characters')
    ])
    content = TextAreaField('Content', validators=[
        DataRequired(),
        Length(min=10, message='Content must be at least 10 characters')
    ])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save') 