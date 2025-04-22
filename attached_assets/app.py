import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
from flask_babel import Babel

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
babel = Babel()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "smartcafe-dev-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///smartcafe.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Configure the login manager
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

# Configure Flask-Babel
app.config["BABEL_DEFAULT_LOCALE"] = "en"
app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"

# Initialize SQLAlchemy
db.init_app(app)

# Create all tables in the database
with app.app_context():
    # Import models here to avoid circular imports
    from models import User, Meal, MealLog, UserProfile  # noqa: F401
    db.create_all()

# Import user loader for Flask-Login
from models import User  # noqa: F401

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Configure language selection
from flask import request, session

# Configure language selection function
def get_locale():
    # If a user is logged in and has a language preference, use it
    if 'language' in session:
        return session['language']
    # Otherwise, try to detect the language from the browser
    return request.accept_languages.best_match(['en', 'hi', 'kn', 'ta', 'te', 'mr', 'gu'])

# Register the locale selector function with babel
babel.init_app(app, locale_selector=get_locale)
