from models import db


class StoreUnit(db.Model):
    __tablename__ = 'store_unit'

    unit_id = db.Column(db.Integer, primary_key=True)
    mall_id = db.Column(db.Integer, db.ForeignKey('mall.mall_id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    size = db.Column(db.Numeric(10, 2), nullable=False)
    rental_rate = db.Column(db.Numeric(12, 2), nullable=False)
    classification_tier = db.Column(db.String(50))
    business_purpose = db.Column(db.String(150))
    availability = db.Column(db.Enum('Available', 'Occupied', 'Under Maintenance'), nullable=False, default='Available')
    contact_info = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())

    appointments = db.relationship('Appointment', backref='unit', lazy=True)
    rental_applications = db.relationship('RentalApplication', backref='unit', lazy=True)
    leases = db.relationship('Lease', backref='unit', lazy=True)
    utility_usages = db.relationship('UtilityUsage', backref='unit', lazy=True)