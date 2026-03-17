from models import db


class Lease(db.Model):
    __tablename__ = 'lease'

    lease_id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('store_unit.unit_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    payment_cycle = db.Column(db.Enum('Monthly', 'Quarterly', 'Semi-Annual', 'Annual'), nullable=False, default='Monthly')
    status = db.Column(db.Enum('Active', 'Expired', 'Terminated', 'Pending'), nullable=False, default='Pending')

    # Electronic signing
    tenant_signature = db.Column(db.String(255))
    tenant_signed_at = db.Column(db.DateTime)
    agent_signature = db.Column(db.String(255))
    agent_signed_at = db.Column(db.DateTime)
    signature_status = db.Column(db.Enum('Unsigned', 'Partially Signed', 'Fully Signed'), nullable=False, default='Unsigned')

    # Lease renewal policy
    auto_renew = db.Column(db.Boolean, nullable=False, default=False)
    renewal_rate_increase = db.Column(db.Numeric(5, 2))
    renewal_status = db.Column(db.Enum('Not Applicable', 'Pending Renewal', 'Renewed', 'Declined'), nullable=False, default='Not Applicable')

    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    invoices = db.relationship('Invoice', backref='lease', lazy=True)
    maintenance_requests = db.relationship('MaintenanceRequest', backref='lease', lazy=True)
    documents = db.relationship('LeaseDocument', backref='lease', lazy=True)
