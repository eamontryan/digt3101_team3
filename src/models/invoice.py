from models import db


class Invoice(db.Model):
    __tablename__ = 'invoice'

    invoice_id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.lease_id'), nullable=False)
    issue_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum('Pending', 'Paid', 'Overdue', 'Partially Paid', 'Cancelled'), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    payments = db.relationship('Payment', backref='invoice', lazy=True)
    utility_usages = db.relationship('UtilityUsage', backref='invoice', lazy=True)
    maintenance_charges = db.relationship('MaintenanceRequest', backref='invoice', lazy=True)
