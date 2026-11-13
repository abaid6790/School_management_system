from datetime import date

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField
from wtforms.validators import DataRequired, Optional, Length


class HomeworkEditForm(FlaskForm):
    """Class, section and subject are fixed once homework exists (submission records
    refer to that group of students) — to change them, cancel and create a new one."""
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Instructions", validators=[Optional(), Length(max=5000)])
    assigned_date = DateField("Assigned on", validators=[DataRequired()], default=date.today)
    due_date = DateField("Due on", validators=[DataRequired()])
    teacher_id = SelectField("Teacher", coerce=int, validators=[Optional()])   # Admin only (removed for teachers)


class HomeworkForm(HomeworkEditForm):
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    section_id = SelectField("Section", coerce=int, validators=[Optional()])
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
