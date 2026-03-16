from models import db


class RentalApplication(db.Model):
    __tablename__ = 'rental_application'

    application_id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('store_unit.unit_id'), nullable=False)
    submission_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('Pending', 'Approved', 'Rejected', 'Withdrawn'), nullable=False, default='Pending')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    documents = db.relationship('ApplicationDocument', backref='application', lazy=True)
