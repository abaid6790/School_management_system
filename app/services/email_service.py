"""
Sends transactional email via Flask-Mail using a Gmail App Password (MAIL_USERNAME/
MAIL_PASSWORD in .env). Every function returns True/False based on whether the SMTP
server actually accepted the message — callers must not tell the user an email was
sent unless this returns True, and should offer a resend path when it returns False.
"""
from flask import current_app, url_for
from flask_mail import Message
from app.extensions import mail


def _send(subject: str, recipient: str, body: str) -> bool:
    msg = Message(subject=subject, recipients=[recipient], body=body,
                  sender=current_app.config["MAIL_DEFAULT_SENDER"])
    try:
        mail.send(msg)
        return True
    except Exception as exc:  # SMTP errors, auth failures, network issues, etc.
        current_app.logger.error("Failed to send email to %s: %s", recipient, exc)
        return False


def send_verification_email(user, token: str) -> bool:
    link = url_for("auth.verify_email", token=token, _external=True)
    body = (
        f"Hello {user.name},\n\n"
        f"Welcome to {current_app.config['APP_NAME']}. Please verify your email address "
        f"by clicking the link below. This link expires in 24 hours.\n\n{link}\n\n"
        f"If you didn't create this account, you can ignore this email."
    )
    return _send("Verify your email address", user.email, body)


def send_account_setup_email(user, token: str) -> bool:
    link = url_for("auth.reset_password", token=token, _external=True)
    body = (
        f"Hello {user.name},\n\n"
        f"An account has been created for you on {current_app.config['APP_NAME']}. "
        f"Click the link below to set your password and get started. This link expires in 24 hours.\n\n{link}\n\n"
        f"Your login email is: {user.email}"
    )
    return _send("Set up your account", user.email, body)


def send_password_reset_email(user, token: str) -> bool:
    link = url_for("auth.reset_password", token=token, _external=True)
    body = (
        f"Hello {user.name},\n\n"
        f"We received a request to reset your password. Click the link below to set a "
        f"new password. This link expires in 1 hour.\n\n{link}\n\n"
        f"If you didn't request this, you can safely ignore this email — your password "
        f"will not change."
    )
    return _send("Reset your password", user.email, body)
