from models import db


class Appointment(db.Model):
    __tablename__ = 'appointment'

    appointment_id = db.Column(db.Integer, primary_key=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    tenant_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('store_unit.unit_id'), nullable=False)
    date_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Enum('Scheduled', 'Completed', 'Cancelled', 'No-Show'), nullable=False, default='Scheduled')
    created_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now(), onupdate=db.func.now())