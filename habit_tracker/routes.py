from datetime import date
import datetime
import pytz
from dateutil import tz
from flask import Blueprint, request, redirect, url_for, flash
from flask.templating import render_template
from habit_tracker.forms import (CreateHabitForm, ModifyAchievedForm, 
    ModifyForm, DeleteHabitForm, FilterHistoryForm)
from habit_tracker.models import Habit, HabitHistory
from habit_tracker import db
from sqlalchemy import func

main = Blueprint("main", __name__)

def local_datetime_is_today(local_datetime):
    return True if (
        local_datetime.year == date.today().year and 
        local_datetime.month == date.today().month and 
        local_datetime.day == date.today().day
        ) else False

def convert_local_date_into_utc_datetime(local_date):
    """
    Converts a local timezone date object into a UTC timezone datetime object.

    Args:
        local_date (datetime.date): Local timezone date object.

    Returns:
        datetime_utc (datetime.datetime): UTC timezone datetime object.
    """
    local_datetime = datetime.datetime.combine(
        local_date, datetime.datetime.min.time(), tz.tzlocal()
    )
    datetime_utc = datetime.datetime.astimezone(local_datetime, pytz.utc)
    return datetime_utc

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
        days_selected (str): String that contains the days selected in the 
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
        last_record_date_is_today = local_datetime_is_today(
            last_record.local_timezone_date
        )

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

            weekdays_selected = get_weekdays_from_weekdays_selector(
                f"weekday-$&day&$-habit-{habit.name}"
            )

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

        weekdays_selected = get_weekdays_from_weekdays_selector(
            f"weekday-$&day&$-habit-new"
        )

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

@main.route("/history", methods=["GET", "POST"])
def history_page():
    filter_history_form = FilterHistoryForm()

    habits = Habit.query.all()
    habits_history = HabitHistory.query.all()

    achieved_sumations, percentage_achieved_averages = {}, {}
    for habit in habits:
        habit_history_query = HabitHistory.query.filter_by(name=habit.name)
        habit_history = habit_history_query.all()

        achieved_sumation = habit_history_query.with_entities(
            func.sum(HabitHistory.achieved).label("total")).first().total

        percentage_achieved_sumation = sum([habit_record.percentage_achieved for habit_record in habit_history])
        average_percentage_achieved = int(
            percentage_achieved_sumation / habit_history_query.count()
        )

        achieved_sumations[habit.name] = achieved_sumation
        percentage_achieved_averages[habit.name] = average_percentage_achieved

    if request.method == "GET":
        # no filters
        filtered_habits_history = habits_history

    if request.method == "POST":
        start_date = filter_history_form.start_date.data
        filtered_habits_history_query = db.session.query(HabitHistory)
        if start_date:
            start_date_utc = convert_local_date_into_utc_datetime(start_date)
            filtered_habits_history_query = \
                filtered_habits_history_query.filter(
                    HabitHistory.date >= start_date_utc
                )

        end_date = filter_history_form.end_date.data
        if end_date:
            end_date_utc = convert_local_date_into_utc_datetime(end_date)
            # end of the day
            end_date_utc = end_date_utc + datetime.timedelta(hours=23, 
                minutes=59, seconds=59, milliseconds=999, microseconds=999
            )
            filtered_habits_history_query = \
                filtered_habits_history_query.filter(
                    HabitHistory.date <= end_date_utc
                )
        if start_date and end_date:
            if start_date > end_date:
                flash("Start date can't be greater than end date.", category="danger")
                return redirect(url_for("main.history_page"))

        filtered_habits_history = filtered_habits_history_query.all()


    return render_template("history.html", habits=habits, filter_history_form=filter_history_form,
        filtered_habits_history=filtered_habits_history, achieved_sumations=achieved_sumations, 
        percentage_achieved_averages=percentage_achieved_averages, 
        zip=zip,)
