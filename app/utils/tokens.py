"""
Email verification and password-reset links both need a token that (a) can't be
forged, and (b) expires. itsdangerous.URLSafeTimedSerializer gives us both without
a separate tokens table — the token itself encodes the expiry, signed with SECRET_KEY.

Different `salt` values for different purposes means a leaked verification token
can't be replayed as a password-reset token, even though both derive from the
same SECRET_KEY.
"""
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

EMAIL_VERIFY_SALT = "email-verify"
PASSWORD_RESET_SALT = "password-reset"
ACCOUNT_SETUP_SALT = "account-setup"
EMAIL_VERIFY_MAX_AGE = 60 * 60 * 24       # 24 hours
PASSWORD_RESET_MAX_AGE = 60 * 60          # 1 hour
ACCOUNT_SETUP_MAX_AGE = 60 * 60 * 24      # 24 hours — new staff need more time to see the email than a reset does


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def generate_token(payload: str, salt: str) -> str:
    return _serializer().dumps(payload, salt=salt)


def confirm_token(token: str, salt: str, max_age_seconds: int):
    """Returns (payload, None) on success, or (None, "expired"/"invalid") on failure."""
    try:
        payload = _serializer().loads(token, salt=salt, max_age=max_age_seconds)
    except SignatureExpired:
        return None, "expired"
    except BadSignature:
        return None, "invalid"
    return payload, None
