import pytest
from unittest.mock import patch
from datetime import datetime, timedelta
from models import db
from models.appointment import Appointment
from models.user import User
from routes.appointments import check_agent_availability

def test_list_appointments_tenant(client, seed_users, seed_units):
    admin_u = seed_users['admin']
    tenant_u = seed_users['tenant']
    u1, u2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        # Tenant's appt
        a1 = Appointment(agent_id=admin_u.user_id, tenant_id=tenant_u.user_id, unit_id=u1.unit_id, date_time=datetime.now(), end_time=datetime.now()+timedelta(hours=1))
        # Someone else's appt
        a2 = Appointment(agent_id=admin_u.user_id, tenant_id=admin_u.user_id, unit_id=u2.unit_id, date_time=datetime.now(), end_time=datetime.now()+timedelta(hours=1))
        db.session.add_all([a1, a2])
        db.session.commit()
        a1_id = a1.appointment_id
        a2_id = a2.appointment_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/appointments/')
    assert resp.status_code == 200
    assert b'Unit-1000' in resp.data
    assert b'Unit-2000' not in resp.data

def test_list_appointments_agent(client, seed_users, seed_units):
    admin_u = seed_users['admin']
    agent_u = seed_users['agent']
    tenant_u = seed_users['tenant']
    u1, u2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        # Agent's appt
        a1 = Appointment(agent_id=agent_u.user_id, tenant_id=tenant_u.user_id, unit_id=u1.unit_id, date_time=datetime.now(), end_time=datetime.now()+timedelta(hours=1))
        # Someone else's appt
        a2 = Appointment(agent_id=admin_u.user_id, tenant_id=tenant_u.user_id, unit_id=u2.unit_id, date_time=datetime.now(), end_time=datetime.now()+timedelta(hours=1))
        db.session.add_all([a1, a2])
        db.session.commit()
        a1_id = a1.appointment_id
        a2_id = a2.appointment_id

    client.post('/login', data={'username': 'agent_test', 'password': 'password123'})
    resp = client.get('/appointments/')
    assert resp.status_code == 200
    assert b'Unit-1000' in resp.data
    assert b'Unit-2000' not in resp.data

def test_list_appointments_admin(client, seed_users, seed_units):
    admin_u = seed_users['admin']
    agent_u = seed_users['agent']
    tenant_u = seed_users['tenant']
    u1, u2 = seed_units[0], seed_units[1]
    
    with client.application.app_context():
        a1 = Appointment(agent_id=agent_u.user_id, tenant_id=tenant_u.user_id, unit_id=u1.unit_id, date_time=datetime.now(), end_time=datetime.now()+timedelta(hours=1))
        a2 = Appointment(agent_id=admin_u.user_id, tenant_id=tenant_u.user_id, unit_id=u2.unit_id, date_time=datetime.now(), end_time=datetime.now()+timedelta(hours=1))
        db.session.add_all([a1, a2])
        db.session.commit()
        a1_id = a1.appointment_id
        a2_id = a2.appointment_id

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/appointments/')
    assert resp.status_code == 200
    assert b'Unit-1000' in resp.data
    assert b'Unit-2000' in resp.data

def test_schedule_appointment_get(client, seed_users):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.get('/appointments/schedule')
    assert resp.status_code == 200
    assert b'Schedule Appointment' in resp.data

def test_schedule_appointment_post_past_time(client, seed_users, seed_units):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    data = {
        'agent_id': seed_users['agent'].user_id,
        'unit_id': seed_units[0].unit_id,
        'date_time': '2000-01-01T10:00',
        'end_time': '2000-01-01T11:00'
    }
    resp = client.post('/appointments/schedule', data=data, follow_redirects=True)
    assert b'Appointment must be scheduled in the future' in resp.data

def test_schedule_appointment_post_end_before_start(client, seed_users, seed_units):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    data = {
        'agent_id': seed_users['agent'].user_id,
        'unit_id': seed_units[0].unit_id,
        'date_time': '2099-01-01T11:00',
        'end_time': '2099-01-01T10:00'
    }
    resp = client.post('/appointments/schedule', data=data, follow_redirects=True)
    assert b'End time must be after start time' in resp.data

def test_schedule_appointment_post_agent_unavailable(client, seed_users, seed_units):
    """Test scheduling outside of agent's availability blocks."""
    agent_u = seed_users['agent']
    with client.application.app_context():
        a = \
User.query.get(agent_u.user_id)
        a.availability_schedule = 'Mon-Fri 9AM-5PM'
        db.session.commit()

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    
    # 2099-01-04 is a Sunday (assuming we can easily pick a Sunday or just pick 8PM)
    data = {
        'agent_id': agent_u.user_id,
        'unit_id': seed_units[0].unit_id,
        'date_time': '2099-01-01T20:00', # Thursday 8:00 PM is outside 9-5
        'end_time': '2099-01-01T21:00'
    }
    resp = client.post('/appointments/schedule', data=data, follow_redirects=True)
    assert b'is not available at that time' in resp.data

def test_schedule_appointment_post_success(client, seed_users, seed_units):
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    
    # Find a Tuesday at 10 AM (which works for Mon-Fri 9-5)
    # 2099-01-06 is a Tuesday
    data = {
        'agent_id': seed_users['agent'].user_id,
        'unit_id': seed_units[0].unit_id,
        'date_time': '2099-01-06T10:00',
        'end_time': '2099-01-06T11:00'
    }
    resp = client.post('/appointments/schedule', data=data, follow_redirects=True)
    assert b'Appointment scheduled successfully' in resp.data
    
    with client.application.app_context():
        appt = Appointment.query.first()
        assert appt is not None
        assert appt.status == 'Scheduled'

def test_cancel_appointment(client, seed_users, seed_units):
    tenant_u = seed_users['tenant']
    agent_u = seed_users['agent']
    with client.application.app_context():
        a1 = Appointment(agent_id=agent_u.user_id, tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id, date_time=datetime.now()+timedelta(days=1), end_time=datetime.now()+timedelta(days=1, hours=1))
        db.session.add(a1)
        db.session.commit()
        a1_id = a1.appointment_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    resp = client.post(f'/appointments/{a1_id}/cancel', follow_redirects=True)
    assert b'Appointment cancelled' in resp.data
    
    with client.application.app_context():
        a = Appointment.query.get(a1_id)
        assert a.status == 'Cancelled'

def test_check_agent_availability_helper():
    """Directly test the check_agent_availability function for complex parsing."""
    class DummyAgent:
        def __init__(self, sched):
            self.availability_schedule = sched
            
    # Test Sat-Sun
    agent1 = DummyAgent('Sat-Sun 10AM-4PM')
    # 2099-01-03 is Saturday
    dt1_start = datetime.strptime('2099-01-03T10:30', '%Y-%m-%dT%H:%M')
    dt1_end = datetime.strptime('2099-01-03T11:30', '%Y-%m-%dT%H:%M')
    assert check_agent_availability(agent1, dt1_start, dt1_end) is True
    
    # Test out of bounds time
    dt2_start = datetime.strptime('2099-01-03T16:30', '%Y-%m-%dT%H:%M')
    dt2_end = datetime.strptime('2099-01-03T17:30', '%Y-%m-%dT%H:%M')
    assert check_agent_availability(agent1, dt2_start, dt2_end) is False

    # Test wrap-around days (Thu-Mon)
    agent2 = DummyAgent('Thu-Mon 9AM-5PM')
    dt3_start = datetime.strptime('2099-01-05T10:00', '%Y-%m-%dT%H:%M') # Monday
    dt3_end = datetime.strptime('2099-01-05T11:00', '%Y-%m-%dT%H:%M')
    assert check_agent_availability(agent2, dt3_start, dt3_end) is True
    
    # 2099-01-07 is Wednesday (Should fail)
    dt4_start = datetime.strptime('2099-01-07T10:00', '%Y-%m-%dT%H:%M')
    dt4_end = datetime.strptime('2099-01-07T11:00', '%Y-%m-%dT%H:%M')
    assert check_agent_availability(agent2, dt4_start, dt4_end) is False


def test_schedule_appointment_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during appointment scheduling."""
    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        data = {
            'agent_id': seed_users['agent'].user_id,
            'unit_id': seed_units[0].unit_id,
            'date_time': '2099-01-06T10:00',
            'end_time': '2099-01-06T11:00'
        }
        resp = client.post('/appointments/schedule', data=data, follow_redirects=True)
        assert b'An error occurred while scheduling the appointment' in resp.data


def test_cancel_appointment_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during appointment cancellation."""
    tenant_u = seed_users['tenant']
    agent_u = seed_users['agent']
    with client.application.app_context():
        a1 = Appointment(agent_id=agent_u.user_id, tenant_id=tenant_u.user_id, unit_id=seed_units[0].unit_id,
                         date_time=datetime.now()+timedelta(days=1), end_time=datetime.now()+timedelta(days=1, hours=1))
        db.session.add(a1)
        db.session.commit()
        a1_id = a1.appointment_id

    client.post('/login', data={'username': 'tenant_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/appointments/{a1_id}/cancel', follow_redirects=True)
        assert b'An error occurred while cancelling the appointment' in resp.data
