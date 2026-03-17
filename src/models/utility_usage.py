from models import db


class UtilityUsage(db.Model):
    __tablename__ = 'utility_usage'

    utility_id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('store_unit.unit_id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'))
    type = db.Column(db.Enum('Electricity', 'Water', 'Waste Management'), nullable=False)
    usage_amount = db.Column(db.Numeric(10, 2), nullable=False)
    billing_month = db.Column(db.Date, nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
