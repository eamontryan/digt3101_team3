"""
TC-001: Search Store Unit - Valid Price Filter
FR4: The system shall allow tenants to search using filters.

Preconditions: Database contains units with rents $1000, $2000, $3000.
Steps: Enter "$2500" in the "Max Price" filter → Click "Search".
Expected: Only units costing $1000 and $2000 are displayed.
"""
from conftest import login_as_tenant


def test_search_max_price_filter(client, seed_users, seed_units):
    """TC-001: Only units at or below max_rate should be returned."""
    login_as_tenant(client)

    response = client.get('/units/search?max_rate=2500')
    assert response.status_code == 200

    html = response.data.decode()
    assert 'Unit-1000' in html
    assert 'Unit-2000' in html
    assert 'Unit-3000' not in html


def test_search_no_max_price_returns_all(client, seed_users, seed_units):
    """Verify that omitting max_rate returns all units."""
    login_as_tenant(client)

    response = client.get('/units/search')
    html = response.data.decode()
    assert 'Unit-1000' in html
    assert 'Unit-2000' in html
    assert 'Unit-3000' in html
