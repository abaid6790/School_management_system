from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, BooleanField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError

from app.models.enums import PaymentMethod, DiscountType


class FeeTypeForm(FlaskForm):
    name = StringField("Fee Type Name", validators=[DataRequired(), Length(max=100)],
                        render_kw={"placeholder": "e.g. Tuition Fee"})
    default_amount = DecimalField("Default Amount", places=2, validators=[Optional(), NumberRange(min=0)])
    is_recurring = BooleanField("Recurring (e.g. monthly)")
    submit = SubmitField("Save Fee Type")


class AssignFeeForm(FlaskForm):
    fee_type_id = SelectField("Fee Type", coerce=int, validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    due_date = DateField("Due Date", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Assign Fee")


class BulkAssignFeeForm(FlaskForm):
    fee_type_id = SelectField("Fee Type", coerce=int, validators=[DataRequired()])
    class_id = SelectField("Class", coerce=int, validators=[DataRequired()])
    amount = DecimalField("Amount", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    due_date = DateField("Due Date", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Assign to Class")


class PaymentForm(FlaskForm):
    amount = DecimalField("Amount", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField(
        "Payment Method", choices=[(m.value, m.value.replace("_", " ").title()) for m in PaymentMethod],
        validators=[DataRequired()],
    )
    payment_date = DateField("Payment Date", validators=[DataRequired()])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Record Payment")


class DiscountForm(FlaskForm):
    discount_type = SelectField(
        "Discount Type", choices=[(t.value, t.value.replace("_", " ").title()) for t in DiscountType],
        validators=[DataRequired()],
    )
    value = DecimalField("Value", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    reason = TextAreaField("Reason", validators=[DataRequired(), Length(max=500)],
                            render_kw={"placeholder": "Required — e.g. 'Sibling discount', 'Financial hardship'"})
    submit = SubmitField("Apply Discount")

    def validate_value(self, field):
        if self.discount_type.data == "percentage" and field.data > 100:
            raise ValidationError("Percentage cannot exceed 100.")
