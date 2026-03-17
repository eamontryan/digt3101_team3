from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from routes import role_required
from models import db
from models.invoice import Invoice
from models.payment import Payment
from models.lease import Lease
from datetime import date

billing_bp = Blueprint('billing', __name__, url_prefix='/billing')


@billing_bp.route('/invoices')
@login_required
def invoices():
    if current_user.role == 'Tenant':
        invoice_list = Invoice.query.join(Lease).filter(
            Lease.tenant_id == current_user.user_id
        ).order_by(Invoice.due_date.desc()).all()
    else:
        invoice_list = Invoice.query.order_by(Invoice.due_date.desc()).all()

    return render_template('billing/invoices.html', invoices=invoice_list)


@billing_bp.route('/invoices/<int:invoice_id>/pay', methods=['GET', 'POST'])
@login_required
def pay(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)

    if request.method == 'POST':
        amount = float(request.form['amount'])
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
