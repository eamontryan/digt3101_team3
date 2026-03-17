from models import db
from models.invoice import Invoice
from models.utility_usage import UtilityUsage
from models.lease import Lease
from datetime import date


def generate_invoice(lease_id, issue_date=None, due_date=None):
    lease = Lease.query.get(lease_id)
    if not lease:
        return None

    if issue_date is None:
        issue_date = date.today()
    if due_date is None:
        due_date = date(issue_date.year, issue_date.month, 15)

    invoice = Invoice(
        lease_id=lease_id,
        issue_date=issue_date,
        due_date=due_date,
        total_amount=0
    )
    db.session.add(invoice)
    db.session.flush()

    total = 0

    # Rent line item
    rent_amount = float(lease.unit.rental_rate)
    rent_item = InvoiceLineItem(
        invoice_id=invoice.invoice_id,
        description=f'Rent - {lease.unit.location}',
        type='Rent',
        amount=rent_amount
    )
    db.session.add(rent_item)
    total += rent_amount

    # Link any un-invoiced utility usage for this unit
    usages = UtilityUsage.query.filter_by(
        unit_id=lease.unit_id,
        invoice_id=None
    ).all()
    for usage in usages:
        line = InvoiceLineItem(
            invoice_id=invoice.invoice_id,
            description=f'{usage.type} - {usage.billing_month.strftime("%b %Y")}',
            type=usage.type,
            amount=float(usage.amount)
        )
        db.session.add(line)
        usage.invoice_id = invoice.invoice_id
        total += float(usage.amount)

    invoice.total_amount = total
    db.session.commit()
    return invoice
