"""
Shared pytest fixtures for the REMS test suite.

Uses an in-memory SQLite database so tests never touch the live MySQL data.
"""
import sys
import os
import pytest

# Add src/ to the Python path so imports resolve correctly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import create_app, bcrypt
from models import db as _db
from models.user import User
from models.mall import Mall
from models.store_unit import StoreUnit
from models.appointment import Appointment
from models.rental_application import RentalApplication
from models.lease import Lease
from models.invoice import Invoice
from models.payment import Payment
from models.utility_usage import UtilityUsage
from models.maintenance_request import MaintenanceRequest
from models.notification import Notification
from models.discount import Discount
from datetime import date, datetime


@pytest.fixture(scope='session')
def app():
    """Create a Flask application configured for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost',
    })
    return app


@pytest.fixture(autouse=True)
def setup_db(app):
    """Create all tables before each test and drop them after."""
    with app.app_context():
        _db.create_all()
        yield
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """Provide access to the db session within app context."""
    with app.app_context():
        yield _db.session


# ---------------------------------------------------------------------------
# Helper: Create common seed data
# ---------------------------------------------------------------------------

def _hash_pw(password='password123'):
    """Hash a password using bcrypt (same method the app uses)."""
    return bcrypt.generate_password_hash(password).decode('utf-8')


@pytest.fixture
def seed_users(app):
    """Seed an admin, a leasing agent, and a tenant. Returns dict of users."""
    with app.app_context():
        admin = User(
            username='admin_test', password=_hash_pw(), name='Test Admin',
            email='admin@test.com', role='Admin', status='Active',
            company_name='Test Co'
        )
        agent = User(
            username='agent_test', password=_hash_pw(), name='Test Agent',
            email='agent@test.com', role='LeasingAgent', status='Active',
            availability_schedule='Mon-Fri 9-5'
        )
        tenant = User(
            username='tenant_test', password=_hash_pw(), name='Test Tenant',
            email='tenant@test.com', role='Tenant', status='Active',
            preferred_payment_cycle='Monthly'
        )
        _db.session.add_all([admin, agent, tenant])
        _db.session.commit()
        return {'admin': admin, 'agent': agent, 'tenant': tenant}


@pytest.fixture
def seed_mall(app):
    """Seed a mall. Returns the Mall object."""
    with app.app_context():
        mall = Mall(name='Test Mall', location='123 Test St')
        _db.session.add(mall)
        _db.session.commit()
        return mall


@pytest.fixture
def seed_units(app, seed_mall):
    """Seed three store units at $1000, $2000, $3000. Returns list of units."""
    with app.app_context():
        mall = Mall.query.first()
        units = []
        for rate in [1000, 2000, 3000]:
            u = StoreUnit(
                mall_id=mall.mall_id, location=f'Unit-{rate}',
                size=100, rental_rate=rate, classification_tier='Standard',
                business_purpose='Retail', availability='Available',
                contact_info='test@test.com'
            )
            _db.session.add(u)
            units.append(u)
        _db.session.commit()
        return units


# ---------------------------------------------------------------------------
# Helper: Login functions
# ---------------------------------------------------------------------------

def login(client, username, password='password123'):
    """Log in a user via the login form."""
    return client.post('/login', data={
        'username': username,
        'password': password,
    }, follow_redirects=True)


def login_as_admin(client):
    return login(client, 'admin_test')


def login_as_agent(client):
    return login(client, 'agent_test')


def login_as_tenant(client):
    return login(client, 'tenant_test')
