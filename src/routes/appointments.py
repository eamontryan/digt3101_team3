from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from routes import role_required
from models import db
from models.appointment import Appointment
from models.store_unit import StoreUnit
from models.user import User
from services.notification_service import create_notification
from datetime import datetime

appointments_bp = Blueprint('appointments', __name__, url_prefix='/appointments')


@appointments_bp.route('/')
@login_required
def list_appointments():
    if current_user.role == 'LeasingAgent':
        appointments = Appointment.query.filter_by(agent_id=current_user.user_id).order_by(Appointment.date_time.desc()).all()
    elif current_user.role == 'Tenant':
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

        tenant_id = current_user.user_id if current_user.role == 'Tenant' else int(request.form['tenant_id'])

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
        return redirect(url_for('appointments.list_appointments'))

    agents = User.query.filter_by(role='LeasingAgent', status='Active').all()
    units = StoreUnit.query.filter_by(availability='Available').all()
    tenants = User.query.filter_by(role='Tenant', status='Active').all() if current_user.role != 'Tenant' else []

    return render_template('appointments/schedule.html', agents=agents, units=units, tenants=tenants)


@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    appointment.status = 'Cancelled'
    db.session.commit()
    flash('Appointment cancelled.', 'info')
    return redirect(url_for('appointments.list_appointments'))