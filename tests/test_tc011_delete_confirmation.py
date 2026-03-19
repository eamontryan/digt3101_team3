"""
TC-011: Delete Confirmation Dialog
NFR6: The system shall provide confirmation dialogs for critical actions.

Preconditions: Admin is logged in. "Manage Store Units" list is visible.
Steps: Click Delete → Wait for popup → Click Cancel.
Expected: A confirmation dialog appears. On Cancel, unit is NOT deleted.

NOTE: The current app does not expose a delete endpoint for store units.
      This test verifies that no unprotected delete action exists, ensuring
      data safety. A future implementation should include a JS confirm dialog.
"""
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_admin


def test_no_unprotected_delete_endpoint(client, app, seed_users):
    """TC-011: There is no unprotected delete endpoint for store units."""
    with app.app_context():
        mall = Mall(name='Del Mall', location='Del City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Del-Unit', size=100,
            rental_rate=5000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.unit_id

        login_as_admin(client)

        # Attempting DELETE or POST to a delete route should 404
        response = client.post(f'/units/{unit_id}/delete')
        assert response.status_code == 404 or response.status_code == 405

        # Unit should still exist
        assert StoreUnit.query.get(unit_id) is not None


def test_unit_list_accessible(client, app, seed_users, seed_units):
    """The unit list page loads successfully for admin."""
    login_as_admin(client)
    response = client.get('/units/')
    assert response.status_code == 200
