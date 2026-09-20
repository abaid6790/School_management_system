from flask_wtf import FlaskForm
from wtforms import StringField, DateField, TextAreaField, BooleanField, IntegerField, SelectField, TimeField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange, ValidationError

from app.models.enums import SubjectType


class PeriodForm(FlaskForm):
    name = StringField("Period Name", validators=[DataRequired(), Length(max=50)],
                        render_kw={"placeholder": "e.g. Period 1, Lunch Break"})
    order_index = IntegerField("Order", validators=[DataRequired(), NumberRange(min=1)])
    start_time = TimeField("Start Time", validators=[DataRequired()])
    end_time = TimeField("End Time", validators=[DataRequired()])
    is_break = BooleanField("This is a break (no subject/teacher expected)")
    submit = SubmitField("Save Period")

    def validate_end_time(self, field):
        if self.start_time.data and field.data and field.data <= self.start_time.data:
            raise ValidationError("End time must be after the start time.")


class AcademicSessionForm(FlaskForm):
    name = StringField("Session Name", validators=[DataRequired(), Length(max=50)],
                        render_kw={"placeholder": "e.g. 2026-2027"})
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    is_active = BooleanField("Make this the active session")
    description = TextAreaField("Description", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save Session")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data <= self.start_date.data:
            raise ValidationError("End date must be after the start date.")


class SchoolClassForm(FlaskForm):
    name = StringField("Class Name", validators=[DataRequired(), Length(max=80)],
                        render_kw={"placeholder": "e.g. Grade 8"})
    code = StringField("Class Code", validators=[Optional(), Length(max=30)])
    capacity = IntegerField("Capacity", validators=[Optional(), NumberRange(min=1, max=500)])
    class_teacher_id = SelectField("Class Teacher", coerce=int, validators=[Optional()])
    submit = SubmitField("Save Class")


class SectionForm(FlaskForm):
    name = StringField("Section Name", validators=[DataRequired(), Length(max=30)],
                        render_kw={"placeholder": "e.g. A"})
    room = StringField("Room", validators=[Optional(), Length(max=30)])
    capacity = IntegerField("Capacity", validators=[Optional(), NumberRange(min=1, max=500)])
    class_teacher_id = SelectField("Section Teacher", coerce=int, validators=[Optional()])
    submit = SubmitField("Save Section")


class SubjectForm(FlaskForm):
    name = StringField("Subject Name", validators=[DataRequired(), Length(max=100)])
    code = StringField("Subject Code", validators=[DataRequired(), Length(max=30)])
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    teacher_id = SelectField("Teacher", coerce=int, validators=[Optional()])
    max_marks = IntegerField("Maximum Marks", default=100, validators=[DataRequired(), NumberRange(min=1)])
    passing_marks = IntegerField("Passing Marks", default=40, validators=[DataRequired(), NumberRange(min=0)])
    subject_type = SelectField(
        "Type", choices=[(t.value, t.value.title()) for t in SubjectType], validators=[DataRequired()]
    )
    submit = SubmitField("Save Subject")

    def validate_passing_marks(self, field):
        if self.max_marks.data is not None and field.data is not None and field.data > self.max_marks.data:
            raise ValidationError("Passing marks cannot exceed maximum marks.")
