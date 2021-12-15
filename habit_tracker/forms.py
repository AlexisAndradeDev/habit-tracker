from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, IntegerField, DateField
from wtforms.validators import Length, DataRequired
from wtforms_components import DateRange
from datetime import date

class ModifyForm(FlaskForm):
    submit = SubmitField(label="Save changes")

class ModifyAchievedForm(FlaskForm):
    submit = SubmitField(label="Save")

class CreateHabitForm(FlaskForm):
    name = StringField(label="Habit name:", validators=[Length(max=20), DataRequired()])
    units = StringField(label="Units (minutes, calories):", validators=[Length(max=15), DataRequired()])
    goal = IntegerField(label="Goal (number): ", validators=[DataRequired()])
    submit = SubmitField(label="Create")

class DeleteHabitForm(FlaskForm):
    submit = SubmitField(label="Delete")

class FilterHistoryForm(FlaskForm):
    start_date = DateField(label="Start date:", validators=[DateRange(min=date(2021, 12, 1))])
    end_date = DateField(label="End date:", validators=[DateRange(min=date(2021, 12, 1))])
    submit = SubmitField(label="Apply")