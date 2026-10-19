from sqlalchemy import func

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app.extensions import db
from app.models import ExpenseCategory, Expense
from app.models.enums import UserRole, RecordStatus, PaymentMethod
from app.forms.expense import ExpenseCategoryForm, ExpenseForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action

expenses_bp = Blueprint("expenses", __name__, url_prefix="/expenses")

PER_PAGE = 20


@expenses_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def list_expenses():
    school_id = current_school_id()
    category_id = request.args.get("category_id", type=int)
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    page = request.args.get("page", 1, type=int)

    query = Expense.query.filter_by(school_id=school_id)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Expense.expense_date >= start_date)
    if end_date:
        query = query.filter(Expense.expense_date <= end_date)

    total_amount = query.with_entities(func.sum(Expense.amount)).scalar() or 0
    pagination = query.order_by(Expense.expense_date.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    categories = ExpenseCategory.query.filter_by(school_id=school_id).order_by(ExpenseCategory.name).all()

    return render_template(
        "expenses/list.html", pagination=pagination, expenses=pagination.items, categories=categories,
        category_id=category_id, start_date=start_date, end_date=end_date, total_amount=total_amount,
    )


@expenses_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def new_expense():
    school_id = current_school_id()
    form = ExpenseForm()
    form.category_id.choices = [
        (c.id, c.name) for c in ExpenseCategory.query.filter_by(school_id=school_id, status=RecordStatus.ACTIVE).order_by(ExpenseCategory.name)
    ]
    if not form.category_id.choices:
        flash("Create an expense category before recording expenses.", "warning")
        return redirect(url_for("expenses.category_new"))

    if form.validate_on_submit():
        expense = Expense(
            school_id=school_id, category_id=form.category_id.data, description=form.description.data.strip(),
            amount=form.amount.data, expense_date=form.expense_date.data,
            payment_method=PaymentMethod(form.payment_method.data), vendor=form.vendor.data or None,
            notes=form.notes.data or None, recorded_by_id=current_user.id,
        )
        db.session.add(expense)
        db.session.flush()
        log_action("expense.created", "expenses", expense.id,
                   new_value={"description": expense.description, "amount": str(expense.amount)})
        db.session.commit()
        flash("Expense recorded.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expenses/form.html", form=form, title="New Expense")


@expenses_bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def edit_expense(expense_id):
    school_id = current_school_id()
    expense = Expense.query.filter_by(id=expense_id, school_id=school_id).first_or_404()

    form = ExpenseForm()
    # Include inactive categories so editing an old expense doesn't break.
    form.category_id.choices = [
        (c.id, c.name) for c in ExpenseCategory.query.filter_by(school_id=school_id).order_by(ExpenseCategory.name)
    ]

    if request.method == "GET":
        form.category_id.data = expense.category_id
        form.description.data = expense.description
        form.amount.data = expense.amount
        form.expense_date.data = expense.expense_date
        form.payment_method.data = expense.payment_method.value
        form.vendor.data = expense.vendor
        form.notes.data = expense.notes

    if form.validate_on_submit():
        expense.category_id = form.category_id.data
        expense.description = form.description.data.strip()
        expense.amount = form.amount.data
        expense.expense_date = form.expense_date.data
        expense.payment_method = PaymentMethod(form.payment_method.data)
        expense.vendor = form.vendor.data or None
        expense.notes = form.notes.data or None
        log_action("expense.edited", "expenses", expense.id,
                   new_value={"description": expense.description, "amount": str(expense.amount)})
        db.session.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("expenses.list_expenses"))

    return render_template("expenses/form.html", form=form, title="Edit Expense")


@expenses_bp.route("/<int:expense_id>/delete", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, school_id=current_school_id()).first_or_404()
    log_action("expense.deleted", "expenses", expense.id,
               old_value={"description": expense.description, "amount": str(expense.amount)})
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted.", "info")
    return redirect(url_for("expenses.list_expenses"))


@expenses_bp.route("/categories")
@login_required
@role_required(UserRole.ADMIN, UserRole.ACCOUNTANT)
def category_list():
    categories = ExpenseCategory.query.filter_by(school_id=current_school_id()).order_by(ExpenseCategory.name).all()
    return render_template("expenses/category_list.html", categories=categories)


@expenses_bp.route("/categories/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def category_new():
    school_id = current_school_id()
    form = ExpenseCategoryForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        if ExpenseCategory.query.filter_by(school_id=school_id, name=name).first():
            form.name.errors.append("A category with this name already exists.")
        else:
            category = ExpenseCategory(school_id=school_id, name=name)
            db.session.add(category)
            db.session.flush()
            log_action("expense_category.created", "expense_categories", category.id, new_value={"name": category.name})
            db.session.commit()
            flash(f"Category '{category.name}' created.", "success")
            return redirect(url_for("expenses.category_list"))
    return render_template("expenses/category_form.html", form=form, title="New Expense Category")


@expenses_bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN)
def category_edit(category_id):
    school_id = current_school_id()
    category = ExpenseCategory.query.filter_by(id=category_id, school_id=school_id).first_or_404()
    form = ExpenseCategoryForm()
    if request.method == "GET":
        form.name.data = category.name
    if form.validate_on_submit():
        name = form.name.data.strip()
        conflict = ExpenseCategory.query.filter(
            ExpenseCategory.school_id == school_id, ExpenseCategory.name == name, ExpenseCategory.id != category.id
        ).first()
        if conflict:
            form.name.errors.append("A category with this name already exists.")
        else:
            category.name = name
            log_action("expense_category.edited", "expense_categories", category.id, new_value={"name": category.name})
            db.session.commit()
            flash(f"Category '{category.name}' updated.", "success")
            return redirect(url_for("expenses.category_list"))
    return render_template("expenses/category_form.html", form=form, title="Edit Expense Category")


@expenses_bp.route("/categories/<int:category_id>/toggle-status", methods=["POST"])
@login_required
@role_required(UserRole.ADMIN)
def category_toggle_status(category_id):
    category = ExpenseCategory.query.filter_by(id=category_id, school_id=current_school_id()).first_or_404()
    category.status = RecordStatus.INACTIVE if category.status == RecordStatus.ACTIVE else RecordStatus.ACTIVE
    log_action("expense_category.status_toggled", "expense_categories", category.id, new_value={"status": category.status.value})
    db.session.commit()
    flash(f"'{category.name}' is now {category.status.value}.", "success")
    return redirect(url_for("expenses.category_list"))
