import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_babel import Babel
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set up database base class
class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
babel = Babel()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-key-for-testing")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure Flask-Login
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Configure Flask-Babel
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'es', 'hi', 'kn', 'ta', 'te', 'mr', 'gu']
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

# Define a simpler version for locale selection
def get_locale():
    return 'en'  # Default to English for now

babel.init_app(app, locale_selector=get_locale)

# Use ProxyFix middleware (needed for url_for to generate with https)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Initialize extensions with the app
db.init_app(app)
login_manager.init_app(app)
# babel.init_app is already called above with the locale_selector

# Import routes at the end to avoid circular imports
with app.app_context():
    import routes  # noqa: F401
    
    # Create database tables if they don't exist
    db.create_all()