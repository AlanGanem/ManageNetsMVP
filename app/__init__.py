from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# app
app = Flask(__name__)
app.config.from_object(Config)
# data base instance
db = SQLAlchemy(app)
# db version control instance
migrate = Migrate(app, db)
#flask login extension
login = LoginManager(app)
login.login_view = 'login'
from app import routes, models