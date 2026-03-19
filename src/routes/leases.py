from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from routes import role_required, get_active_role
from models import db
from models.lease import Lease
from models.store_unit import StoreUnit
from models.user import User
from services.lease_service import sign_lease, generate_lease_pdf
from datetime import datetime

leases_bp = Blueprint('leases', __name__, url_prefix='/leases')


@leases_bp.route('/')
@login_required
def list_leases():
    if get_active_role() == 'Tenant':
        leases = Lease.query.filter_by(tenant_id=current_user.user_id).all()
    else:
        leases = Lease.query.all()

    return render_template('leases/list.html', leases=leases)


@leases_bp.route('/<int:lease_id>')
@login_required
def detail(lease_id):
    lease = Lease.query.get_or_404(lease_id)
    return render_template('leases/detail.html', lease=lease)


@leases_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin', 'LeasingAgent')
def create():
    if request.method == 'POST':
        lease = Lease(
            tenant_id=int(request.form['tenant_id']),
            unit_id=int(request.form['unit_id']),
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d').date(),
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d').date(),
            payment_cycle=request.form['payment_cycle'],
            auto_renew=bool(request.form.get('auto_renew')),
            renewal_rate_increase=float(request.form['renewal_rate_increase']) if request.form.get('renewal_rate_increase') else None
        )
        db.session.add(lease)

        # Mark unit as occupied
        unit = StoreUnit.query.get(int(request.form['unit_id']))
        unit.availability = 'Occupied'

        db.session.commit()
        flash('Lease created successfully.', 'success')
        return redirect(url_for('leases.detail', lease_id=lease.lease_id))

    tenants = User.query.filter(User.role.in_(['Tenant', 'Dev']), User.status == 'Active').all()
    units = StoreUnit.query.filter_by(availability='Available').all()
    return render_template('leases/form.html', tenants=tenants, units=units)


@leases_bp.route('/<int:lease_id>/sign', methods=['GET', 'POST'])
@login_required
@role_required('Tenant', 'LeasingAgent')
def sign(lease_id):
    lease = Lease.query.get_or_404(lease_id)

    if request.method == 'POST':
        signature = request.form.get('signature')
        if signature:
            sign_lease(lease, current_user, signature)
            flash('Lease signed successfully.', 'success')
            return redirect(url_for('leases.detail', lease_id=lease.lease_id))

    return render_template('leases/sign.html', lease=lease)


@leases_bp.route('/<int:lease_id>/download-agreement')
@login_required
def download_agreement(lease_id):
    lease = Lease.query.get_or_404(lease_id)

    if get_active_role() == 'Tenant' and lease.tenant_id != current_user.user_id:
        flash('You are not authorized to download this agreement.', 'danger')
        return redirect(url_for('leases.list_leases'))

    pdf_buffer = generate_lease_pdf(lease)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'lease_agreement_{lease.lease_id}.pdf'
    )


@leases_bp.route('/<int:lease_id>/terminate', methods=['POST'])
@login_required
@role_required('Admin', 'LeasingAgent')
def terminate(lease_id):
    lease = Lease.query.get_or_404(lease_id)

    if lease.status not in ('Active', 'Pending'):
        flash('Only active or pending leases can be terminated.', 'warning')
        return redirect(url_for('leases.detail', lease_id=lease_id))

    lease.status = 'Terminated'

    # Mark unit as available again
    unit = StoreUnit.query.get(lease.unit_id)
    # Only set Available if no other active lease exists on this unit
    other_active = Lease.query.filter(
        Lease.unit_id == lease.unit_id,
        Lease.lease_id != lease.lease_id,
        Lease.status == 'Active'
    ).count()
    if other_active == 0:
        unit.availability = 'Available'

    db.session.commit()
    flash('Lease terminated successfully.', 'success')
    return redirect(url_for('leases.detail', lease_id=lease_id))
