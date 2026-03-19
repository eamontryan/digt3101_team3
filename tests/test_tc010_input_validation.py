"""
TC-010: Input Validation - Special Characters
NFR5: The system shall validate user input to prevent malformed or invalid data.

Preconditions: Admin is logged in.
Steps: Enter <script>alert('test')</script> in a text field → Save.
Expected: Script is sanitized/escaped. Script does not execute in output.
"""
from models import db
from models.mall import Mall
from models.store_unit import StoreUnit
from conftest import login_as_admin


def test_script_tag_is_escaped_in_output(client, app, seed_users):
    """TC-010: Script tags in unit location should be escaped in rendered HTML."""
    with app.app_context():
        mall = Mall(name='XSS Mall', location='XSS City')
        db.session.add(mall)
        db.session.commit()

        login_as_admin(client)

        xss_payload = "<script>alert('test')</script>"

        response = client.post('/units/create', data={
            'mall_id': mall.mall_id,
            'location': xss_payload,
            'size': '100',
            'rental_rate': '5000',
            'classification_tier': 'Standard',
            'business_purpose': 'Retail',
            'availability': 'Available',
        }, follow_redirects=True)

        assert response.status_code == 200
        html = response.data.decode()

        # The raw <script> tag should NOT appear unescaped in the response
        assert '<script>alert' not in html
        # Jinja2 auto-escapes, so we expect the escaped version
        assert '&lt;script&gt;' in html or 'alert' not in html


def test_script_tag_in_search_results(client, app, seed_users):
    """Script tags stored in the DB should be escaped when rendered in search."""
    with app.app_context():
        mall = Mall(name='Safe Mall', location='Safe City')
        db.session.add(mall)
        db.session.commit()

        unit = StoreUnit(
            mall_id=mall.mall_id,
            location="<script>alert('xss')</script>",
            size=100, rental_rate=5000, availability='Available'
        )
        db.session.add(unit)
        db.session.commit()

        login_as_admin(client)

        response = client.get('/units/search')
        html = response.data.decode()
        # Must be escaped in output
        assert "<script>alert('xss')</script>" not in html
