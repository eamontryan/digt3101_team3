"""
TC-014: Search Store Units - Response Time Under Load
NFR1: Search queries must load within 2 seconds.

Preconditions: Database contains 1,000+ store units.
Steps: Apply filters, click Search, repeat 10 times, record response times.
Expected: Average ≤ 2.0s and no single run > 3.0s.
"""
import time
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_tenant


def test_search_response_time_under_load(client, app, seed_users):
    """TC-014: 10 repeated searches must average ≤ 2.0s, no run > 3.0s."""
    with app.app_context():
        mall = Mall(name='Load Mall', location='Load City')
        db.session.add(mall)
        db.session.commit()

        units = []
        for i in range(1100):
            units.append(StoreUnit(
                mall_id=mall.mall_id,
                location=f'Load-Unit-{i}',
                size=50 + (i % 200),
                rental_rate=1000 + (i * 5),
                classification_tier='Standard' if i % 2 == 0 else 'Premium',
                business_purpose='Retail' if i % 3 == 0 else 'Services',
                availability='Available' if i % 4 != 0 else 'Occupied',
            ))
        db.session.bulk_save_objects(units)
        db.session.commit()

        login_as_tenant(client)

        times = []
        for _ in range(10):
            start = time.time()
            response = client.get(
                '/units/search?max_rate=2500&availability=Available&business_purpose=Retail'
            )
            elapsed = time.time() - start
            times.append(elapsed)
            assert response.status_code == 200

        avg_time = sum(times) / len(times)
        max_time = max(times)

        assert avg_time <= 2.0, f'Average {avg_time:.2f}s exceeds 2.0s'
        assert max_time <= 3.0, f'Max {max_time:.2f}s exceeds 3.0s'
