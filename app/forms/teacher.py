from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, DateField, SelectField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, Email as EmailValidator, NumberRange

from app.models.enums import Gender, EmploymentStatus


class TeacherForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = EmailField("Email", validators=[DataRequired(), EmailValidator(check_deliverability=False), Length(max=150)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])

    employee_id = StringField("Employee ID", validators=[DataRequired(), Length(max=40)])
    father_or_spouse_name = StringField("Father's/Spouse's Name", validators=[Optional(), Length(max=120)])
    date_of_birth = DateField("Date of Birth", validators=[Optional()])
    gender = SelectField("Gender", choices=[("", "—")] + [(g.value, g.value.title()) for g in Gender],
                          validators=[Optional()])
    address = TextAreaField("Address", validators=[Optional(), Length(max=255)])
    qualification = StringField("Qualification", validators=[Optional(), Length(max=200)])
    specialization = StringField("Specialization", validators=[Optional(), Length(max=200)])
    joining_date = DateField("Joining Date", validators=[DataRequired()])
    salary = DecimalField("Salary", places=2, validators=[Optional(), NumberRange(min=0)])

    submit = SubmitField("Save Teacher")


class TeacherStatusForm(FlaskForm):
    employment_status = SelectField(
        "Employment Status", choices=[(s.value, s.value.replace("_", " ").title()) for s in EmploymentStatus],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Status")
