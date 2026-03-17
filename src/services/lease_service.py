from models import db
from datetime import datetime


def sign_lease(lease, user, signature_token):
    now = datetime.utcnow()

    if user.role == 'Tenant' and lease.tenant_id == user.user_id:
        lease.tenant_signature = signature_token
        lease.tenant_signed_at = now
    elif user.role in ('Admin', 'LeasingAgent'):
        lease.agent_signature = signature_token
        lease.agent_signed_at = now

    # Update signature status
    if lease.tenant_signature and lease.agent_signature:
        lease.signature_status = 'Fully Signed'
        lease.status = 'Active'
    elif lease.tenant_signature or lease.agent_signature:
        lease.signature_status = 'Partially Signed'

    db.session.commit()
