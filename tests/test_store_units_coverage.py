import pytest
from unittest.mock import patch
from datetime import date, timedelta
from models import db
from models.store_unit import StoreUnit
from models.mall import Mall
from models.lease import Lease


def test_search_with_mall_filter(client, seed_users, seed_units, seed_mall):
    """Test search filtering by mall_id."""
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    mall = seed_mall
    resp = client.get(f'/units/search?mall_id={mall.mall_id}')
    assert resp.status_code == 200
    assert b'Unit-1000' in resp.data


def test_search_with_classification_filter(client, seed_users, seed_units):
    """Test search filtering by classification_tier."""
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get('/units/search?classification_tier=Standard')
    assert resp.status_code == 200
    assert b'Unit-1000' in resp.data


def test_edit_unit_get(client, seed_users, seed_units):
    """Test GET request for editing a store unit."""
    unit = seed_units[0]
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.get(f'/units/{unit.unit_id}/edit')
    assert resp.status_code == 200
    assert b'Unit-1000' in resp.data


def test_edit_unit_post(client, seed_users, seed_units, seed_mall):
    """Test POST request for editing a store unit."""
    unit = seed_units[0]
    mall = seed_mall
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/units/{unit.unit_id}/edit', data={
        'mall_id': mall.mall_id,
        'location': 'Updated Location',
        'size': '150',
        'rental_rate': '1500',
        'classification_tier': 'Premium',
        'business_purpose': 'Food Court',
        'availability': 'Available',
        'contact_info': 'updated@test.com'
    }, follow_redirects=True)
    assert b'Store unit updated successfully' in resp.data

    with client.application.app_context():
        u = StoreUnit.query.get(unit.unit_id)
        assert u.location == 'Updated Location'
        assert u.rental_rate == 1500


def test_delete_unit_success(client, seed_users, seed_units):
    """Test successful deletion of a store unit with no active leases."""
    unit = seed_units[2]  # Use the third unit to avoid conflicts
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/units/{unit.unit_id}/delete', follow_redirects=True)
    assert b'Store unit deleted successfully' in resp.data

    with client.application.app_context():
        u = StoreUnit.query.get(unit.unit_id)
        assert u is None


def test_delete_unit_with_active_lease(client, seed_users, seed_units):
    """Test deletion blocked when unit has active leases."""
    unit = seed_units[0]
    with client.application.app_context():
        l1 = Lease(tenant_id=seed_users['tenant'].user_id, unit_id=unit.unit_id,
                    start_date=date.today(), end_date=date.today() + timedelta(days=365),
                    payment_cycle='Monthly', status='Active')
        db.session.add(l1)
        db.session.commit()

    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    resp = client.post(f'/units/{unit.unit_id}/delete', follow_redirects=True)
    assert b'Cannot delete unit' in resp.data


def test_create_unit_db_error(client, seed_users, seed_mall):
    """Test rollback when db error occurs during unit creation."""
    mall = seed_mall
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post('/units/create', data={
            'mall_id': mall.mall_id,
            'location': 'Error Unit',
            'size': '100',
            'rental_rate': '500',
            'availability': 'Available'
        }, follow_redirects=True)
        assert b'An error occurred while creating the store unit' in resp.data


def test_edit_unit_db_error(client, seed_users, seed_units, seed_mall):
    """Test rollback when db error occurs during unit edit."""
    unit = seed_units[0]
    mall = seed_mall
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/units/{unit.unit_id}/edit', data={
            'mall_id': mall.mall_id,
            'location': 'Error Update',
            'size': '100',
            'rental_rate': '500',
            'availability': 'Available'
        }, follow_redirects=True)
        assert b'An error occurred while updating the store unit' in resp.data


def test_delete_unit_db_error(client, seed_users, seed_units):
    """Test rollback when db error occurs during unit deletion."""
    unit = seed_units[2]
    client.post('/login', data={'username': 'admin_test', 'password': 'password123'})
    with patch.object(db.session, 'commit', side_effect=Exception('DB error')):
        resp = client.post(f'/units/{unit.unit_id}/delete', follow_redirects=True)
        assert b'An error occurred while deleting the store unit' in resp.data
