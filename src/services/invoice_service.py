from decimal import Decimal
from dateutil.relativedelta import relativedelta
from models import db
from models.invoice import Invoice
from models.utility_usage import UtilityUsage
from models.maintenance_request import MaintenanceRequest
from models.lease import Lease
from services.discount_service import get_active_discount
from datetime import date

CYCLE_MULTIPLIERS = {
    'Monthly': 1,
    'Quarterly': 3,
    'Semi-Annual': 6,
    'Annual': 12,
}

CYCLE_MONTHS = CYCLE_MULTIPLIERS  # months between invoices per cycle


def generate_invoice(lease_id, issue_date=None, due_date=None):
    lease = Lease.query.get(lease_id)
    if not lease:
        return None

    if issue_date is None:
        issue_date = date.today()
    if due_date is None:
        due_date = issue_date + relativedelta(months=1)

    multiplier = CYCLE_MULTIPLIERS.get(lease.payment_cycle, 1)
    rent_amount = lease.unit.rental_rate * multiplier

    # Apply multi-unit discount to rent if applicable
    discount_pct = get_active_discount(lease.tenant_id)
    if discount_pct:
        discount_amount = rent_amount * discount_pct / Decimal('100')
        rent_amount = rent_amount - discount_amount

    # Link any un-invoiced utility usage for this unit
    usages = UtilityUsage.query.filter_by(
        unit_id=lease.unit_id,
        invoice_id=None
    ).all()
    utility_total = sum((u.amount for u in usages), Decimal('0'))

    # Link any un-invoiced misuse charges for this lease
    misuse_requests = MaintenanceRequest.query.filter_by(
        lease_id=lease_id,
        invoice_id=None,
        misuse_flag=True
    ).filter(MaintenanceRequest.charge_amount.isnot(None)).all()
    misuse_total = sum((m.charge_amount for m in misuse_requests), Decimal('0'))

    total = rent_amount + utility_total + misuse_total

    invoice = Invoice(
        lease_id=lease_id,
        issue_date=issue_date,
        due_date=due_date,
        total_amount=total
    )
    db.session.add(invoice)
    db.session.flush()

    for usage in usages:
        usage.invoice_id = invoice.invoice_id

    for req in misuse_requests:
        req.invoice_id = invoice.invoice_id

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return invoice


def recalculate_invoice_total(invoice):
    """Recalculate an invoice's total_amount from rent + utilities + misuse charges."""
    multiplier = CYCLE_MULTIPLIERS.get(invoice.lease.payment_cycle, 1)
    rent = invoice.lease.unit.rental_rate * multiplier

    # Apply multi-unit discount to rent if applicable
    discount_pct = get_active_discount(invoice.lease.tenant_id)
    if discount_pct:
        discount_amount = rent * discount_pct / Decimal('100')
        rent = rent - discount_amount

    utility_total = sum((u.amount for u in invoice.utility_usages), Decimal('0'))
    misuse_total = sum(
        (m.charge_amount for m in invoice.maintenance_charges if m.misuse_flag and m.charge_amount),
        Decimal('0')
    )
    invoice.total_amount = rent + utility_total + misuse_total
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def generate_all_due_invoices():
    """Generate invoices for all active leases that are due for billing.

    For each active lease, checks the most recent invoice date and the
    payment cycle to determine if a new invoice should be generated.

    Returns a list of newly created invoices.
    """
    today = date.today()
    active_leases = Lease.query.filter_by(status='Active').all()
    generated = []

    for lease in active_leases:
        cycle_months = CYCLE_MONTHS.get(lease.payment_cycle, 1)

        # Find the most recent invoice for this lease
        last_invoice = Invoice.query.filter_by(
            lease_id=lease.lease_id
        ).order_by(Invoice.issue_date.desc()).first()

        if last_invoice:
            next_due = last_invoice.issue_date + relativedelta(months=cycle_months)
            if next_due > today:
                continue  # not yet due
            issue_date = next_due
        else:
            # No previous invoice — first invoice starts from lease start date
            issue_date = lease.start_date

        # Generate invoices for any missed periods up to today
        while issue_date <= today:
            due_date = issue_date + relativedelta(months=1)
            invoice = generate_invoice(lease.lease_id, issue_date, due_date)
            if invoice:
                generated.append(invoice)
            issue_date = issue_date + relativedelta(months=cycle_months)

    return generated


def check_overdue_invoices():
    """Mark pending invoices past due date as Overdue and notify tenants/admins."""
    from services.notification_service import create_notification
    from models.user import User

    today = date.today()
    overdue = Invoice.query.filter(
        Invoice.status == 'Pending',
        Invoice.due_date < today
    ).all()

    if not overdue:
        return

    admin_ids = [u.user_id for u in User.query.filter(
        User.role.in_(['Admin', 'Dev']),
        User.status == 'Active'
    ).all()]

    for invoice in overdue:
        invoice.status = 'Overdue'

        total_paid = sum(
            p.amount for p in invoice.payments if p.status == 'Completed'
        )
        balance = invoice.total_amount - total_paid

        create_notification(
            recipient_id=invoice.lease.tenant_id,
            notif_type='Payment Overdue',
            title='Invoice Overdue',
            message=f'Invoice #{invoice.invoice_id} for {invoice.lease.unit.location} is overdue. Balance: ${balance:,.2f}.',
            related_entity='invoice',
            related_id=invoice.invoice_id
        )

        for admin_id in admin_ids:
            create_notification(
                recipient_id=admin_id,
                notif_type='Payment Overdue',
                title='Tenant Invoice Overdue',
                message=f'Invoice #{invoice.invoice_id} for {invoice.lease.tenant.name} ({invoice.lease.unit.location}) is overdue. Balance: ${balance:,.2f}.',
                related_entity='invoice',
                related_id=invoice.invoice_id
            )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
