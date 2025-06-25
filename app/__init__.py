from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager


from flask_migrate import Migrate

migrate = Migrate()


db = SQLAlchemy()
login_manager = LoginManager()

login_manager.login_view = 'main.login'




def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    from app.models import User
    from app.routes import main

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    app.register_blueprint(main)
    return app

