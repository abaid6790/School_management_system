from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, TimeField, TextAreaField, IntegerField, FloatField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError

from app.models.enums import ExamType


class ExamForm(FlaskForm):
    name = StringField("Exam Name", validators=[DataRequired(), Length(max=120)],
                        render_kw={"placeholder": "e.g. Midterm Exam"})
    exam_type = SelectField("Exam Type", choices=[(t.value, t.value.replace("_", " ").title()) for t in ExamType],
                             validators=[DataRequired()])
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Save Exam")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before the start date.")


class ExamSubjectForm(FlaskForm):
    subject_id = SelectField("Subject", coerce=int, validators=[DataRequired()])
    max_marks = IntegerField("Maximum Marks", validators=[DataRequired(), NumberRange(min=1)])
    passing_marks = IntegerField("Passing Marks", validators=[DataRequired(), NumberRange(min=0)])
    exam_date = DateField("Exam Date", validators=[Optional()])
    start_time = TimeField("Start Time", validators=[Optional()])
    end_time = TimeField("End Time", validators=[Optional()])
    room = StringField("Room", validators=[Optional(), Length(max=50)])
    submit = SubmitField("Save")

    def validate_passing_marks(self, field):
        if self.max_marks.data is not None and field.data is not None and field.data > self.max_marks.data:
            raise ValidationError("Passing marks cannot exceed maximum marks.")


class GradeBandForm(FlaskForm):
    grade = StringField("Grade", validators=[DataRequired(), Length(max=5)], render_kw={"placeholder": "e.g. A+"})
    min_percentage = FloatField("Minimum %", validators=[DataRequired(), NumberRange(min=0, max=100)])
    max_percentage = FloatField("Maximum %", validators=[DataRequired(), NumberRange(min=0, max=100)])
    order_index = IntegerField("Display Order", validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField("Save Grade Band")

    def validate_max_percentage(self, field):
        if self.min_percentage.data is not None and field.data is not None and field.data < self.min_percentage.data:
            raise ValidationError("Maximum % must be greater than or equal to minimum %.")
