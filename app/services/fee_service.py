"""
Same "never store what can be derived" principle as attendance stats and exam
results: discount_total, net_amount, paid_total, remaining, and status are
always computed here from FeeDiscount/FeePayment rows, so a fee's displayed
balance can never silently disagree with its actual discount/payment history.
"""
from datetime import date

from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models import FeePayment, StudentFee, Student
from app.models.enums import FeeStatus


def compute_fee_totals(student_fee) -> dict:
    discount_total = sum((d.computed_amount for d in student_fee.discounts), start=0)
    net_amount = student_fee.amount - discount_total
    paid_total = sum((p.amount for p in student_fee.payments), start=0)
    remaining = net_amount - paid_total

    if remaining <= 0:
        status = FeeStatus.PAID
    elif paid_total > 0:
        status = FeeStatus.PARTIALLY_PAID
    else:
        status = FeeStatus.UNPAID

    is_overdue = remaining > 0 and student_fee.due_date < date.today()
    if is_overdue:
        status = FeeStatus.OVERDUE  # headline status; the underlying paid/partial state is still shown alongside it

    return {
        "amount": student_fee.amount,
        "discount_total": discount_total,
        "net_amount": net_amount,
        "paid_total": paid_total,
        "remaining": remaining,
        "status": status,
        "is_overdue": is_overdue,
    }


def generate_receipt_number(school_id: int) -> str:
    """A starting suggestion, not a hard guarantee — the real uniqueness
    guard is FeePayment's DB unique constraint on (school_id, receipt_number),
    same pattern as admission-number suggestion."""
    year = date.today().year
    count = FeePayment.query.filter_by(school_id=school_id).count()
    return f"RCPT-{year}-{count + 1:05d}"


def compute_defaulters(school_id: int, class_id: int | None = None, section_id: int | None = None) -> list[dict]:
    """One student can have several outstanding fees; this aggregates them
    per student. Deliberately reuses compute_fee_totals per fee (rather than
    a single hand-written SQL aggregate like the low-attendance report) so
    this can never silently disagree with the balance shown on the student's
    own fee page — correctness over raw query efficiency. Fine at the scale
    a school's fee volume actually reaches; worth revisiting with a grouped
    SQL query if a school's fee history grows into the hundreds of thousands
    of rows."""
    query = (
        StudentFee.query.filter_by(school_id=school_id)
        .join(Student)
        .options(joinedload(StudentFee.discounts), joinedload(StudentFee.payments),
                 joinedload(StudentFee.student), joinedload(StudentFee.fee_type))
    )
    if class_id:
        query = query.filter(Student.current_class_id == class_id)
    if section_id:
        query = query.filter(Student.current_section_id == section_id)

    by_student = {}
    for fee in query.all():
        totals = compute_fee_totals(fee)
        if totals["remaining"] <= 0:
            continue
        entry = by_student.setdefault(fee.student_id, {
            "student": fee.student, "total_net": 0, "total_paid": 0, "total_remaining": 0,
            "earliest_due_date": fee.due_date, "fees": [],
        })
        entry["total_net"] += totals["net_amount"]
        entry["total_paid"] += totals["paid_total"]
        entry["total_remaining"] += totals["remaining"]
        entry["earliest_due_date"] = min(entry["earliest_due_date"], fee.due_date)
        entry["fees"].append({"fee": fee, "totals": totals})

    results = list(by_student.values())
    for r in results:
        r["days_overdue"] = max((date.today() - r["earliest_due_date"]).days, 0)
    results.sort(key=lambda r: r["total_remaining"], reverse=True)
    return results
