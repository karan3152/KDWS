from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, Optional, ValidationError
from models import Client

class ClientForm(FlaskForm):
    """Form for adding or editing a client."""
    
    name = StringField('Client Name', validators=[DataRequired(), Length(min=2, max=100)])
    code = StringField('Client Code', validators=[DataRequired(), Length(min=2, max=10)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email()])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(max=20)])
    address = TextAreaField('Address', validators=[Optional(), Length(max=255)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Client')
    
    def validate_code(self, code):
        """Validate that the code is unique."""
        client = Client.query.filter_by(code=code.data).first()
        if client:
            raise ValidationError('This client code is already in use. Please choose a different one.')
