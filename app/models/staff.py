"""
Staff covers non-teaching roles (accountant, receptionist, clerk, driver,
security guard, cleaner, office staff...). Unlike Teacher, a Staff record does
NOT require a User account — user_id is nullable. Only roles the system
actually has login-level access for (Accountant, Receptionist) can optionally
get one, created the same way a Teacher's account is (see account_service.py):
the Admin never sees or sets the password.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import EmploymentStatus


class Staff(db.Model, TimestampMixin):
    __tablename__ = "staff"
    __table_args__ = (
        db.UniqueConstraint("school_id", "employee_id", name="uq_staff_school_employee_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), unique=True, nullable=True)

    employee_id = db.Column(db.String(40), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    position = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(100))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    joining_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Numeric(12, 2))
    employment_status = db.Column(
        db.Enum(EmploymentStatus, name="staff_employment_status"), default=EmploymentStatus.ACTIVE, nullable=False
    )
    photo_path = db.Column(db.String(255))

    school = db.relationship("School")
    user = db.relationship("User")

    def __repr__(self):
        return f"<Staff {self.name} ({self.employee_id}) - {self.position}>"
