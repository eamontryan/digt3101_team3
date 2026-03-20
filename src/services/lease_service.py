from io import BytesIO
from models import db
from routes import get_active_role
from datetime import datetime, date, timedelta
from decimal import Decimal


def sign_lease(lease, user, signature_token):
    now = datetime.utcnow()
    role = get_active_role()

    if role == 'Tenant' and lease.tenant_id == user.user_id:
        lease.tenant_signature = signature_token
        lease.tenant_signed_at = now
    elif role == 'LeasingAgent':
        lease.agent_signature = signature_token
        lease.agent_signed_at = now

    # Update signature status
    if lease.tenant_signature and lease.agent_signature:
        lease.signature_status = 'Fully Signed'
        lease.status = 'Active'
    elif lease.tenant_signature or lease.agent_signature:
        lease.signature_status = 'Partially Signed'

    db.session.commit()


def generate_lease_pdf(lease):
    """Generate a PDF lease agreement and return it as a BytesIO buffer."""
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pw = pdf.w - pdf.l_margin - pdf.r_margin  # usable page width

    # Title
    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(pw, 12, 'LEASE AGREEMENT', ln=True, align='C')
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(pw, 8, f'Agreement #{lease.lease_id}', ln=True, align='C')
    pdf.ln(8)

    # Parties
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(pw, 8, 'Parties', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(pw, 7, f'Landlord / Mall:  {lease.unit.mall.name}', ln=True)
    pdf.cell(pw, 7, f'Address:  {lease.unit.mall.location}', ln=True)
    pdf.cell(pw, 7, f'Tenant:  {lease.tenant.name} ({lease.tenant.email})', ln=True)
    pdf.ln(5)

    # Premises
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(pw, 8, 'Premises', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(pw, 7, f'Unit:  {lease.unit.location}', ln=True)
    pdf.cell(pw, 7, f'Size:  {lease.unit.size} sqm', ln=True)
    pdf.cell(pw, 7, f'Classification:  {lease.unit.classification_tier or "N/A"}', ln=True)
    pdf.cell(pw, 7, f'Business Purpose:  {lease.unit.business_purpose or "N/A"}', ln=True)
    pdf.ln(5)

    # Lease Terms
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(pw, 8, 'Lease Terms', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(pw, 7, f'Start Date:  {lease.start_date.strftime("%B %d, %Y")}', ln=True)
    pdf.cell(pw, 7, f'End Date:  {lease.end_date.strftime("%B %d, %Y")}', ln=True)
    pdf.cell(pw, 7, f'Monthly Rental Rate:  ${lease.unit.rental_rate:,.2f}', ln=True)
    pdf.cell(pw, 7, f'Payment Cycle:  {lease.payment_cycle}', ln=True)
    pdf.ln(5)

    # Renewal Terms
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(pw, 8, 'Renewal Terms', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(pw, 7, f'Auto-Renew:  {"Yes" if lease.auto_renew else "No"}', ln=True)
    if lease.auto_renew and lease.renewal_rate_increase:
        pdf.cell(pw, 7, f'Renewal Rate Increase:  {lease.renewal_rate_increase}%', ln=True)
    pdf.ln(5)

    # Signatures
    pdf.set_font('Helvetica', 'B', 13)
    pdf.cell(pw, 8, 'Signatures', ln=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.ln(10)

    half = pw / 2
    y_before = pdf.get_y()

    # Tenant signature
    if lease.tenant_signature:
        pdf.cell(half, 7, f'{lease.tenant.name}')
        pdf.cell(half, 7, '', ln=True)
        pdf.cell(half, 7, f'Signed: {lease.tenant_signed_at.strftime("%B %d, %Y")}')
    else:
        pdf.cell(half, 7, '___________________________')
    pdf.set_xy(pdf.l_margin + half, y_before)

    # Agent signature
    if lease.agent_signature:
        pdf.cell(half, 7, 'Agent / Admin', ln=True)
        pdf.set_x(pdf.l_margin + half)
        pdf.cell(half, 7, f'Signed: {lease.agent_signed_at.strftime("%B %d, %Y")}', ln=True)
    else:
        pdf.cell(half, 7, '___________________________', ln=True)

    pdf.ln(5)
    pdf.set_x(pdf.l_margin)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(half, 6, 'Tenant Signature')
    pdf.cell(half, 6, 'Agent / Admin Signature', ln=True)

    buf = BytesIO()
    pdf_string = pdf.output(dest='S').encode('latin-1')
    buf.write(pdf_string)
    buf.seek(0)
    return buf


def process_lease_renewals():
    """Auto-renew eligible leases within 30 days of expiration."""
    from dateutil.relativedelta import relativedelta
    from models.lease import Lease
    from models.store_unit import StoreUnit
    from services.notification_service import create_notification

    today = date.today()
    threshold = today + timedelta(days=30)

    eligible = Lease.query.filter(
        Lease.auto_renew == True,
        Lease.status == 'Active',
        Lease.end_date <= threshold,
        Lease.renewal_status.in_(['Not Applicable', 'Pending Renewal'])
    ).all()

    for lease in eligible:
        duration = relativedelta(lease.end_date, lease.start_date)
        new_start = lease.end_date + timedelta(days=1)
        new_end = new_start + duration

        # Basic renewal logic logic (e.g., 5% increase for standard)
        increase_rate = Decimal('1.05')
        # Apply rate increase to the unit
        if lease.renewal_rate_increase:
            unit = StoreUnit.query.get(lease.unit_id)
            increase_pct = Decimal(str(lease.renewal_rate_increase)) / Decimal('100')
            unit.rental_rate = unit.rental_rate * (Decimal('1') + increase_pct)

        # Extend the existing lease in place
        lease.start_date = new_start
        lease.end_date = new_end
        lease.renewal_status = 'Renewed'

        create_notification(
            recipient_id=lease.tenant_id,
            notif_type='Lease Renewal',
            title='Lease Auto-Renewed',
            message=f'Your lease for {lease.unit.location} has been auto-renewed. New period: {new_start.strftime("%b %d, %Y")} to {new_end.strftime("%b %d, %Y")}.',
            related_entity='lease',
            related_id=lease.lease_id
        )

    db.session.commit()
