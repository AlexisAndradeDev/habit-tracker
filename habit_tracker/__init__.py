from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile("settings.py")

db = SQLAlchemy(app)

from .routes import main
app.register_blueprint(main)

db.create_all()
