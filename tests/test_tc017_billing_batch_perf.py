"""
TC-017: Generate Monthly Bill - Processing Time
NFR1 + FR19: Consolidated billing batch performance.

Preconditions: 100 tenants with active leases.
Steps: Trigger monthly billing job. Measure runtime.
Expected: Batch billing completes within 10 seconds for 100 tenants.
"""
import time
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from services.invoice_service import generate_all_due_invoices
from conftest import _hash_pw
from datetime import date


def test_batch_billing_performance(app, seed_users):
    """TC-017: Generating invoices for 100 tenants completes in ≤ 10 seconds."""
    with app.app_context():
        mall = Mall(name='Batch Mall', location='Batch City')
        db.session.add(mall)
        db.session.commit()

        # Create 100 tenants with leases
        for i in range(100):
            tenant = User(
                username=f'batch_tenant_{i}', password=_hash_pw(),
                name=f'Batch Tenant {i}', email=f'batch_t_{i}@test.com',
                role='Tenant', status='Active',
                preferred_payment_cycle='Monthly'
            )
            db.session.add(tenant)
            db.session.flush()

            unit = StoreUnit(
                mall_id=mall.mall_id,
                location=f'Batch-Unit-{i}', size=100,
                rental_rate=Decimal('5000.00'), availability='Occupied'
            )
            db.session.add(unit)
            db.session.flush()

            lease = Lease(
                tenant_id=tenant.user_id, unit_id=unit.unit_id,
                start_date=date(2025, 1, 1), end_date=date(2026, 12, 31),
                payment_cycle='Monthly', status='Active'
            )
            db.session.add(lease)

        db.session.commit()

        start = time.time()
        generated = generate_all_due_invoices()
        elapsed = time.time() - start

        assert len(generated) > 0, 'Expected at least some invoices to be generated'
        assert elapsed <= 10.0, f'Batch billing took {elapsed:.2f}s, expected ≤ 10s'
