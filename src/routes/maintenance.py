from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from routes import role_required
from models import db
from models.maintenance_request import MaintenanceRequest
from models.lease import Lease
from services.invoice_service import recalculate_invoice_total
from services.notification_service import create_notification

maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


@maintenance_bp.route('/')
@login_required
def list_requests():
    if current_user.role == 'Tenant':
        requests = MaintenanceRequest.query.join(Lease).filter(
            Lease.tenant_id == current_user.user_id
        ).order_by(MaintenanceRequest.created_at.desc()).all()
    else:
        requests = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).all()

    return render_template('maintenance/list.html', requests=requests)


@maintenance_bp.route('/submit', methods=['GET', 'POST'])
@login_required
@role_required('Tenant')
def submit():
    if request.method == 'POST':
        maint_request = MaintenanceRequest(
            lease_id=int(request.form['lease_id']),
            category=request.form['category'],
            description=request.form.get('description'),
            priority=request.form.get('priority', 'Medium')
        )
        db.session.add(maint_request)
        db.session.commit()
        flash('Maintenance request submitted.', 'success')
        return redirect(url_for('maintenance.list_requests'))

    leases = Lease.query.filter_by(tenant_id=current_user.user_id, status='Active').all()
    return render_template('maintenance/submit.html', leases=leases)


@maintenance_bp.route('/<int:request_id>/update', methods=['POST'])
@login_required
@role_required('Admin', 'LeasingAgent')
def update_status(request_id):
    maint_request = MaintenanceRequest.query.get_or_404(request_id)
    new_status = request.form['status']
    maint_request.status = new_status

    if request.form.get('misuse_flag'):
        maint_request.misuse_flag = True
        maint_request.charge_amount = float(request.form.get('charge_amount', 0))

    db.session.commit()

    # Recalculate invoice total if this charge is linked to an invoice
    if maint_request.invoice_id and maint_request.invoice:
        recalculate_invoice_total(maint_request.invoice)

    # Notify tenant
    lease = Lease.query.get(maint_request.lease_id)
    create_notification(
        recipient_id=lease.tenant_id,
        notif_type='Maintenance Update',
        title=f'Maintenance {new_status}',
        message=f'Your {maint_request.category} maintenance request is now: {new_status}.',
        related_entity='maintenance_request',
        related_id=maint_request.request_id
    )

    flash('Maintenance request updated.', 'success')
    return redirect(url_for('maintenance.list_requests'))
