"""
TC-004: Manage Store Units - Add New Unit
FR1: Add, update, view, and delete store unit records.

Preconditions: Leasing Agent (actually Admin per route) is logged in.
Steps: Select "Add Unit", enter valid unit info, save.
Expected: New unit stored and appears in the unit list.
"""
from models import db
from models.store_unit import StoreUnit
from models.mall import Mall
from conftest import login_as_admin, login_as_tenant


def test_admin_can_add_store_unit(client, app, seed_users):
    """TC-004: Admin can create a new store unit."""
    with app.app_context():
        mall = Mall(name='Add Mall', location='300 Add St')
        db.session.add(mall)
        db.session.commit()
        mall_id = mall.mall_id

        login_as_admin(client)

        response = client.post('/units/create', data={
            'mall_id': mall_id,
            'location': 'Ground Floor, Unit NEW-01',
            'size': '120.00',
            'rental_rate': '75000.00',
            'classification_tier': 'Premium',
            'business_purpose': 'Retail',
            'availability': 'Available',
            'contact_info': 'new@test.com',
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode()
        assert 'created successfully' in html.lower() or 'success' in html.lower()

        # Verify the unit exists in DB
        unit = StoreUnit.query.filter_by(location='Ground Floor, Unit NEW-01').first()
        assert unit is not None
        assert float(unit.rental_rate) == 75000.00
        assert unit.classification_tier == 'Premium'


def test_tenant_cannot_add_store_unit(client, app, seed_users):
    """Tenants should be forbidden from creating store units."""
    with app.app_context():
        mall = Mall(name='Blocked Mall', location='400 Block St')
        db.session.add(mall)
        db.session.commit()

        login_as_tenant(client)

        response = client.post('/units/create', data={
            'mall_id': mall.mall_id,
            'location': 'Blocked Unit',
            'size': '50',
            'rental_rate': '5000',
        }, follow_redirects=False)

        assert response.status_code == 403
