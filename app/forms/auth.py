import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp, ValidationError

from app.models import School, User

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class RegisterForm(FlaskForm):
    school_name = StringField("School Name", validators=[DataRequired(), Length(max=150)])
    school_slug = StringField(
        "School URL Slug",
        validators=[
            DataRequired(),
            Length(min=3, max=80),
            Regexp(SLUG_REGEX, message="Use lowercase letters, numbers, and hyphens only."),
        ],
    )
    admin_name = StringField("Your Name", validators=[DataRequired(), Length(max=120)])
    admin_email = StringField("Your Email", validators=[DataRequired(), Email(check_deliverability=False), Length(max=150)])
    password = PasswordField(
        "Password", validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters.")]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Create School Account")

    def validate_school_slug(self, field):
        if School.query.filter_by(slug=field.data.lower().strip()).first():
            raise ValidationError("This school URL is already taken. Choose another.")

    def validate_admin_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists.")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False)])
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters.")]
    )
    confirm_password = PasswordField(
        "Confirm New Password", validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Reset Password")


class ResendVerificationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(check_deliverability=False)])
    submit = SubmitField("Resend Verification Email")
