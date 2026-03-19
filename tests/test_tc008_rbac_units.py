"""
TC-008: Role-Based Access Control - Units/Property
FR24: Enforce role-based access control.

Preconditions: Tenant is logged in with the Tenant role.
Steps: Tenant clicks on "Properties".
Expected: Tenant cannot add, update, or delete properties; can only search.
"""
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_tenant, login_as_admin


def test_tenant_cannot_access_create_unit(client, app, seed_users):
    """TC-008a: Tenant GET /units/create returns 403."""
    login_as_tenant(client)
    response = client.get('/units/create')
    assert response.status_code == 403


def test_tenant_cannot_post_create_unit(client, app, seed_users):
    """TC-008b: Tenant POST /units/create returns 403."""
    with app.app_context():
        mall = Mall(name='RBAC Mall', location='900 RBAC St')
        db.session.add(mall)
        db.session.commit()

        login_as_tenant(client)

        response = client.post('/units/create', data={
            'mall_id': mall.mall_id,
            'location': 'Forbidden Unit',
            'size': '50',
            'rental_rate': '1000',
        })
        assert response.status_code == 403


def test_tenant_cannot_edit_unit(client, app, seed_users):
    """TC-008c: Tenant POST /units/<id>/edit returns 403."""
    with app.app_context():
        mall = Mall(name='Edit Mall', location='901 Edit St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Edit-Unit', size=50,
            rental_rate=1000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.unit_id

        login_as_tenant(client)

        response = client.post(f'/units/{unit_id}/edit', data={
            'mall_id': mall.mall_id,
            'location': 'Hacked Unit',
            'size': '50',
            'rental_rate': '1000',
            'availability': 'Available',
        })
        assert response.status_code == 403


def test_tenant_can_search_units(client, app, seed_users, seed_units):
    """TC-008d: Tenant can search/view units (read-only access)."""
    login_as_tenant(client)

    response = client.get('/units/search')
    assert response.status_code == 200

    response = client.get('/units/')
    assert response.status_code == 200
