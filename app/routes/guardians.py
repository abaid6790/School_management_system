from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from app.extensions import db
from app.models import Guardian
from app.models.enums import UserRole
from app.forms.guardian import GuardianForm
from app.utils.decorators import role_required
from app.utils.tenant import current_school_id
from app.services.audit_service import log_action

guardians_bp = Blueprint("guardians", __name__, url_prefix="/guardians")

PER_PAGE = 20


@guardians_bp.route("/")
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def list_guardians():
    school_id = current_school_id()
    q = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)

    query = Guardian.query.filter_by(school_id=school_id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Guardian.father_name.ilike(like), Guardian.mother_name.ilike(like),
                   Guardian.phone.ilike(like), Guardian.alternate_phone.ilike(like))
        )
    pagination = query.order_by(Guardian.father_name).paginate(page=page, per_page=PER_PAGE, error_out=False)
    return render_template("guardians/list.html", pagination=pagination, guardians=pagination.items, q=q)


@guardians_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def new_guardian():
    form = GuardianForm()
    if form.validate_on_submit():
        guardian = Guardian(
            school_id=current_school_id(),
            father_name=form.father_name.data or None,
            mother_name=form.mother_name.data or None,
            phone=form.phone.data.strip(),
            alternate_phone=form.alternate_phone.data or None,
            email=form.email.data or None,
            occupation=form.occupation.data or None,
            address=form.address.data or None,
            emergency_contact_name=form.emergency_contact_name.data or None,
            emergency_contact_phone=form.emergency_contact_phone.data or None,
        )
        db.session.add(guardian)
        db.session.flush()
        log_action("guardian.created", "guardians", guardian.id, new_value={"phone": guardian.phone})
        db.session.commit()
        flash("Guardian added.", "success")
        return redirect(url_for("guardians.view_guardian", guardian_id=guardian.id))
    return render_template("guardians/form.html", form=form, title="New Guardian")


@guardians_bp.route("/<int:guardian_id>")
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def view_guardian(guardian_id):
    guardian = Guardian.query.filter_by(id=guardian_id, school_id=current_school_id()).first_or_404()
    return render_template("guardians/view.html", guardian=guardian)


@guardians_bp.route("/<int:guardian_id>/edit", methods=["GET", "POST"])
@login_required
@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def edit_guardian(guardian_id):
    guardian = Guardian.query.filter_by(id=guardian_id, school_id=current_school_id()).first_or_404()
    form = GuardianForm()

    if request.method == "GET":
        form.father_name.data = guardian.father_name
        form.mother_name.data = guardian.mother_name
        form.phone.data = guardian.phone
        form.alternate_phone.data = guardian.alternate_phone
        form.email.data = guardian.email
        form.occupation.data = guardian.occupation
        form.address.data = guardian.address
        form.emergency_contact_name.data = guardian.emergency_contact_name
        form.emergency_contact_phone.data = guardian.emergency_contact_phone

    if form.validate_on_submit():
        old_value = {"phone": guardian.phone}
        guardian.father_name = form.father_name.data or None
        guardian.mother_name = form.mother_name.data or None
        guardian.phone = form.phone.data.strip()
        guardian.alternate_phone = form.alternate_phone.data or None
        guardian.email = form.email.data or None
        guardian.occupation = form.occupation.data or None
        guardian.address = form.address.data or None
        guardian.emergency_contact_name = form.emergency_contact_name.data or None
        guardian.emergency_contact_phone = form.emergency_contact_phone.data or None
        log_action("guardian.edited", "guardians", guardian.id, old_value=old_value, new_value={"phone": guardian.phone})
        db.session.commit()
        flash("Guardian updated.", "success")
        return redirect(url_for("guardians.view_guardian", guardian_id=guardian.id))

    return render_template("guardians/form.html", form=form, title="Edit Guardian")
