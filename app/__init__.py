from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Load the configuration from the config.py file
    app.config.from_object('app.config.Config')

    # Initialize the database and migration support
    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register the main Blueprint
    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app

