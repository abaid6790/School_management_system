from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, ValidationError

from app.models.enums import LeaveType


class LeaveRequestForm(FlaskForm):
    leave_type = SelectField("Leave Type", choices=[(t.value, t.value.title()) for t in LeaveType],
                              validators=[DataRequired()])
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[Optional(), Length(max=1000)])
    submit = SubmitField("Submit Leave Request")

    def validate_end_date(self, field):
        if self.start_date.data and field.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before the start date.")
