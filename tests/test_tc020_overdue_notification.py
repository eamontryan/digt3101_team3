"""
TC-020: Notification of Overdue Payments
FR17: Track payments and send notifications for overdue payments.

Preconditions: A tenant has an overdue payment.
Steps: System checks overdue payments → sends notification.
Expected: Tenant receives overdue payment notification.
"""
from decimal import Decimal
from models import db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.lease import Lease
from models.invoice import Invoice
from models.notification import Notification
from services.notification_service import create_notification
from datetime import date


def test_overdue_notification_created(app, seed_users):
    """TC-020: An overdue invoice triggers a Payment Overdue notification."""
    with app.app_context():
        mall = Mall(name='Overdue Mall', location='Overdue City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Overdue-Unit', size=100,
            rental_rate=Decimal('5000.00'), availability='Occupied'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()

        lease = Lease(
            tenant_id=tenant.user_id, unit_id=unit.unit_id,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
            payment_cycle='Monthly', status='Active'
        )
        db.session.add(lease)
        db.session.commit()

        # Create an overdue invoice
        invoice = Invoice(
            lease_id=lease.lease_id,
            issue_date=date(2026, 2, 1),
            due_date=date(2026, 3, 1),
            total_amount=Decimal('5000.00'),
            status='Overdue'
        )
        db.session.add(invoice)
        db.session.commit()

        # Simulate the system creating an overdue notification
        notification = create_notification(
            recipient_id=tenant.user_id,
            notif_type='Payment Overdue',
            title='Payment Overdue Notice',
            message=f'Your invoice #{invoice.invoice_id} is overdue. Outstanding: $5,000.00.',
            related_entity='invoice',
            related_id=invoice.invoice_id
        )

        assert notification is not None
        assert notification.type == 'Payment Overdue'
        assert str(invoice.invoice_id) in notification.message

        # Verify it's persisted
        saved = Notification.query.filter_by(
            recipient_id=tenant.user_id,
            type='Payment Overdue'
        ).first()
        assert saved is not None
