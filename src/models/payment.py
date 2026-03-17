from models import db


class Payment(db.Model):
    __tablename__ = 'payment'

    payment_id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoice.invoice_id'), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    payment_date = db.Column(db.Date)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Pending', 'Completed', 'Failed', 'Refunded'), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())
