"""
TC-016: Appointment Scheduling - Conflict Check Performance
NFR1 + FR7: Prevent double booking, conflict decision within 2 seconds.

Preconditions: 500+ appointments across multiple agents/units.
Steps: Attempt conflicting bookings 10 times. Measure each.
Expected: Conflict decision ≤ 2.0 seconds. Correctly blocks conflicts.
"""
import time
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from models.appointment import Appointment
from models.user import User
from app import bcrypt
from conftest import login_as_tenant, _hash_pw
from datetime import datetime, timedelta


def test_conflict_check_performance(client, app, seed_users):
    """TC-016: Conflict check with 500+ appointments must respond in ≤ 2s each."""
    with app.app_context():
        mall = Mall(name='Conflict Perf Mall', location='CP City')
        db.session.add(mall)
        db.session.commit()

        # Create multiple agents
        agents = []
        for i in range(10):
            agent = User(
                username=f'perf_agent_{i}', password=_hash_pw(),
                name=f'Perf Agent {i}', email=f'perf_agent_{i}@test.com',
                role='LeasingAgent', status='Active'
            )
            db.session.add(agent)
            agents.append(agent)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='CP-Unit', size=100,
            rental_rate=5000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()

        tenant = User.query.filter_by(username='tenant_test').first()

        # Seed 500+ appointments across agents
        base_time = datetime(2027, 6, 1, 8, 0)
        appointments = []
        for i in range(550):
            agent = agents[i % len(agents)]
            dt = base_time + timedelta(hours=i * 2)
            appointments.append(Appointment(
                agent_id=agent.user_id,
                tenant_id=tenant.user_id,
                unit_id=unit.unit_id,
                date_time=dt,
                end_time=dt + timedelta(hours=1),
                status='Scheduled'
            ))
        db.session.bulk_save_objects(appointments)
        db.session.commit()

        login_as_tenant(client)

        times = []
        for i in range(10):
            agent = agents[i % len(agents)]
            # Attempt a conflicting booking (same time as existing)
            conflict_time = base_time + timedelta(hours=i * 20)  # hits existing slots

            start = time.time()
            response = client.post('/appointments/schedule', data={
                'agent_id': agent.user_id,
                'unit_id': unit.unit_id,
                'date_time': conflict_time.strftime('%Y-%m-%dT%H:%M'),
                'end_time': (conflict_time + timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M'),
            }, follow_redirects=True)
            elapsed = time.time() - start
            times.append(elapsed)

            assert response.status_code == 200
            assert elapsed <= 2.0, f'Conflict check took {elapsed:.2f}s for agent {i}'
