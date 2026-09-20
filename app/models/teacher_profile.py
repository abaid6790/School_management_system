"""
Auth identity (name, email, phone, login) lives on User — a Teacher IS a User
with role=TEACHER. Everything HR-specific (employee id, qualifications, salary,
employment status) lives here instead, one-to-one with that User, so the auth
table doesn't grow an ever-longer tail of fields that only apply to some roles.

"Assigned subjects" and "assigned classes" are deliberately NOT duplicated here:
they already exist as Subject.teacher_id and SchoolClass/Section.class_teacher_id
(set from the Academic Setup screens). This model doesn't re-store that — a
teacher's profile page just queries those existing relationships.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin
from app.models.enums import Gender, EmploymentStatus


class TeacherProfile(db.Model, TimestampMixin):
    __tablename__ = "teacher_profiles"
    __table_args__ = (
        db.UniqueConstraint("school_id", "employee_id", name="uq_teacher_school_employee_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    employee_id = db.Column(db.String(40), nullable=False)
    father_or_spouse_name = db.Column(db.String(120))
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum(Gender, name="teacher_gender"))
    address = db.Column(db.String(255))
    qualification = db.Column(db.String(200))
    specialization = db.Column(db.String(200))
    joining_date = db.Column(db.Date, nullable=False)
    salary = db.Column(db.Numeric(12, 2))
    employment_status = db.Column(
        db.Enum(EmploymentStatus, name="employment_status"), default=EmploymentStatus.ACTIVE, nullable=False
    )
    photo_path = db.Column(db.String(255))

    school = db.relationship("School")
    user = db.relationship("User", backref=db.backref("teacher_profile", uselist=False, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<TeacherProfile employee_id={self.employee_id} user_id={self.user_id}>"
