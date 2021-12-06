from datetime import date
from flask import Blueprint, request, redirect, url_for
from flask.templating import render_template
from sqlalchemy.sql.functions import func, localtime
from habit_tracker.forms import AddToAchievedForm, ModifyForm
from habit_tracker.models import Habit, HabitHistory
from habit_tracker import db

main = Blueprint("main", __name__)

def local_datetime_is_today(local_datetime):
    return True if (
        local_datetime.year == date.today().year and 
        local_datetime.month == date.today().month and 
        local_datetime.day == date.today().day
        ) else False

@main.route("/", methods=["GET", "POST"])
def habits_page():
    modify_form = ModifyForm()
    add_to_achieved_form = AddToAchievedForm()

    if request.method == "POST":
        action = request.form.get("action")
        habit_name = request.form.get("modified_habit")
        habit = Habit.query.filter_by(name=habit_name).first()

        last_record = habit.history[-1]

        # get habit's today's 'achieved' value and today's record
        if local_datetime_is_today(last_record.local_timezone_date):
            achieved_today = last_record.achieved
            habit_record = last_record
        else:
            achieved_today = 0
            habit_record = HabitHistory(name=habit.name, goal=habit.goal, 
                units=habit.units, achieved=0, habit_obj_id=habit.id
            )

        if action == "add":
            achieved_today += int(request.form.get("add-to-achieved"))

        elif action == "modify":
            goal = int(request.form.get("goal"))
            units = request.form.get("units")

            days = {"M": None, "T": None, "W": None, "X": None, "F": None, 
                "S": None, "D": None,
            }
            for day in days:
                days[day] = request.form.get(f"weekday-{day}-habit-{habit.name}")

            days_selected = "" #MTWXFSD
            for day, selected in days.items():
                if selected:
                    days_selected = days_selected + day
            
            habit.goal = goal
            habit.units = units
            habit.days_of_the_week = days_selected

        # update habit history
        if local_datetime_is_today(habit_record.local_timezone_date):
            # update today's record
            habit_record.name = habit.name
            habit_record.goal = habit.goal
            habit_record.units = habit.units
            habit_record.achieved = achieved_today
        else:
            # create today's record
            db.session.add(habit_record)

        db.session.commit()

        return redirect(url_for("main.habits_page"))
    
    if request.method == "GET":
        habits = Habit.query.all()
        return render_template("habits.html", habits=habits, 
            modify_form=modify_form, add_to_achieved_form=add_to_achieved_form,
            date=date, local_datetime_is_today=local_datetime_is_today,
        )

@main.route("/statistics")
def statistics_page():
    return render_template("statistics.html", )
