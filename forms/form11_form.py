from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Length, Optional

class Form11(FlaskForm):
    # Personal Information
    title = StringField('Title', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    father_husband_name = StringField("Father's/Husband's Name", validators=[DataRequired(), Length(max=100)])
    relationship = StringField('Relationship', validators=[DataRequired()])
    gender = StringField('Gender', validators=[DataRequired()])
    marital_status = StringField('Marital Status', validators=[DataRequired()])
    mobile_number = StringField('Mobile Number', validators=[Optional(), Length(max=15)])
    email = StringField('Email', validators=[Optional(), Length(max=100)])
    
    # Previous Employment Details
    is_epf_member = StringField('EPF Member', validators=[DataRequired()])
    is_eps_member = StringField('EPS Member', validators=[DataRequired()])
    uan = StringField('UAN', validators=[Optional(), Length(max=12)])
    region_code = StringField('Region Code', validators=[Optional(), Length(max=2)])
    office_code = StringField('Office Code', validators=[Optional(), Length(max=2)])
    establishment_id = StringField('Establishment ID', validators=[Optional(), Length(max=3)])
    extension = StringField('Extension', validators=[Optional(), Length(max=2)])
    account_number = StringField('Account Number', validators=[Optional(), Length(max=3)])
    date_of_exit = DateField('Date of Exit', validators=[Optional()])
    scheme_certificate = StringField('Scheme Certificate', validators=[Optional(), Length(max=20)])
    ppo_number = StringField('PPO Number', validators=[Optional(), Length(max=20)])
    
    # Other Details
    is_international_worker = StringField('International Worker', validators=[DataRequired()])
    country_of_origin = StringField('Country of Origin', validators=[Optional()])
    other_country = StringField('Other Country', validators=[Optional()])
    passport_number = StringField('Passport Number', validators=[Optional(), Length(max=20)])
    passport_valid_from = DateField('Passport Valid From', validators=[Optional()])
    passport_valid_to = DateField('Passport Valid To', validators=[Optional()])
    education = StringField('Education', validators=[Optional()])
    is_specially_abled = StringField('Specially Abled', validators=[DataRequired()])
    disability_type = StringField('Disability Type', validators=[Optional()])
    
    # KYC Details
    bank_account = StringField('Bank Account', validators=[DataRequired(), Length(max=20)])
    ifsc_code = StringField('IFSC Code', validators=[DataRequired(), Length(max=11)])
    aadhaar = StringField('Aadhaar', validators=[Optional(), Length(max=12)])
    pan = StringField('PAN', validators=[Optional(), Length(max=10)])
    passport = StringField('Passport', validators=[Optional(), Length(max=20)])
    driving_license = StringField('Driving License', validators=[Optional(), Length(max=20)])
    election_card = StringField('Election Card', validators=[Optional(), Length(max=20)])
    ration_card = StringField('Ration Card', validators=[Optional(), Length(max=20)])
    esic_card = StringField('ESIC Card', validators=[Optional(), Length(max=20)])
    
    # Declaration
    agree_terms = BooleanField('Agree Terms', validators=[DataRequired()])
    agree_transfer = BooleanField('Agree Transfer', validators=[Optional()])
    declaration_date = DateField('Declaration Date', validators=[DataRequired()])
    declaration_place = StringField('Declaration Place', validators=[DataRequired(), Length(max=50)])
