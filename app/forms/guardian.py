from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email as EmailValidator, ValidationError


class GuardianForm(FlaskForm):
    father_name = StringField("Father's Name", validators=[Optional(), Length(max=120)])
    mother_name = StringField("Mother's Name", validators=[Optional(), Length(max=120)])
    phone = StringField("Phone", validators=[DataRequired(), Length(max=30)])
    alternate_phone = StringField("Alternate Phone", validators=[Optional(), Length(max=30)])
    email = EmailField("Email", validators=[Optional(), EmailValidator(check_deliverability=False), Length(max=150)])
    occupation = StringField("Occupation", validators=[Optional(), Length(max=120)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    emergency_contact_name = StringField("Emergency Contact Name", validators=[Optional(), Length(max=120)])
    emergency_contact_phone = StringField("Emergency Contact Phone", validators=[Optional(), Length(max=30)])
    submit = SubmitField("Save Guardian")

    def validate_mother_name(self, field):
        if not self.father_name.data and not field.data:
            raise ValidationError("Provide at least a father's or mother's name.")
