from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class ModifyForm(FlaskForm):
    submit = SubmitField(label="Save changes")

class AddToAchievedForm(FlaskForm):
    submit = SubmitField(label="Add")
