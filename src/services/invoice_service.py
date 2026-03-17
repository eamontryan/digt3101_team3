from decimal import Decimal
from models import db
from models.invoice import Invoice
from models.utility_usage import UtilityUsage
from models.maintenance_request import MaintenanceRequest
from models.lease import Lease
from datetime import date

CYCLE_MULTIPLIERS = {
    'Monthly': 1,
    'Quarterly': 3,
    'Semi-Annual': 6,
    'Annual': 12,
}


def generate_invoice(lease_id, issue_date=None, due_date=None):
    lease = Lease.query.get(lease_id)
    if not lease:
        return None

    if issue_date is None:
        issue_date = date.today()
    if due_date is None:
        due_date = date(issue_date.year, issue_date.month, 15)

    multiplier = CYCLE_MULTIPLIERS.get(lease.payment_cycle, 1)
    rent_amount = lease.unit.rental_rate * multiplier

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

    db.session.commit()
    return invoice


def recalculate_invoice_total(invoice):
    """Recalculate an invoice's total_amount from rent + utilities + misuse charges."""
    multiplier = CYCLE_MULTIPLIERS.get(invoice.lease.payment_cycle, 1)
    rent = invoice.lease.unit.rental_rate * multiplier
    utility_total = sum((u.amount for u in invoice.utility_usages), Decimal('0'))
    misuse_total = sum(
        (m.charge_amount for m in invoice.maintenance_charges if m.misuse_flag and m.charge_amount),
        Decimal('0')
    )
    invoice.total_amount = rent + utility_total + misuse_total
    db.session.commit()
