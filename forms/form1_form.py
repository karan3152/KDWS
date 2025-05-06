from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

class Form1(FlaskForm):
    # Personal details
    employee_name = StringField('Employee Name', validators=[DataRequired(), Length(max=100)])
    father_or_husband_name = StringField("Father's/Husband's Name", validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    sex = SelectField('Sex', choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], validators=[DataRequired()])
    permanent_address = TextAreaField('Permanent Address', validators=[DataRequired(), Length(max=200)])
    temporary_address = TextAreaField('Temporary Address', validators=[Optional(), Length(max=200)])
    
    # Nominee details
    nominee_name = StringField('Nominee Name', validators=[DataRequired(), Length(max=100)])
    nominee_relationship = StringField('Relationship with Nominee', validators=[DataRequired(), Length(max=50)])
    nominee_dob = DateField('Nominee Date of Birth', validators=[DataRequired()])
    nominee_address = TextAreaField('Nominee Address', validators=[DataRequired(), Length(max=200)])
    distribution_percentage = StringField('Distribution Percentage', validators=[DataRequired()])
    guardian_details = TextAreaField('Guardian Details (if nominee is minor)', validators=[Optional(), Length(max=200)])
    
    # Declaration
    no_family = BooleanField('I have no family as defined in Para 2(g) of the EPF Scheme, 1952')
    parents_dependent = BooleanField('My parents are dependent on me')
    employee_signature = StringField('Employee Signature', validators=[DataRequired()])
