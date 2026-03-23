from flask import Blueprint, render_template, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.notification import Notification

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')


@notifications_bp.route('/')
@login_required
def list_notifications():
    notifications = Notification.query.filter_by(
        recipient_id=current_user.user_id
    ).order_by(Notification.created_at.desc()).all()

    return render_template('notifications/list.html', notifications=notifications)


@notifications_bp.route('/<int:notification_id>/dismiss', methods=['POST'])
@login_required
def dismiss(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    if notification.recipient_id != current_user.user_id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('notifications.list_notifications'))
    try:
        db.session.delete(notification)
        db.session.commit()
        flash('Notification dismissed.', 'info')
    except Exception:
        db.session.rollback()
        flash('An error occurred while dismissing the notification.', 'danger')
    return redirect(url_for('notifications.list_notifications'))


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

