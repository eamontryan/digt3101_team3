from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from routes import role_required
from models import db
from models.store_unit import StoreUnit
from models.mall import Mall
from models.lease import Lease

store_units_bp = Blueprint('store_units', __name__, url_prefix='/units')


@store_units_bp.route('/')
@login_required
def list_units():
    units = StoreUnit.query.all()
    return render_template('store_units/list.html', units=units)


@store_units_bp.route('/search')
@login_required
def search():
    filters = request.args
    query = StoreUnit.query

    if filters.get('mall_id'):
        query = query.filter_by(mall_id=int(filters['mall_id']))
    if filters.get('availability'):
        query = query.filter_by(availability=filters['availability'])
    if filters.get('min_size'):
        query = query.filter(StoreUnit.size >= float(filters['min_size']))
    if filters.get('max_rate'):
        query = query.filter(StoreUnit.rental_rate <= float(filters['max_rate']))
    if filters.get('classification_tier'):
        query = query.filter_by(classification_tier=filters['classification_tier'])
    if filters.get('business_purpose'):
        query = query.filter(StoreUnit.business_purpose.ilike(f"%{filters['business_purpose']}%"))

    units = query.all()
    malls = Mall.query.all()
    return render_template('store_units/search.html', units=units, malls=malls, filters=filters)


@store_units_bp.route('/<int:unit_id>')
@login_required
def detail(unit_id):
    unit = StoreUnit.query.get_or_404(unit_id)
    return render_template('store_units/detail.html', unit=unit)


@store_units_bp.route('/create', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def create():
    malls = Mall.query.all()
    if request.method == 'POST':
        try:
            unit = StoreUnit(
                mall_id=int(request.form['mall_id']),
                location=request.form['location'],
                size=float(request.form['size']),
                rental_rate=float(request.form['rental_rate']),
                classification_tier=request.form.get('classification_tier'),
                business_purpose=request.form.get('business_purpose'),
                availability=request.form.get('availability', 'Available'),
                contact_info=request.form.get('contact_info')
            )
            db.session.add(unit)
            db.session.commit()
            flash('Store unit created successfully.', 'success')
            return redirect(url_for('store_units.detail', unit_id=unit.unit_id))
        except Exception:
            db.session.rollback()
            flash('An error occurred while creating the store unit.', 'danger')

    return render_template('store_units/form.html', malls=malls, unit=None)


@store_units_bp.route('/<int:unit_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit(unit_id):
    unit = StoreUnit.query.get_or_404(unit_id)
    malls = Mall.query.all()

    if request.method == 'POST':
        try:
            unit.mall_id = int(request.form['mall_id'])
            unit.location = request.form['location']
            unit.size = float(request.form['size'])
            unit.rental_rate = float(request.form['rental_rate'])
            unit.classification_tier = request.form.get('classification_tier')
            unit.business_purpose = request.form.get('business_purpose')
            unit.availability = request.form['availability']
            unit.contact_info = request.form.get('contact_info')
            db.session.commit()
            flash('Store unit updated successfully.', 'success')
            return redirect(url_for('store_units.detail', unit_id=unit.unit_id))
        except Exception:
            db.session.rollback()
            flash('An error occurred while updating the store unit.', 'danger')

    return render_template('store_units/form.html', malls=malls, unit=unit)


@store_units_bp.route('/<int:unit_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete(unit_id):
    unit = StoreUnit.query.get_or_404(unit_id)

    blocking_leases = Lease.query.filter(
        Lease.unit_id == unit_id,
        Lease.status.in_(['Active', 'Pending'])
    ).count()
    if blocking_leases > 0:
        flash('Cannot delete unit: it has active or pending leases. Terminate them first.', 'danger')
        return redirect(url_for('store_units.detail', unit_id=unit_id))

    try:
        db.session.delete(unit)
        db.session.commit()
        flash('Store unit deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while deleting the store unit.', 'danger')
    return redirect(url_for('store_units.list_units'))