from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import case
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
    # Status ordering for better display
    status_order = case(
        (MaintenanceRequest.status == 'Open', 1),
        (MaintenanceRequest.status == 'In Progress', 2),
        (MaintenanceRequest.status == 'Rejected', 3),
        (MaintenanceRequest.status == 'Resolved', 4),
        (MaintenanceRequest.status == 'Misuse', 5),
        else_=6
    )

    # Priority ordering for better display
    priority_order = case(
        (MaintenanceRequest.priority == 'Urgent', 1),
        (MaintenanceRequest.priority == 'High', 2),
        (MaintenanceRequest.priority == 'Medium', 3),
        (MaintenanceRequest.priority == 'Low', 4),
        else_=5
    )

    base_query = MaintenanceRequest.query.join(Lease)

    if current_user.role == 'Tenant':
        base_query = base_query.filter(Lease.tenant_id == current_user.user_id)

    requests = base_query.order_by(
        status_order.asc(),
        priority_order.asc(),
        MaintenanceRequest.created_at.desc()
    ).all()

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

    leases = Lease.query.filter_by(tenant_id=current_user.user_id, status='Active').order_by(Lease.start_date.desc()).all()
    return render_template('maintenance/submit.html', leases=leases)


@maintenance_bp.route('/<int:request_id>')
@login_required
def request_detail(request_id):
    maint_request = MaintenanceRequest.query.join(Lease).filter(
        MaintenanceRequest.request_id == request_id
    ).first_or_404()

    # Tenants can only view their own requests
    if current_user.role == 'Tenant' and maint_request.lease.tenant_id != current_user.user_id:
        flash('You are not authorized to view this maintenance request.', 'danger')
        return redirect(url_for('maintenance.list_requests'))

    return render_template('maintenance/detail.html', req=maint_request)


@maintenance_bp.route('/<int:request_id>/update', methods=['POST'])
@login_required
@role_required('Admin', 'LeasingAgent')
def update_status(request_id):
    maint_request = MaintenanceRequest.query.get_or_404(request_id)
    action = request.form.get('action')
    new_status = request.form.get('status')

    if action == 'misuse':
        # Only admins can mark misuse
        if current_user.role != 'Admin':
            flash('Only admins can mark a maintenance request as misuse.', 'danger')
            return redirect(url_for('maintenance.list_requests'))

        maint_request.status = 'Misuse'
        maint_request.misuse_flag = True
        maint_request.charge_amount = float(request.form.get('charge_amount', 0) or 0)
        status_for_notice = 'Misuse'
    else:
        maint_request.status = new_status
        if maint_request.status != 'Misuse':
            maint_request.misuse_flag = False
            maint_request.charge_amount = None
        status_for_notice = new_status

    db.session.commit()

    if maint_request.invoice_id and maint_request.invoice:
        recalculate_invoice_total(maint_request.invoice)

    lease = Lease.query.get(maint_request.lease_id)
    create_notification(
        recipient_id=lease.tenant_id,
        notif_type='Maintenance Update',
        title=f'Maintenance {status_for_notice}',
        message=f'Your {maint_request.category} maintenance request is now: {status_for_notice}.',
        related_entity='maintenance_request',
        related_id=maint_request.request_id
    )

    flash('Maintenance request updated.', 'success')
    return redirect(url_for('maintenance.list_requests'))