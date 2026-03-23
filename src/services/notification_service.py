from models import db
from models.notification import Notification


def create_notification(recipient_id, notif_type, title, message,
                        related_entity=None, related_id=None):
    notification = Notification(
        recipient_id=recipient_id,
        type=notif_type,
        title=title,
        message=message,
        related_entity=related_entity,
        related_id=related_id
    )
    try:
        db.session.add(notification)
        db.session.commit()
        return notification
    except Exception:
        db.session.rollback()
        raise
