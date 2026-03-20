from decimal import Decimal
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from routes import role_required, get_active_role
from models import db
from models.invoice import Invoice
from models.payment import Payment
from models.lease import Lease
from services.invoice_service import generate_all_due_invoices
from services.discount_service import get_active_discount
from datetime import date

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')


@billing_bp.route('/generate-invoices', methods=['POST'])
@login_required
@role_required('Admin')
def generate_invoices():
    generated = generate_all_due_invoices()
    if generated:
        flash(f'{len(generated)} invoice(s) generated successfully.', 'success')
    else:
        flash('No invoices are due at this time.', 'info')
    return redirect(url_for('billing.invoices'))


@billing_bp.route('/invoices')
@login_required
def invoices():
    if get_active_role() == 'Tenant':
        invoice_list = Invoice.query.join(Lease).filter(
            Lease.tenant_id == current_user.user_id
        ).order_by(Invoice.due_date.desc()).all()
    else:
        invoice_list = Invoice.query.order_by(Invoice.due_date.desc()).all()

    return render_template('billing/invoices.html', invoices=invoice_list)


@billing_bp.route('/invoices/<int:invoice_id>/detail')
@login_required
def invoice_detail(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    # Verify tenant can only view their own invoices
    if get_active_role() == 'Tenant' and invoice.lease.tenant_id != current_user.user_id:
        return jsonify({'error': 'Unauthorized'}), 403

    cycle_multipliers = {
        'Monthly': 1,
        'Quarterly': 3,
        'Semi-Annual': 6,
        'Annual': 12,
    }
    multiplier = cycle_multipliers.get(invoice.lease.payment_cycle, 1)
    rent_amount = float(invoice.lease.unit.rental_rate) * multiplier

    utility_total = sum(float(u.amount) for u in invoice.utility_usages)
    misuse_charges = [
        m for m in invoice.maintenance_charges if m.misuse_flag and m.charge_amount
    ]
    misuse_total = sum(float(m.charge_amount) for m in misuse_charges)
    total_paid = sum(float(p.amount) for p in invoice.payments if p.status == 'Completed')

    # Only show discount if it was actually applied to this invoice's stored total.
    # Compare stored total against undiscounted total to detect whether a discount was baked in.
    undiscounted_total = rent_amount + utility_total + misuse_total
    discount_pct = 0
    discount_amount = 0
    rent_after_discount = rent_amount

    if float(invoice.total_amount) < undiscounted_total:
        active_discount = get_active_discount(invoice.lease.tenant_id)
        if active_discount:
            discount_pct = float(active_discount)
            discount_amount = rent_amount * discount_pct / 100
            rent_after_discount = rent_amount - discount_amount

    data = {
        'invoice_id': invoice.invoice_id,
        'tenant': invoice.lease.tenant.name,
        'unit': invoice.lease.unit.location,
        'issue_date': invoice.issue_date.strftime('%b %d, %Y'),
        'due_date': invoice.due_date.strftime('%b %d, %Y'),
        'status': invoice.status,
        'payment_cycle': invoice.lease.payment_cycle,
        'monthly_rate': float(invoice.lease.unit.rental_rate),
        'rent_amount': rent_after_discount,
        'discount_pct': discount_pct,
        'discount_amount': discount_amount,
        'utilities': [
            {
                'type': u.type,
                'usage_amount': float(u.usage_amount),
                'amount': float(u.amount),
            }
            for u in invoice.utility_usages
        ],
        'utility_total': utility_total,
        'maintenance_charges': [
            {
                'category': m.category,
                'description': m.description,
                'amount': float(m.charge_amount),
            }
            for m in misuse_charges
        ],
        'maintenance_total': misuse_total,
        'total_amount': float(invoice.total_amount),
        'payments': [
            {
                'payment_id': p.payment_id,
                'amount': float(p.amount),
                'date': p.payment_date.strftime('%b %d, %Y') if p.payment_date else None,
                'status': p.status,
            }
            for p in invoice.payments
        ],
        'total_paid': total_paid,
        'balance_due': float(invoice.total_amount) - total_paid,
    }

    return jsonify(data)


@billing_bp.route('/invoices/<int:invoice_id>/pay', methods=['GET', 'POST'])
@login_required
def pay(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'POST':
        amount = Decimal(request.form['amount'])
        payment = Payment(
            invoice_id=invoice_id,
            amount=amount,
            payment_date=date.today(),
            due_date=invoice.due_date,
            status='Completed'
        )
        db.session.add(payment)

        # Update invoice status
        total_paid = sum(p.amount for p in invoice.payments) + amount
        if total_paid >= invoice.total_amount:
            invoice.status = 'Paid'
        else:
            invoice.status = 'Partially Paid'

        db.session.commit()
        flash('Payment recorded successfully.', 'success')
        return redirect(url_for('billing.invoices'))

    return render_template('billing/payment.html', invoice=invoice)
