from datetime import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.store_unit import StoreUnit
from models.lease import Lease
from models.invoice import Invoice
from models.appointment import Appointment
from models.maintenance_request import MaintenanceRequest
from models.notification import Notification

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    if current_user.role == 'Admin':
        return admin_dashboard()
    elif current_user.role == 'LeasingAgent':
        return agent_dashboard()
    else:
        return tenant_dashboard()


def admin_dashboard():
    total_units = StoreUnit.query.count()
    available_units = StoreUnit.query.filter_by(availability='Available').count()
    active_leases = Lease.query.filter_by(status='Active').count()
    overdue_invoices = Invoice.query.filter_by(status='Overdue').count()
    open_maintenance = MaintenanceRequest.query.filter(
        MaintenanceRequest.status.in_(['Open', 'In Progress'])
    ).count()

    return render_template('dashboard/admin.html',
                           total_units=total_units,
                           available_units=available_units,
                           active_leases=active_leases,
                           overdue_invoices=overdue_invoices,
                           open_maintenance=open_maintenance)


def agent_dashboard():
    upcoming = Appointment.query.filter(
        Appointment.agent_id == current_user.user_id,
        Appointment.status == 'Scheduled',
        Appointment.date_time >= datetime.now()
    ).order_by(Appointment.date_time).limit(10).all()

    return render_template('dashboard/agent.html', upcoming_appointments=upcoming)


def tenant_dashboard():
    leases = Lease.query.filter_by(tenant_id=current_user.user_id, status='Active').all()
    pending_invoices = Invoice.query.join(Lease).filter(
        Lease.tenant_id == current_user.user_id,
        Invoice.status.in_(['Pending', 'Overdue'])
    ).all()
    notifications = Notification.query.filter_by(
        recipient_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    return render_template('dashboard/tenant.html',
                           leases=leases,
                           pending_invoices=pending_invoices,
                           notifications=notifications)
