from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models.notification import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(
        recipient_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).all()

    return render_template('notifications/list.html', notifications=notifications)


@notifications_bp.route('/api')
@login_required
def api_notifications():
    notifications = Notification.query.filter_by(
        recipient_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).limit(10).all()

    return jsonify([{
        'id': n.notification_id,
        'type': n.type,
        'title': n.title,
        'message': n.message,
        'created_at': n.created_at.isoformat()
    } for n in notifications])
