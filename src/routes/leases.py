from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from routes import role_required
from models import db
from models.lease import Lease
from models.store_unit import StoreUnit
from models.user import User
from services.lease_service import sign_lease
from datetime import datetime

leases_bp = Blueprint('leases', __name__, url_prefix='/leases')


@leases_bp.route('/')
@login_required
def list_leases():
    if current_user.role == 'Tenant':
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

    tenants = User.query.filter_by(role='Tenant', status='Active').all()
    units = StoreUnit.query.filter_by(availability='Available').all()
    return render_template('leases/form.html', tenants=tenants, units=units)


@leases_bp.route('/<int:lease_id>/sign', methods=['GET', 'POST'])
@login_required
def sign(lease_id):
    lease = Lease.query.get_or_404(lease_id)

    if request.method == 'POST':
        signature = request.form.get('signature')
        if signature:
            sign_lease(lease, current_user, signature)
            flash('Lease signed successfully.', 'success')
            return redirect(url_for('leases.detail', lease_id=lease.lease_id))

    return render_template('leases/sign.html', lease=lease)
