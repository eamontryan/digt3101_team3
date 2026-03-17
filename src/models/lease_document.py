from models import db


class LeaseDocument(db.Model):
    __tablename__ = 'lease_document'

    document_id = db.Column(db.Integer, primary_key=True)
    lease_id = db.Column(db.Integer, db.ForeignKey('lease.lease_id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    generated_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())
