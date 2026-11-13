from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

from app.models.enums import EventType


class EventForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    event_type = SelectField("Type", choices=[(t.value, t.value.title()) for t in EventType], validators=[DataRequired()])
    start_date = DateField("Starts on", validators=[DataRequired()])
    end_date = DateField("Ends on (leave blank for a one-day event)", validators=[Optional()])
    start_time = TimeField("Start time (optional)", validators=[Optional()])
    end_time = TimeField("End time (optional)", validators=[Optional()])
    location = StringField("Location", validators=[Optional(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    is_holiday = BooleanField("The school is closed on these days")
