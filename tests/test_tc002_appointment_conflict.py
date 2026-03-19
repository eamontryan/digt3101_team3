"""
TC-002: Appointment Scheduling - Conflict Check
FR7: The system shall prevent double-booking.

Preconditions: Agent A is already booked for a specific time.
Steps: User B attempts to book Agent A for the same time → submit.
Expected: System rejects the request and displays "already booked" error.
"""
from models import db
from models.appointment import Appointment
from models.store_unit import StoreUnit
from models.mall import Mall
from conftest import login_as_tenant
from datetime import datetime


def test_appointment_double_booking_rejected(client, app, seed_users):
    """TC-002: Booking the same agent at the same time must be rejected."""
    with app.app_context():
        mall = Mall(name='Conflict Mall', location='456 Test Ave')
        db.session.add(mall)
        db.session.commit()

        unit1 = StoreUnit(
            mall_id=mall.mall_id, location='Unit-A', size=50,
            rental_rate=1000, availability='Available'
        )
        unit2 = StoreUnit(
            mall_id=mall.mall_id, location='Unit-B', size=60,
            rental_rate=1500, availability='Available'
        )
        db.session.add_all([unit1, unit2])
        db.session.commit()

        from models.user import User
        agent = User.query.filter_by(username='agent_test').first()
        tenant = User.query.filter_by(username='tenant_test').first()

        # Create an existing appointment for the agent
        existing = Appointment(
            agent_id=agent.user_id, tenant_id=tenant.user_id,
            unit_id=unit1.unit_id,
            date_time=datetime(2026, 11, 20, 14, 0),
            end_time=datetime(2026, 11, 20, 15, 0),
            status='Scheduled'
        )
        db.session.add(existing)
        db.session.commit()

        login_as_tenant(client)

        # Attempt to book the same agent at the same overlapping time
        response = client.post('/appointments/schedule', data={
            'agent_id': agent.user_id,
            'unit_id': unit2.unit_id,
            'date_time': '2026-11-20T14:00',
            'end_time': '2026-11-20T15:00',
        }, follow_redirects=True)

        html = response.data.decode()
        assert 'already booked' in html.lower() or 'already booked' in html


def test_appointment_no_conflict_succeeds(client, app, seed_users):
    """Booking a different time slot for the same agent should succeed."""
    with app.app_context():
        mall = Mall(name='OK Mall', location='789 Test Blvd')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Unit-OK', size=50,
            rental_rate=1000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()

        from models.user import User
        agent = User.query.filter_by(username='agent_test').first()
        tenant = User.query.filter_by(username='tenant_test').first()

        existing = Appointment(
            agent_id=agent.user_id, tenant_id=tenant.user_id,
            unit_id=unit.unit_id,
            date_time=datetime(2026, 11, 21, 10, 0),
            end_time=datetime(2026, 11, 21, 11, 0),
            status='Scheduled'
        )
        db.session.add(existing)
        db.session.commit()

        login_as_tenant(client)

        # Book a non-overlapping time
        response = client.post('/appointments/schedule', data={
            'agent_id': agent.user_id,
            'unit_id': unit.unit_id,
            'date_time': '2026-11-21T12:00',
            'end_time': '2026-11-21T13:00',
        }, follow_redirects=True)

        html = response.data.decode()
        assert 'already booked' not in html.lower()
        assert Appointment.query.count() == 2
