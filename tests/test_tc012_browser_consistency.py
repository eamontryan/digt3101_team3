"""
TC-012: Browser Layout Consistency
NFR8: Compatible with standard web browsers (Chrome, Firefox, Edge).

Preconditions: System is deployed and accessible.
Steps: Open Tenant Dashboard in Chrome/Firefox. Compare layout.
Expected: Layout, fonts, button positions identical across browsers.

NOTE: This is a structural test verifying that the Bootstrap 5 framework
      (providing cross-browser consistency) is loaded in the templates.
      Full visual comparison is a manual testing activity.
"""
from conftest import login_as_tenant


def test_dashboard_includes_bootstrap(client, app, seed_users):
    """TC-012: Dashboard HTML includes Bootstrap 5 CSS for cross-browser support."""
    login_as_tenant(client)

    response = client.get('/')
    assert response.status_code == 200

    html = response.data.decode()
    # Bootstrap 5 CDN or local reference should be present
    assert 'bootstrap' in html.lower()


def test_html_has_doctype(client, app, seed_users):
    """Pages should have valid HTML5 doctype for consistent rendering."""
    login_as_tenant(client)

    response = client.get('/')
    html = response.data.decode()
    assert '<!doctype html>' in html.lower() or '<!DOCTYPE html>' in html
