from models.discount import Discount
from models.lease import Lease


def get_active_discount(tenant_id):
    active_leases = Lease.query.filter_by(tenant_id=tenant_id, status='Active').count()
    discount = Discount.query.filter_by(
        tenant_id=tenant_id,
        status='Active'
    ).order_by(Discount.discount_pct.desc()).first()

    if discount and active_leases >= 2:
        return discount
    return None
