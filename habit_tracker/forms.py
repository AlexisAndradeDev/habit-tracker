from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField

class ModifyForm(FlaskForm):
    submit = SubmitField(label="Save changes")

class ModifyAchievedForm(FlaskForm):
    submit = SubmitField(label="Save")
