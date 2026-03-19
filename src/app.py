import click
import datetime as _dt
from flask import Flask, session, redirect, request, url_for, flash
from flask_login import LoginManager, current_user, login_required
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db
from models.user import User

login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
_last_daily_check = None


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

    @app.before_request
    def daily_checks():
        global _last_daily_check
        today = _dt.date.today()
        if _last_daily_check == today:
            return
        _last_daily_check = today
        from services.invoice_service import check_overdue_invoices, generate_all_due_invoices
        from services.lease_service import process_lease_renewals
        check_overdue_invoices()
        process_lease_renewals()
        generate_all_due_invoices()

    @app.context_processor
    def inject_active_role():
        if current_user.is_authenticated:
            if current_user.role == 'Dev':
                active = session.get('dev_active_role', 'Admin')
                return {'active_role': active, 'is_dev': True}
            return {'active_role': current_user.role, 'is_dev': False}
        return {'active_role': None, 'is_dev': False}

    @app.route('/switch-role', methods=['POST'])
    @login_required
    def switch_role():
        if current_user.role != 'Dev':
            flash('Only Dev users can switch roles.', 'danger')
            return redirect(url_for('dashboard.index'))
        role = request.form.get('role')
        if role not in ('Admin', 'LeasingAgent', 'Tenant'):
            flash('Invalid role.', 'danger')
            return redirect(url_for('dashboard.index'))
        session['dev_active_role'] = role
        flash(f'Switched to {role} view.', 'info')
        return redirect(url_for('dashboard.index'))

    @app.cli.command('generate-invoices')
    def cli_generate_invoices():
        """Generate invoices for all active leases that are due."""
        from services.invoice_service import generate_all_due_invoices
        generated = generate_all_due_invoices()
        click.echo(f'{len(generated)} invoice(s) generated.')

    @app.cli.command('check-overdue')
    def cli_check_overdue():
        """Mark overdue invoices and send notifications."""
        from services.invoice_service import check_overdue_invoices
        check_overdue_invoices()
        click.echo('Overdue invoice check completed.')

    @app.cli.command('process-renewals')
    def cli_process_renewals():
        """Process automatic lease renewals for leases expiring within 30 days."""
        from services.lease_service import process_lease_renewals
        process_lease_renewals()
        click.echo('Lease renewal processing completed.')

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
