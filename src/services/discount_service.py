from decimal import Decimal
from models.lease import Lease

MULTI_UNIT_DISCOUNT_PCT = Decimal('5.0')


def get_active_discount(tenant_id):
    """Return the discount percentage if tenant has more than 1 active lease, else None."""
    active_leases = Lease.query.filter_by(tenant_id=tenant_id, status='Active').count()
    if active_leases > 1:
        return MULTI_UNIT_DISCOUNT_PCT
    return None
