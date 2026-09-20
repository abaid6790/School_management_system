"""
Admin-created staff accounts (teachers, and later staff who need logins) never
have a password chosen or seen by the Admin — a random, unusable-in-practice
password is set internally purely to satisfy the NOT NULL column, and the real
password is chosen by the staff member themselves via the same emailed-link
flow as a password reset. is_verified is set True immediately since the Admin
creating the account is itself the trust signal — there's no separate email
loop to prove the address is reachable before they can log in, only before
they've SET a password.
"""
import secrets
from datetime import datetime, timezone, timedelta

from app.extensions import db
from app.models import User
from app.utils.tokens import generate_token, ACCOUNT_SETUP_SALT, ACCOUNT_SETUP_MAX_AGE


def create_staff_account(school_id: int, name: str, email: str, role, phone: str | None = None) -> tuple[User, str]:
    user = User(
        school_id=school_id,
        name=name,
        email=email.lower().strip(),
        role=role,
        phone=phone or None,
        is_verified=True,
    )
    user.set_password(secrets.token_urlsafe(32))  # never communicated to anyone; overwritten via setup link
    db.session.add(user)
    db.session.flush()

    token = generate_token(user.email, salt=ACCOUNT_SETUP_SALT)
    # Reuses the User.verification_token columns as generic "pending link" storage —
    # they're free once is_verified=True, and this keeps a single-use-token pattern
    # for setup links consistent with how email verification already works.
    user.verification_token = token
    user.verification_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=ACCOUNT_SETUP_MAX_AGE)

    return user, token
