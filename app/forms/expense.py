from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

from app.models.enums import PaymentMethod


class ExpenseCategoryForm(FlaskForm):
    name = StringField("Category Name", validators=[DataRequired(), Length(max=100)],
                        render_kw={"placeholder": "e.g. Electricity, Maintenance"})
    submit = SubmitField("Save Category")


class ExpenseForm(FlaskForm):
    category_id = SelectField("Category", coerce=int, validators=[DataRequired()])
    description = StringField("Description", validators=[DataRequired(), Length(max=255)])
    amount = DecimalField("Amount", places=2, validators=[DataRequired(), NumberRange(min=0.01)])
    expense_date = DateField("Expense Date", validators=[DataRequired()])
    payment_method = SelectField(
        "Payment Method", choices=[(m.value, m.value.replace("_", " ").title()) for m in PaymentMethod],
        validators=[DataRequired()],
    )
    vendor = StringField("Vendor", validators=[Optional(), Length(max=150)])
    notes = TextAreaField("Notes", validators=[Optional(), Length(max=500)])
    submit = SubmitField("Save Expense")
