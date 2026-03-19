"""
TC-013: Mobile Interface Adaptation
NFR7: Responsive interface for mobile devices.

Preconditions: User is accessing via desktop browser.
Steps: Resize to 375px width. Observe nav menu and tables.
Expected: Nav collapses to hamburger. Tables stack or scroll.

NOTE: This is a structural test verifying that responsive meta tags and
      Bootstrap responsive components (navbar-toggler) are present.
      Full visual validation is a manual testing activity.
"""
from conftest import login_as_tenant


def test_responsive_viewport_meta_tag(client, app, seed_users):
    """TC-013a: Pages include the responsive viewport meta tag."""
    login_as_tenant(client)

    response = client.get('/')
    html = response.data.decode()
    assert 'viewport' in html.lower()
    assert 'width=device-width' in html.lower()


def test_navbar_toggler_present(client, app, seed_users):
    """TC-013b: Navbar includes a toggler (hamburger menu) for mobile."""
    login_as_tenant(client)

    response = client.get('/')
    html = response.data.decode()
    # Bootstrap navbar-toggler class enables the hamburger menu
    assert 'navbar-toggler' in html or 'navbar-collapse' in html
