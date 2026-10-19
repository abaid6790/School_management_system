"""
Cash-basis: income counts fee PAYMENTS received in the range (not fees billed);
salaries count only records marked PAID with a payment_date in range.
"""
from sqlalchemy import func

from app.extensions import db
from app.models import FeePayment, Expense, ExpenseCategory, SalaryRecord
from app.models.enums import SalaryPaymentStatus
from app.services.salary_service import compute_net_salary


def compute_financial_summary(school_id: int, start_date, end_date) -> dict:
    income = (
        db.session.query(func.coalesce(func.sum(FeePayment.amount), 0))
        .filter(FeePayment.school_id == school_id,
                FeePayment.payment_date >= start_date, FeePayment.payment_date <= end_date)
        .scalar()
    )
    expenses_total = (
        db.session.query(func.coalesce(func.sum(Expense.amount), 0))
        .filter(Expense.school_id == school_id,
                Expense.expense_date >= start_date, Expense.expense_date <= end_date)
        .scalar()
    )
    paid_salaries = SalaryRecord.query.filter(
        SalaryRecord.school_id == school_id, SalaryRecord.payment_status == SalaryPaymentStatus.PAID,
        SalaryRecord.payment_date >= start_date, SalaryRecord.payment_date <= end_date,
    ).all()
    salaries_total = sum((compute_net_salary(r) for r in paid_salaries), start=0)

    expense_by_category = (
        db.session.query(ExpenseCategory.name, func.coalesce(func.sum(Expense.amount), 0))
        .join(Expense, Expense.category_id == ExpenseCategory.id)
        .filter(Expense.school_id == school_id,
                Expense.expense_date >= start_date, Expense.expense_date <= end_date)
        .group_by(ExpenseCategory.name)
        .order_by(func.sum(Expense.amount).desc())
        .all()
    )
    return {
        "income": income, "expenses_total": expenses_total, "salaries_total": salaries_total,
        "net_balance": income - expenses_total - salaries_total,
        "expense_by_category": expense_by_category, "salary_count": len(paid_salaries),
    }
