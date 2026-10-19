from datetime import date

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.models.enums import UserRole
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.financial_report_service import compute_financial_summary

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/financial-summary")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def financial_summary():
    school_id = current_school_id()
    today = date.today()
    try:
        start_date = date.fromisoformat(request.args.get("start_date") or today.replace(day=1).isoformat())
        end_date = date.fromisoformat(request.args.get("end_date") or today.isoformat())
    except ValueError:
        start_date, end_date = today.replace(day=1), today
    summary = compute_financial_summary(school_id, start_date, end_date)
    return render_template("reports/financial_summary.html", summary=summary, start_date=start_date, end_date=end_date)
