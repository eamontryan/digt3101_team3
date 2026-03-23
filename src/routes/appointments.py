import re
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from routes import role_required, get_active_role
from models import db
from models.appointment import Appointment
from models.store_unit import StoreUnit
from models.user import User
from services.notification_service import create_notification
from datetime import datetime


# Map day abbreviations to Python weekday numbers (0=Mon, 6=Sun)
_DAY_MAP = {'mon': 0, 'tue': 1, 'wed': 2, 'thu': 3, 'fri': 4, 'sat': 5, 'sun': 6}


def _parse_time(s):
    """Parse time strings like '9AM', '10:30AM', '6PM' into (hour, minute)."""
    s = s.strip().upper().replace('.', '')
    m = re.match(r'^(\d{1,2}):?(\d{2})?\s*(AM|PM)$', s)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2) or 0)
    if m.group(3) == 'PM' and hour != 12:
        hour += 12
    elif m.group(3) == 'AM' and hour == 12:
        hour = 0
    return hour * 60 + minute


def check_agent_availability(agent, appt_start, appt_end):
    """Check if the appointment falls within the agent's availability schedule.
    Returns True if available or if schedule can't be parsed. Returns False if outside schedule."""
    schedule = agent.availability_schedule
    if not schedule:
        return True  # no schedule set = always available

    # Parse patterns like "Mon-Fri 9AM-6PM", "Tue-Sat 8AM-5PM", "Mon-Sat 10AM-7PM"
    m = re.match(r'(\w{3})-(\w{3})\s+(.+)-(.+)', schedule.strip(), re.IGNORECASE)
    if not m:
        return True  # can't parse = allow

    day_start = _DAY_MAP.get(m.group(1).lower()[:3])
    day_end = _DAY_MAP.get(m.group(2).lower()[:3])
    time_start = _parse_time(m.group(3))
    time_end = _parse_time(m.group(4))

    if day_start is None or day_end is None or time_start is None or time_end is None:
        return True  # can't parse = allow

    # Check day of week
    appt_day = appt_start.weekday()
    if day_start <= day_end:
        day_ok = day_start <= appt_day <= day_end
    else:
        day_ok = appt_day >= day_start or appt_day <= day_end

    if not day_ok:
        return False

    # Check time range
    start_mins = appt_start.hour * 60 + appt_start.minute
    end_mins = appt_end.hour * 60 + appt_end.minute
    if start_mins < time_start or end_mins > time_end:
        return False

    return True

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')


@appointments_bp.before_app_request
def cleanup_past_appointments():
    """Remove appointments whose end_time has passed."""
    try:
        Appointment.query.filter(Appointment.end_time < datetime.now()).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()


@appointments_bp.route('/')
@login_required
def list_appointments():
    role = get_active_role()
    if role == 'LeasingAgent':
        appointments = Appointment.query.filter_by(agent_id=current_user.user_id).order_by(Appointment.date_time.desc()).all()
    elif role == 'Tenant':
        appointments = Appointment.query.filter_by(tenant_id=current_user.user_id).order_by(Appointment.date_time.desc()).all()
    else:
        appointments = Appointment.query.order_by(Appointment.date_time.desc()).all()

    return render_template('appointments/list.html', appointments=appointments)


@appointments_bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if request.method == 'POST':
        agent_id = int(request.form['agent_id'])
        unit_id = int(request.form['unit_id'])
        date_time = datetime.strptime(request.form['date_time'], '%Y-%m-%dT%H:%M')
        end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')

        # Validate times
        if end_time <= date_time:
            flash('End time must be after start time.', 'danger')
            return redirect(url_for('appointments.schedule'))

        if date_time <= datetime.now():
            flash('Appointment must be scheduled in the future.', 'danger')
            return redirect(url_for('appointments.schedule'))

        tenant_id = current_user.user_id if get_active_role() == 'Tenant' else int(request.form['tenant_id'])

        # Check agent availability schedule
        agent = User.query.get(agent_id)
        if not check_agent_availability(agent, date_time, end_time):
            flash(f'The selected agent is not available at that time. Their schedule is: {agent.availability_schedule}', 'danger')
            return redirect(url_for('appointments.schedule'))

        # Check for double-booking (agent)
        agent_conflict = Appointment.query.filter(
            Appointment.agent_id == agent_id,
            Appointment.status == 'Scheduled',
            Appointment.date_time < end_time,
            Appointment.end_time > date_time
        ).first()

        if agent_conflict:
            flash('The selected agent is already booked during this time.', 'danger')
            return redirect(url_for('appointments.schedule'))

        # Check for double-booking (unit)
        unit_conflict = Appointment.query.filter(
            Appointment.unit_id == unit_id,
            Appointment.status == 'Scheduled',
            Appointment.date_time < end_time,
            Appointment.end_time > date_time
        ).first()

        if unit_conflict:
            flash('This unit already has a viewing scheduled during this time.', 'danger')
            return redirect(url_for('appointments.schedule'))

        try:
            appointment = Appointment(
                agent_id=agent_id,
                tenant_id=tenant_id,
                unit_id=unit_id,
                date_time=date_time,
                end_time=end_time
            )
            db.session.add(appointment)
            db.session.commit()

            unit = StoreUnit.query.get(unit_id)
            create_notification(
                recipient_id=tenant_id,
                notif_type='Appointment Confirmation',
                title='Appointment Confirmed',
                message=f'Your viewing appointment for {unit.location} on {date_time.strftime("%b %d at %I:%M %p")} has been confirmed.',
                related_entity='appointment',
                related_id=appointment.appointment_id
            )

            flash('Appointment scheduled successfully.', 'success')
        except Exception:
            db.session.rollback()
            flash('An error occurred while scheduling the appointment.', 'danger')
        return redirect(url_for('appointments.list_appointments'))

    agents = User.query.filter(
        User.status == 'Active',
        User.role.in_(['LeasingAgent', 'Dev'])
    ).all()
    units = StoreUnit.query.filter_by(availability='Available').all()
    if get_active_role() != 'Tenant':
        tenants = User.query.filter(
            User.status == 'Active',
            User.role.in_(['Tenant', 'Dev'])
        ).all()
    else:
        tenants = []

    return render_template('appointments/schedule.html', agents=agents, units=units, tenants=tenants)


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    try:
        appointment.status = 'Cancelled'
        db.session.commit()

        # Notify tenant and agent about the cancellation
        unit = StoreUnit.query.get(appointment.unit_id)
        agent = User.query.get(appointment.agent_id)
        tenant = User.query.get(appointment.tenant_id)
        appt_time = appointment.date_time.strftime("%b %d at %I:%M %p")

        create_notification(
            recipient_id=appointment.tenant_id,
            notif_type='Appointment Update',
            title='Appointment Cancelled',
            message=f'Your viewing appointment for {unit.location} on {appt_time} has been cancelled.',
            related_entity='appointment',
            related_id=appointment.appointment_id
        )
        create_notification(
            recipient_id=appointment.agent_id,
            notif_type='Appointment Update',
            title='Appointment Cancelled',
            message=f'The viewing appointment with {tenant.name} for {unit.location} on {appt_time} has been cancelled.',
            related_entity='appointment',
            related_id=appointment.appointment_id
        )

        flash('Appointment cancelled.', 'info')
    except Exception:
        db.session.rollback()
        flash('An error occurred while cancelling the appointment.', 'danger')
    return redirect(url_for('appointments.list_appointments'))