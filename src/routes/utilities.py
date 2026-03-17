from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from routes import role_required
from models import db
from models.utility_usage import UtilityUsage
from models.invoice import Invoice
from models.store_unit import StoreUnit
from services.invoice_service import recalculate_invoice_total
from datetime import datetime

utilities_bp = Blueprint('utilities', __name__, url_prefix='/utilities')


@utilities_bp.route('/')
@login_required
@role_required('Admin', 'LeasingAgent')
def list_utilities():
    usages = UtilityUsage.query.order_by(UtilityUsage.billing_month.desc()).all()
    return render_template('utilities/list.html', usages=usages)


@utilities_bp.route('/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add():
    if request.method == 'POST':
        invoice_id = request.form.get('invoice_id') or None
        usage = UtilityUsage(
            unit_id=int(request.form['unit_id']),
            invoice_id=int(invoice_id) if invoice_id else None,
            type=request.form['type'],
            usage_amount=float(request.form['usage_amount']),
            billing_month=datetime.strptime(request.form['billing_month'], '%Y-%m-%d').date(),
            amount=float(request.form['amount'])
        )
        db.session.add(usage)
        db.session.commit()

        # Recalculate invoice total if linked to an invoice
        if usage.invoice_id:
            invoice = Invoice.query.get(usage.invoice_id)
            if invoice:
                recalculate_invoice_total(invoice)

        flash('Utility usage recorded.', 'success')
        return redirect(url_for('utilities.list_utilities'))

    units = StoreUnit.query.filter_by(availability='Occupied').all()
    return render_template('utilities/add.html', units=units)
