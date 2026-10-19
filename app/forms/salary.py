from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class SalaryForm(FlaskForm):
    month = DateField("Month (any date within the month)", validators=[DataRequired()])
    basic_salary = DecimalField("Basic Salary", places=2, validators=[DataRequired(), NumberRange(min=0)])
    allowances = DecimalField("Allowances", places=2, validators=[Optional(), NumberRange(min=0)], default=0)
    deductions = DecimalField("Deductions", places=2, validators=[Optional(), NumberRange(min=0)], default=0)
    bonus = DecimalField("Bonus", places=2, validators=[Optional(), NumberRange(min=0)], default=0)
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save")
