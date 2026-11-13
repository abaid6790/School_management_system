from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateField, BooleanField
from wtforms.validators import DataRequired, Optional, Length

from app.models.enums import NoticeAudience
from app.services.notice_service import AUDIENCE_LABELS


class NoticeForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    body = TextAreaField("Message", validators=[DataRequired(), Length(max=5000)])
    audience = SelectField(
        "Send to", choices=[(a.value, AUDIENCE_LABELS[a]) for a in NoticeAudience], validators=[DataRequired()],
    )
    class_id = SelectField("Class", coerce=int, validators=[Optional()])
    section_id = SelectField("Section", coerce=int, validators=[Optional()])
    expires_on = DateField("Expires on (optional)", validators=[Optional()])
    is_pinned = BooleanField("Pin to the top")
