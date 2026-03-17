from flask_login import UserMixin
from models import db


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.Enum('Admin', 'LeasingAgent', 'Tenant'), nullable=False)
    phone = db.Column(db.String(20))
    status = db.Column(db.Enum('Active', 'Inactive', 'Suspended'), nullable=False, default='Active')

    # Admin-specific
    company_name = db.Column(db.String(150))

    # LeasingAgent-specific
    availability_schedule = db.Column(db.String(255))

    # Tenant-specific
    preferred_payment_cycle = db.Column(db.Enum('Monthly', 'Quarterly', 'Semi-Annual', 'Annual'))

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    # Relationships
    appointments_as_agent = db.relationship('Appointment', foreign_keys='Appointment.agent_id', backref='agent', lazy=True)
    appointments_as_tenant = db.relationship('Appointment', foreign_keys='Appointment.tenant_id', backref='tenant', lazy=True)
    rental_applications = db.relationship('RentalApplication', backref='tenant', lazy=True)
    leases = db.relationship('Lease', backref='tenant', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True)
    discounts = db.relationship('Discount', backref='tenant', lazy=True)

    def get_id(self):
        return str(self.user_id)
