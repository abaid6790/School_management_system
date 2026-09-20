from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models import School, User, SchoolSettings
from app.models.enums import UserRole
from app.forms.auth import (
    RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm, ResendVerificationForm,
)
from app.services.email_service import send_verification_email, send_password_reset_email
from app.services.audit_service import log_action
from app.utils.tokens import (
    generate_token, confirm_token,
    EMAIL_VERIFY_SALT, PASSWORD_RESET_SALT, ACCOUNT_SETUP_SALT,
    EMAIL_VERIFY_MAX_AGE, PASSWORD_RESET_MAX_AGE, ACCOUNT_SETUP_MAX_AGE,
)
from app.utils.url_safety import is_safe_redirect_url

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegisterForm()
    if form.validate_on_submit():
        school = School(name=form.school_name.data.strip(), slug=form.school_slug.data.lower().strip())
        db.session.add(school)
        db.session.flush()  # need school.id before creating dependent rows

        db.session.add(SchoolSettings(school_id=school.id))

        admin = User(
            school_id=school.id,
            name=form.admin_name.data.strip(),
            email=form.admin_email.data.lower().strip(),
            role=UserRole.ADMIN,
        )
        admin.set_password(form.password.data)

        token = generate_token(admin.email, salt=EMAIL_VERIFY_SALT)
        admin.verification_token = token
        admin.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=EMAIL_VERIFY_MAX_AGE
        )
        db.session.add(admin)
        db.session.flush()

        log_action(
            "school.registered", "schools", school.id,
            new_value={"name": school.name, "slug": school.slug}, school_id=school.id,
        )
        log_action(
            "user.registered", "users", admin.id,
            new_value={"email": admin.email, "role": admin.role.value}, school_id=school.id,
        )
        db.session.commit()

        if send_verification_email(admin, token):
            flash("Account created! Check your email to verify your address before logging in.", "success")
        else:
            flash(
                "Account created, but the verification email couldn't be sent right now. "
                "Use 'Resend verification email' on the login page once that's resolved.",
                "warning",
            )
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/verify/<token>")
def verify_email(token):
    email, error = confirm_token(token, salt=EMAIL_VERIFY_SALT, max_age_seconds=EMAIL_VERIFY_MAX_AGE)

    if error == "expired":
        flash("Your verification link has expired. Request a new one below.", "warning")
        return redirect(url_for("auth.resend_verification"))
    if error == "invalid" or not email:
        flash("That verification link is invalid.", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email, verification_token=token).first()
    if not user:
        flash("This verification link has already been used or is invalid.", "danger")
        return redirect(url_for("auth.login"))

    user.is_verified = True
    user.verification_token = None
    user.verification_token_expires_at = None
    log_action("user.email_verified", "users", user.id, school_id=user.school_id)
    db.session.commit()

    flash("Your email is verified. You can now log in.", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    form = ResendVerificationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and not user.is_verified:
            token = generate_token(user.email, salt=EMAIL_VERIFY_SALT)
            user.verification_token = token
            user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=EMAIL_VERIFY_MAX_AGE
            )
            db.session.commit()
            if not send_verification_email(user, token):
                flash("We couldn't send the email right now — please try again shortly.", "warning")
                return redirect(url_for("auth.login"))
        # Same message whether or not the account exists / is already verified —
        # doesn't leak which emails are registered.
        flash("If that email needs verification, a new link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/resend_verification.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()

        if not user or not user.check_password(form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_verified:
            flash("Please verify your email before logging in.", "warning")
            return render_template("auth/login.html", form=form)

        if not user.is_active_account:
            flash("Your account has been deactivated. Contact your school administrator.", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember.data)
        user.last_login_at = datetime.now(timezone.utc)
        log_action("user.login", "users", user.id)
        db.session.commit()

        next_url = request.args.get("next")
        if next_url and is_safe_redirect_url(next_url):
            return redirect(next_url)
        return redirect(url_for("dashboard.index"))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_action("user.logout", "users", current_user.id)
    db.session.commit()
    logout_user()
    flash("You've been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user:
            token = generate_token(user.email, salt=PASSWORD_RESET_SALT)
            send_password_reset_email(user, token)
        # Same message regardless of whether the account exists.
        flash("If that email is registered, a password reset link has been sent.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    email, error = confirm_token(token, salt=PASSWORD_RESET_SALT, max_age_seconds=PASSWORD_RESET_MAX_AGE)
    if error:
        # Also accept a new-staff-account-setup link — it points at this same
        # page since "set your password" and "reset your password" are the
        # same form; only the token's origin/expiry differs.
        email, error = confirm_token(token, salt=ACCOUNT_SETUP_SALT, max_age_seconds=ACCOUNT_SETUP_MAX_AGE)
    if error:
        flash("That password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("That password reset link is invalid.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        log_action("user.password_reset", "users", user.id, school_id=user.school_id)
        db.session.commit()
        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", form=form)
