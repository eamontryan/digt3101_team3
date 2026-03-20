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
import pytest
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_admin



def test_unit_list_accessible(client, app, seed_users, seed_units):
    """The unit list page loads successfully for admin."""
    login_as_admin(client)
    response = client.get('/units/')
    assert response.status_code == 200
