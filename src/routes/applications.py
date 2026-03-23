import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from routes import role_required, get_active_role
from models import db
from models.rental_application import RentalApplication
from models.application_document import ApplicationDocument
from models.store_unit import StoreUnit
from models.user import User
from services.notification_service import create_notification
from datetime import date

applications_bp = Blueprint('applications', __name__, url_prefix='/applications')

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@applications_bp.route('/')
@login_required
def list_applications():
    if get_active_role() == 'Tenant':
        applications = RentalApplication.query.filter_by(tenant_id=current_user.user_id).all()
    else:
        applications = RentalApplication.query.all()

    available_units = StoreUnit.query.filter_by(availability='Available').all()
    return render_template('applications/list.html', applications=applications, available_units=available_units)


@applications_bp.route('/submit', methods=['GET', 'POST'])
@login_required
@role_required('Tenant')
def submit():
    if request.method == 'POST':
        unit_id = int(request.form['unit_id'])

        try:
            application = RentalApplication(
                tenant_id=current_user.user_id,
                unit_id=unit_id,
                submission_date=date.today()
            )
            db.session.add(application)
            db.session.commit()

            # Handle file uploads
            files = request.files.getlist('documents')
            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    upload_dir = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        'applications',
                        str(application.application_id)
                    )
                    os.makedirs(upload_dir, exist_ok=True)
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)

                    doc = ApplicationDocument(
                        application_id=application.application_id,
                        file_name=filename,
                        file_path=filepath,
                        file_type=filename.rsplit('.', 1)[1].lower(),
                        file_size=os.path.getsize(filepath)
                    )
                    db.session.add(doc)

            db.session.commit()
            flash('Application submitted successfully.', 'success')
        except Exception:
            db.session.rollback()
            flash('An error occurred while submitting the application.', 'danger')
        return redirect(url_for('applications.list_applications'))

    units = StoreUnit.query.filter_by(availability='Available').all()
    return render_template('applications/submit.html', units=units)


@applications_bp.route('/<int:app_id>/update', methods=['POST'])
@login_required
@role_required('Tenant', 'Admin', 'LeasingAgent')
def update(app_id):
    application = RentalApplication.query.get_or_404(app_id)
    if get_active_role() == 'Tenant' and application.tenant_id != current_user.user_id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('applications.list_applications'))
    if application.status != 'Pending':
        flash('Only pending applications can be updated.', 'warning')
        return redirect(url_for('applications.list_applications'))

    try:
        application.unit_id = int(request.form['unit_id'])
        application.submission_date = date.today()

        # Handle additional file uploads
        files = request.files.getlist('documents')
        for file in files:
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    'applications',
                    str(application.application_id)
                )
                os.makedirs(upload_dir, exist_ok=True)
                filepath = os.path.join(upload_dir, filename)
                file.save(filepath)

                doc = ApplicationDocument(
                    application_id=application.application_id,
                    file_name=filename,
                    file_path=filepath,
                    file_type=filename.rsplit('.', 1)[1].lower(),
                    file_size=os.path.getsize(filepath)
                )
                db.session.add(doc)

        db.session.commit()
        flash('Application updated successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while updating the application.', 'danger')
    return redirect(url_for('applications.list_applications'))


@applications_bp.route('/<int:app_id>/approve', methods=['POST'])
@login_required
@role_required('Admin', 'LeasingAgent')
def approve(app_id):
    application = RentalApplication.query.get_or_404(app_id)
    try:
        application.status = 'Approved'
        db.session.commit()

        unit = StoreUnit.query.get(application.unit_id)
        create_notification(
            recipient_id=application.tenant_id,
            notif_type='General',
            title='Application Approved',
            message=f'Your rental application for {unit.location} has been approved.',
            related_entity='rental_application',
            related_id=application.application_id
        )

        flash('Application approved.', 'success')
    except Exception:
        db.session.rollback()
        flash('An error occurred while approving the application.', 'danger')
    return redirect(url_for('applications.list_applications'))


@applications_bp.route('/<int:app_id>/reject', methods=['POST'])
@login_required
@role_required('Admin', 'LeasingAgent')
def reject(app_id):
    application = RentalApplication.query.get_or_404(app_id)
    try:
        application.status = 'Rejected'
        db.session.commit()

        unit = StoreUnit.query.get(application.unit_id)
        create_notification(
            recipient_id=application.tenant_id,
            notif_type='General',
            title='Application Rejected',
            message=f'Your rental application for {unit.location} has been rejected.',
            related_entity='rental_application',
            related_id=application.application_id
        )

        flash('Application rejected.', 'info')
    except Exception:
        db.session.rollback()
        flash('An error occurred while rejecting the application.', 'danger')
    return redirect(url_for('applications.list_applications'))
@applications_bp.route('/<int:app_id>/document/<int:doc_id>')
@login_required
def download_document(app_id, doc_id):
    from flask import send_file
    application = RentalApplication.query.get_or_404(app_id)
    if get_active_role() == 'Tenant' and application.tenant_id != current_user.user_id:
        flash('Unauthorized.', 'danger')
        return redirect(url_for('applications.list_applications'))
        
    doc = ApplicationDocument.query.get_or_404(doc_id)
    if doc.application_id != app_id:
        flash('Invalid document.', 'danger')
        return redirect(url_for('applications.list_applications'))
        
    if not os.path.exists(doc.file_path):
        flash('File not found on server.', 'danger')
        return redirect(url_for('applications.list_applications'))

    return send_file(doc.file_path, as_attachment=True, download_name=doc.file_name)
