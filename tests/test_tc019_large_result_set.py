"""
TC-019: UI Responsiveness - No Freeze During Large Result Set
NFR1 + NFR7: Performance and responsive UI.

Preconditions: Database contains 1,000+ units.
Steps: Search with broad filters (200+ results). Scroll results. Click detail.
Expected: UI remains responsive, no crash, response < 2 seconds.
"""
import time
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_tenant


def test_large_result_set_response(client, app, seed_users):
    """TC-019: Search returning 200+ results responds in < 2s with valid HTML."""
    with app.app_context():
        mall = Mall(name='Large Mall', location='Large City')
        db.session.add(mall)
        db.session.commit()

        # Seed 1000+ units, all Available to ensure broad results
        units = []
        for i in range(1100):
            units.append(StoreUnit(
                mall_id=mall.mall_id,
                location=f'Large-Unit-{i}',
                size=100,
                rental_rate=1000 + (i % 500),
                availability='Available',
                business_purpose='Retail',
            ))
        db.session.bulk_save_objects(units)
        db.session.commit()

        login_as_tenant(client)

        # Broad search returning all available units
        start = time.time()
        response = client.get('/units/search?availability=Available')
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0, f'Large result set took {elapsed:.2f}s'

        html = response.data.decode()
        # Verify it's valid HTML with content
        assert 'Large-Unit-0' in html
        assert '</html>' in html.lower()


def test_unit_detail_page_loads(client, app, seed_users):
    """Clicking into a unit detail page should load quickly."""
    with app.app_context():
        mall = Mall(name='Detail Mall', location='Detail City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id, location='Detail-Unit',
            size=100, rental_rate=5000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()
        unit_id = unit.unit_id

        login_as_tenant(client)

        start = time.time()
        response = client.get(f'/units/{unit_id}')
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0
