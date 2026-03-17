from models import db


class MaintenanceRequest(db.Model):
    __tablename__ = 'maintenance_request'

    request_id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.lease_id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.Enum('Low', 'Medium', 'High', 'Urgent'), nullable=False, default='Medium')
    status = db.Column(db.Enum('Open', 'In Progress', 'Resolved', 'Closed', 'Rejected'), nullable=False, default='Open')
    misuse_flag = db.Column(db.Boolean, nullable=False, default=False)
    charge_amount = db.Column(db.Numeric(12, 2))
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
