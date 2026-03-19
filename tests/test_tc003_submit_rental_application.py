"""
TC-003: Submit Rental Application - Valid Information
FR9: Allow tenants to submit digital rental applications.

Preconditions: Tenant is logged in.
Steps: Navigate to submit, complete all fields, upload docs, click Submit.
Expected: Application is stored, tenant sees confirmation message.
"""
from models import db
from models.rental_application import RentalApplication
from models.store_unit import StoreUnit
from models.mall import Mall
from conftest import login_as_tenant


def test_submit_rental_application(client, app, seed_users):
    """TC-003: Tenant can submit a rental application successfully."""
    with app.app_context():
        mall = Mall(name='App Mall', location='100 App St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Unit-Apply', size=80,
            rental_rate=2000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.unit_id

        login_as_tenant(client)

        response = client.post('/applications/submit', data={
            'unit_id': unit_id,
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode()
        assert 'submitted successfully' in html.lower() or 'success' in html.lower()

        # Verify application is stored in the DB
        app_record = RentalApplication.query.filter_by(unit_id=unit_id).first()
        assert app_record is not None
        assert app_record.status == 'Pending'


def test_submit_application_requires_tenant_role(client, app, seed_users):
    """Only Tenant role users can submit rental applications."""
    with app.app_context():
        mall = Mall(name='Agent Mall', location='200 Agent St')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Unit-No', size=80,
            rental_rate=2000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()

        from conftest import login_as_agent
        login_as_agent(client)

        response = client.post('/applications/submit', data={
            'unit_id': unit.unit_id,
        }, follow_redirects=False)

        # Agent should get 403
        assert response.status_code == 403
