from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import all models so SQLAlchemy can resolve relationships
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
from models.application_document import ApplicationDocument
from models.lease_document import LeaseDocument
