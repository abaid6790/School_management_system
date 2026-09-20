from flask_wtf import FlaskForm
from wtforms import (
    StringField, DateField, TextAreaField, SelectField, EmailField,
)
from wtforms import SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email as EmailValidator

from app.models.enums import Gender

BLOOD_GROUPS = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


class StudentForm(FlaskForm):
    admission_number = StringField("Admission Number", validators=[DataRequired(), Length(max=40)])
    admission_date = DateField("Admission Date", validators=[DataRequired()])

    name = StringField("Student Name", validators=[DataRequired(), Length(max=150)])
    father_name = StringField("Father's Name", validators=[Optional(), Length(max=120)])
    mother_name = StringField("Mother's Name", validators=[Optional(), Length(max=120)])
    date_of_birth = DateField("Date of Birth", validators=[Optional()])
    gender = SelectField("Gender", choices=[("", "—")] + [(g.value, g.value.title()) for g in Gender],
                          validators=[Optional()])
    cnic_or_bform = StringField("CNIC / B-Form No.", validators=[Optional(), Length(max=40)])
    blood_group = SelectField("Blood Group", choices=[(b, b or "—") for b in BLOOD_GROUPS], validators=[Optional()])

    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    email = EmailField("Email", validators=[Optional(), EmailValidator(check_deliverability=False), Length(max=150)])
    address = StringField("Address", validators=[Optional(), Length(max=255)])
    city = StringField("City", validators=[Optional(), Length(max=100)])
    previous_school = StringField("Previous School", validators=[Optional(), Length(max=150)])

    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    section_id = SelectField("Section", coerce=int, validators=[DataRequired()])
    roll_number = StringField("Roll Number", validators=[DataRequired(), Length(max=20)])

    medical_info = TextAreaField("Medical / Emergency Info", validators=[Optional(), Length(max=2000)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=2000)])

    submit = SubmitField("Save Student")
