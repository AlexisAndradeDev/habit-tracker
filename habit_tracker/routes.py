from datetime import date
from flask import Blueprint, request, redirect, url_for
from flask.templating import render_template
from habit_tracker.forms import CreateHabitForm, ModifyAchievedForm, ModifyForm, DeleteHabitForm
from habit_tracker.models import Habit, HabitHistory
from habit_tracker import db

main = Blueprint("main", __name__)

def local_datetime_is_today(local_datetime):
    return True if (
        local_datetime.year == date.today().year and 
        local_datetime.month == date.today().month and 
        local_datetime.day == date.today().day
        ) else False

def get_weekdays_from_weekdays_selector(checkboxes_template_name):
    """
    Gets the selected weekdays from a weekdays_selector.

    Args:
        checkboxes_template_name (str): Template name of the weekdays_selector 
            checkboxes.

            The string has to include a substring '$%day%$', which
            will be replaced with the letter of the day ('M', 'F', 'X', ...).

            For example: 'weekday-$&day&$-habit-reading'.

                The names of the checkboxes would be:

                weekday-M-habit-reading

                weekday-T-habit-reading

                ...

            These names have to match the HTML name attributes of the checkboxes.
    Returns:
        days_selected: String that contains the days selected in the 
            weekdays_selector.
            
            It has the format 'MTWXFSD', each letter represents a weekday.
            
            For example: 'MTXF' means Monday, Tuesday, Thursday and Friday 
            are selected.
    """    
    days = {"M": None, "T": None, "W": None, "X": None, "F": None, 
        "S": None, "D": None,
    }
    for day in days:
        checkbox_name = checkboxes_template_name.replace("$&day&$", day)
        print(checkbox_name)
        days[day] = request.form.get(checkbox_name)

    days_selected = "" #MTWXFSD
    for day, selected in days.items():
        if selected:
            days_selected = days_selected + day
    return days_selected


@main.route("/", methods=["GET", "POST"])
def habits_page():
    create_habit_form = CreateHabitForm()
    modify_form = ModifyForm()
    modify_achieved_form = ModifyAchievedForm()
    delete_habit_form = DeleteHabitForm()

    if (request.method == "POST" and 
            request.form.get("action") in ["modify-achieved", "modify"]):
        action = request.form.get("action")
        habit_name = request.form.get("modified_habit")
        habit = Habit.query.filter_by(name=habit_name).first()

        last_record = habit.history[-1]
        last_record_date_is_today = local_datetime_is_today(last_record.local_timezone_date)

        # get habit's today's 'achieved' value and today's record
        if last_record_date_is_today:
            habit_record = last_record
            achieved_today = habit_record.achieved
        else:
            habit_record = HabitHistory(name=habit.name, goal=habit.goal, 
                units=habit.units, achieved=0, habit_obj_id=habit.id
            )
            achieved_today = 0

        if action == "modify-achieved":
            achieved_today = request.form.get("modify-achieved")
            achieved_today = int(achieved_today) if achieved_today else 0

        elif action == "modify":
            goal = request.form.get("goal")
            goal = int(goal) if goal else 0
            units = request.form.get("units")

            weekdays_selected = get_weekdays_from_weekdays_selector(f"weekday-$&day&$-habit-{habit.name}")
            
            habit.goal = goal
            habit.units = units
            habit.days_of_the_week = weekdays_selected

        # Update habit history

        # update today's record
        habit_record.name = habit.name
        habit_record.goal = habit.goal
        habit_record.units = habit.units
        habit_record.achieved = achieved_today

        if not last_record_date_is_today:
            # add today's record to database
            db.session.add(habit_record)

        db.session.commit()

        return redirect(url_for("main.habits_page"))
    
    elif (request.method == "POST" and 
            request.form.get("action") == "create-habit" and
            create_habit_form.validate_on_submit()):
        habit_name = create_habit_form.name.data
        units = create_habit_form.units.data
        goal = create_habit_form.goal.data

        weekdays_selected = get_weekdays_from_weekdays_selector(f"weekday-$&day&$-habit-new")

        habit = Habit(name=habit_name, units=units, goal=goal, 
            days_of_the_week=weekdays_selected)
        habit.create()

        return redirect(url_for("main.habits_page"))

    elif (request.method == "POST" and
            request.form.get("action") == "delete-habit"):
        habit_name = request.form.get("deleted_habit")
        habit = Habit.query.filter_by(name=habit_name).first()
        db.session.delete(habit)
        db.session.commit()
        return redirect(url_for("main.habits_page"))

    if request.method == "GET":
        habits = Habit.query.all()
        return render_template("habits.html", habits=habits, 
            create_habit_form=create_habit_form, modify_form=modify_form, 
            modify_achieved_form=modify_achieved_form, 
            delete_habit_form=delete_habit_form, date=date, 
            local_datetime_is_today=local_datetime_is_today,
        )

@main.route("/history")
def history_page():
    if request.method == "GET":
        habits_history = HabitHistory.query.all()
        return render_template("history.html", habits_history=habits_history)
