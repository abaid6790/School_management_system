"""
amount is the billed amount before any discount. Discount and paid totals are
deliberately NOT columns here — they're always summed from FeeDiscount and
FeePayment rows (see fee_service.py), the same "never store what can be
derived" principle used for attendance stats and exam results. This makes a
fee's status structurally unable to disagree with its actual discount/payment
history.
"""
from app.extensions import db
from app.models.mixins import TimestampMixin


class StudentFee(db.Model, TimestampMixin):
    __tablename__ = "student_fees"

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    fee_type_id = db.Column(db.Integer, db.ForeignKey("fee_types.id", ondelete="RESTRICT"), nullable=False, index=True)
    session_id = db.Column(db.Integer, db.ForeignKey("academic_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)

    school = db.relationship("School")
    student = db.relationship("Student")
    fee_type = db.relationship("FeeType")
    session = db.relationship("AcademicSession")
    discounts = db.relationship("FeeDiscount", back_populates="student_fee", cascade="all, delete-orphan")
    payments = db.relationship("FeePayment", back_populates="student_fee", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<StudentFee student={self.student_id} type={self.fee_type_id} amount={self.amount}>"
