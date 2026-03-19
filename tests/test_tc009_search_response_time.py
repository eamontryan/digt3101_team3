"""
TC-009: Search Response Time
NFR1: System shall process search queries within 2 seconds.

Preconditions: Database populated with 1,000+ mock unit records.
Steps: Initiate a search with multiple filters. Measure time.
Expected: Results load in < 2 seconds.
"""
import time
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_tenant


def test_search_response_time_under_2_seconds(client, app, seed_users):
    """TC-009: Search with filters must complete in < 2 seconds."""
    with app.app_context():
        mall = Mall(name='Perf Mall', location='Perf City')
        db.session.add(mall)
        db.session.commit()

        # Seed 1000+ units
        units = []
        for i in range(1100):
            units.append(StoreUnit(
                mall_id=mall.mall_id,
                location=f'Perf-Unit-{i}',
                size=50 + (i % 200),
                rental_rate=1000 + (i * 10),
                classification_tier='Standard' if i % 2 == 0 else 'Premium',
                business_purpose='Retail' if i % 3 == 0 else 'Services',
                availability='Available' if i % 4 != 0 else 'Occupied',
            ))
        db.session.bulk_save_objects(units)
        db.session.commit()

        login_as_tenant(client)

        start = time.time()
        response = client.get('/units/search?max_rate=5000&min_size=100&availability=Available')
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 2.0, f'Search took {elapsed:.2f}s, expected < 2.0s'
