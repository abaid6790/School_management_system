from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, NumberRange


class MeetingForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    description = TextAreaField("Details", validators=[Optional(), Length(max=2000)])
    meeting_date = DateField("Date", validators=[DataRequired()])
    start_time = TimeField("Starts at", validators=[DataRequired()])
    end_time = TimeField("Ends at", validators=[DataRequired()])
    slot_minutes = IntegerField("Minutes per appointment", default=10,
                                validators=[DataRequired(), NumberRange(min=5, max=120)])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    class_id = SelectField("Class (optional)", coerce=int, validators=[Optional()])
    section_id = SelectField("Section (optional)", coerce=int, validators=[Optional()])


class BookingForm(FlaskForm):
    teacher_id = SelectField("Teacher", coerce=int, validators=[DataRequired()])
    student_id = SelectField("Student", coerce=int, validators=[DataRequired()])
    slot = SelectField("Time slot", validators=[DataRequired()])
    guardian_id = IntegerField("Who is coming", validators=[Optional()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=1000)])
