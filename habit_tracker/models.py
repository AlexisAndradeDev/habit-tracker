from sqlalchemy.sql.functions import func
from habit_tracker import db
from sqlalchemy import DateTime
from dateutil import tz

class Habit(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=40), unique=True, nullable=False)
    goal = db.Column(db.Integer(), unique=False, nullable=False)
    units = db.Column(db.String(length=20), unique=False, nullable=False)
    days_of_the_week = db.Column(db.String(length=7), unique=False, nullable=False) # MTWXFSD
    history = db.relationship("HabitHistory", backref="habit_obj", lazy=True)

    def create(self):
        db.session.add(self)
        db.session.commit()

        habit_record = HabitHistory(name=self.name, goal=self.goal, 
            units=self.units, achieved=0, habit_obj_id=self.id
        )
        db.session.add(habit_record)
        db.session.commit()

class HabitHistory(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(length=40), unique=False, nullable=False)
    date = db.Column(DateTime(timezone=True), server_default=func.now())
    goal = db.Column(db.Integer(), unique=False, nullable=False)
    units = db.Column(db.String(length=20), unique=False, nullable=False)
    achieved = db.Column(db.Integer(), unique=False, nullable=False)
    habit_obj_id = db.Column(db.Integer(), db.ForeignKey("habit.id"))

    # sort list of HabitHistory instances by date
    def __lt__(self, other):
        return self.date < other.date

    @property
    def local_timezone_date(self):
        local_datetime = self.date.replace(tzinfo=tz.tzutc())
        local_datetime = local_datetime.astimezone(tz.tzlocal())
        return local_datetime
