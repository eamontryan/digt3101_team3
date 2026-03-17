import click
from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db
from models.user import User

login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.store_units import store_units_bp
    from routes.appointments import appointments_bp
    from routes.applications import applications_bp
    from routes.leases import leases_bp
    from routes.billing import billing_bp
    from routes.utilities import utilities_bp
    from routes.maintenance import maintenance_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(store_units_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(applications_bp)
    app.register_blueprint(leases_bp)
    app.register_blueprint(billing_bp)
    app.register_blueprint(utilities_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(notifications_bp)

    @app.cli.command('generate-invoices')
    def cli_generate_invoices():
        """Generate invoices for all active leases that are due."""
        from services.invoice_service import generate_all_due_invoices
        generated = generate_all_due_invoices()
        click.echo(f'{len(generated)} invoice(s) generated.')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
