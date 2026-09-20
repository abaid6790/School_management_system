from flask_wtf import FlaskForm
from wtforms import (
    StringField, EmailField, DateField, DecimalField, TextAreaField, BooleanField, SelectField, SubmitField,
)
from wtforms.validators import DataRequired, Optional, Length, Email as EmailValidator, NumberRange, ValidationError

LOGIN_CAPABLE_ROLES = [("accountant", "Accountant"), ("receptionist", "Receptionist")]


class StaffForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    employee_id = StringField("Employee ID", validators=[DataRequired(), Length(max=40)])
    position = StringField("Position", validators=[DataRequired(), Length(max=100)],
                            render_kw={"placeholder": "e.g. Accountant, Driver, Security Guard, Cleaner"})
    department = StringField("Department", validators=[Optional(), Length(max=100)])
    phone = StringField("Phone", validators=[Optional(), Length(max=30)])
    address = TextAreaField("Address", validators=[Optional(), Length(max=255)])
    joining_date = DateField("Joining Date", validators=[DataRequired()])
    salary = DecimalField("Salary", places=2, validators=[Optional(), NumberRange(min=0)])

    needs_login = BooleanField("This staff member needs to log into the system")
    system_role = SelectField("System Role", choices=LOGIN_CAPABLE_ROLES, validators=[Optional()])
    email = EmailField("Email (for login)", validators=[Optional(), EmailValidator(check_deliverability=False), Length(max=150)])

    submit = SubmitField("Save Staff")
