"""
User is the auth identity for staff-side roles in Phase 0 (admin, teacher, accountant,
receptionist) plus a platform-level super_admin. Parent and Student logins are added
in a later phase, but the role values already exist in UserRole so the schema doesn't
need to change when that phase arrives.

Login identifier is email, unique across the whole platform (not per-school) — one
person has one account. A CHECK constraint keeps super_admin and school_id consistent:
a super_admin never belongs to a single school; everyone else must.
"""
from sqlalchemy import CheckConstraint
from flask_login import UserMixin

from app.extensions import db, bcrypt
from app.models.mixins import TimestampMixin
from app.models.enums import UserRole


class User(db.Model, UserMixin, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        # NOTE: db.Enum(PyEnum) stores the member's NAME by default ("SUPER_ADMIN"),
        # not its .value ("super_admin") — this must match that storage, not the
        # lowercase value used everywhere else in the app.
        CheckConstraint(
            "(role = 'SUPER_ADMIN' AND school_id IS NULL) OR "
            "(role != 'SUPER_ADMIN' AND school_id IS NOT NULL)",
            name="ck_super_admin_has_no_school",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(
        db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True
    )

    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole, name="user_role"), nullable=False, index=True)
    phone = db.Column(db.String(30))

    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(255), unique=True, nullable=True)
    verification_token_expires_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Named is_active_account (not is_active) so it doesn't collide with the
    # is_active property below, which Flask-Login actually checks at login time.
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # --- Relationships ---
    school = db.relationship("School", back_populates="users")

    # --- Password helpers ---
    def set_password(self, raw_password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(raw_password).decode("utf-8")

    def check_password(self, raw_password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw_password)

    # --- Flask-Login override ---
    @property
    def is_active(self):
        # Overrides UserMixin's default (always True): an unverified email or a
        # deactivated account must be blocked from logging in.
        return self.is_active_account and self.is_verified

    def __repr__(self):
        return f"<User {self.email} ({self.role.value})>"
