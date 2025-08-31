from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from flask_login import current_user, login_required, login_user
from werkzeug.utils import secure_filename
from src.models import db, User, Property, PropertyImage, ContactInquiry, UserApplication, AdminLog, State, LocalGovernment, CustomerEmail
import os
import re
from datetime import datetime, timedelta
import uuid
import secrets
import string

admin_bp = Blueprint('admin', __name__)

# Helper function to log admin actions
def log_admin_action(admin_id, action, description=None):
    """Log admin actions for audit trail"""
    try:
        log_entry = AdminLog(
            admin_id=admin_id,
            action=action,
            description=description,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        print(f"Error logging admin action: {e}")

# Helper function to check if user is admin
def is_admin():
    return session.get('user_id') and session.get('is_admin')

def is_master_admin():
    """Check if current user is master admin"""
    user_id = session.get('user_id')
    if not user_id:
        return False
    user = User.query.get(user_id)
    return user and user.is_master()

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def master_admin_required(f):
    def decorated_function(*args, **kwargs):
        if not is_master_admin():
            return jsonify({'error': 'Master admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        # Check if this is master admin login
        master_username = os.environ.get('MASTER_USERNAME')
        master_password = os.environ.get('MASTER_PASSWORD')
        
        if email == master_username and password == master_password:
            # Master admin login
            user = User.query.filter_by(email=email).first()
            if not user:
                # Create master admin user if doesn't exist
                user = User(email=email, is_admin=True, is_master_admin=True)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
            
            session['user_id'] = user.id
            session['is_admin'] = True
            session['is_master_admin'] = True
            session['user_email'] = user.email
            
            log_admin_action(user.id, 'LOGIN', 'Master admin login')
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Master admin login successful'})
            else:
                flash('Master admin login successful', 'success')
                return redirect(url_for('admin.dashboard'))
        else:
            # Regular admin login
            user = User.query.filter_by(email=email, is_admin=True).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['is_admin'] = True
                session['is_master_admin'] = user.is_master()
                session['user_email'] = user.email
                
                log_admin_action(user.id, 'LOGIN', 'Admin login')
                
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Login successful'})
                else:
                    flash('Login successful', 'success')
                    return redirect(url_for('admin.dashboard'))
            else:
                if request.is_json:
                    return jsonify({'error': 'Invalid credentials'}), 401
                else:
                    flash('Invalid credentials', 'error')
                    return render_template('admin/login.html')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def admin_logout():
    user_id = session.get('user_id')
    if user_id:
        log_admin_action(user_id, 'LOGOUT', 'Admin logout')
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin.admin_login'))

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Get summary statistics
    total_properties = Property.query.count()
    active_properties = Property.query.filter_by(status='active').count()
    total_inquiries = ContactInquiry.query.count()
    new_inquiries = ContactInquiry.query.filter_by(status='new').count()
    responded_inquiries = ContactInquiry.query.filter_by(status='responded').count()
    total_applications = UserApplication.query.count()
    pending_applications = UserApplication.query.filter_by(status='pending').count()
    total_admins = User.query.filter_by(is_admin=True).count()
    
    stats = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'total_inquiries': total_inquiries,
        'new_inquiries': new_inquiries,
        'responded_inquiries': responded_inquiries,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'total_admins': total_admins
    }
    
    # Get recent properties
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_properties=recent_properties, is_master=is_master_admin())

# Master Admin Routes
@admin_bp.route('/admins')
@master_admin_required
def list_admins():
    """List all admin users - master admin only"""
    page = request.args.get('page', 1, type=int)
    admins = User.query.filter_by(is_admin=True).order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'admins': [admin.to_dict() for admin in admins.items],
            'total': admins.total,
            'pages': admins.pages,
            'current_page': page
        })
    
    return render_template('admin/admins.html', admins=admins)

@admin_bp.route('/admins', methods=['POST'])
@master_admin_required
def create_admin():
    """Create new admin user - master admin only"""
    data = request.get_json() if request.is_json else request.form
    
    try:
        email = data.get('email')
        password = data.get('password', secrets.token_urlsafe(12))
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'error': 'Email already exists'}), 400
            else:
                flash('Email already exists', 'error')
                return redirect(url_for('admin.list_admins'))
        
        admin = User(
            email=email,
            is_admin=True,
            is_master_admin=False
        )
        admin.set_password(password)
        
        db.session.add(admin)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'CREATE_ADMIN', f'Created admin: {email}')
        
        if request.is_json:
            return jsonify({'success': True, 'admin': admin.to_dict(), 'password': password}), 201
        else:
            flash(f'Admin created successfully. Password: {password}', 'success')
            return redirect(url_for('admin.list_admins'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error creating admin: {str(e)}', 'error')
            return redirect(url_for('admin.list_admins'))

@admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@master_admin_required
def delete_admin(admin_id):
    """Delete admin user - master admin only"""
    admin = User.query.get_or_404(admin_id)
    
    # Prevent deleting master admin
    if admin.is_master():
        if request.is_json:
            return jsonify({'error': 'Cannot delete master admin'}), 400
        else:
            flash('Cannot delete master admin', 'error')
            return redirect(url_for('admin.list_admins'))
    
    try:
        email = admin.email
        db.session.delete(admin)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'DELETE_ADMIN', f'Deleted admin: {email}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Admin deleted successfully'})
        else:
            flash('Admin deleted successfully', 'success')
            return redirect(url_for('admin.list_admins'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error deleting admin: {str(e)}', 'error')
            return redirect(url_for('admin.list_admins'))

@admin_bp.route('/admin-logs')
@master_admin_required
def view_admin_logs():
    """View admin action logs for last 30 days - master admin only"""
    page = request.args.get('page', 1, type=int)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    logs = AdminLog.query.filter(
        AdminLog.created_at >= thirty_days_ago
    ).order_by(AdminLog.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'logs': [log.to_dict() for log in logs.items],
            'total': logs.total,
            'pages': logs.pages,
            'current_page': page
        })
    
    return render_template('admin/admin_logs.html', logs=logs)

@admin_bp.route('/change-password', methods=['GET', 'POST'])
@admin_required
def change_password():
    """Change admin password"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        user = User.query.get(session.get('user_id'))
        
        # For master admin, allow changing password with master credentials
        if user.is_master():
            master_password = os.environ.get('MASTER_PASSWORD')
            if current_password == master_password:
                # Update master password in database
                user.set_password(new_password)
                db.session.commit()
                log_admin_action(user.id, 'CHANGE_PASSWORD', 'Master admin password changed')
                
                if request.is_json:
                    return jsonify({'success': True, 'message': 'Master password changed successfully'})
                else:
                    flash('Master password changed successfully', 'success')
                    return redirect(url_for('admin.dashboard'))
        
        if not user.check_password(current_password):
            if request.is_json:
                return jsonify({'error': 'Current password is incorrect'}), 400
            else:
                flash('Current password is incorrect.', 'error')
        elif new_password != confirm_password:
            if request.is_json:
                return jsonify({'error': 'New passwords do not match'}), 400
            else:
                flash('New passwords do not match.', 'error')
        else:
            user.set_password(new_password)
            db.session.commit()
            log_admin_action(user.id, 'CHANGE_PASSWORD', 'Admin password changed')
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Password changed successfully'})
            else:
                flash('Password changed successfully.', 'success')
                return redirect(url_for('admin.dashboard'))
    
    return render_template('admin/change_password.html', is_master=is_master_admin())

@admin_bp.route('/reset-admin-password', methods=['POST'])
@master_admin_required
def reset_admin_password():
    """Reset another admin's password - master admin only"""
    data = request.get_json() if request.is_json else request.form
    admin_id = data.get('admin_id')
    new_password = data.get('new_password', secrets.token_urlsafe(12))
    
    admin = User.query.get_or_404(admin_id)
    
    if admin.is_master():
        if request.is_json:
            return jsonify({'error': 'Cannot reset master admin password'}), 400
        else:
            flash('Cannot reset master admin password', 'error')
            return redirect(url_for('admin.list_admins'))
    
    try:
        admin.set_password(new_password)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'RESET_ADMIN_PASSWORD', f'Reset password for admin: {admin.email}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Password reset successfully', 'new_password': new_password})
        else:
            flash(f'Password reset successfully. New password: {new_password}', 'success')
            return redirect(url_for('admin.list_admins'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error resetting password: {str(e)}', 'error')
            return redirect(url_for('admin.list_admins'))

# Property Management Routes (existing functionality)
@admin_bp.route('/properties')
@admin_required
def list_properties():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    state_id = request.args.get('state_id', type=int)
    
    query = Property.query
    if search:
        query = query.filter(Property.title.contains(search) | Property.location.contains(search))
    if state_id:
        query = query.filter(Property.state_id == state_id)
    
    properties = query.order_by(Property.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'properties': [prop.to_dict() for prop in properties.items],
            'total': properties.total,
            'pages': properties.pages,
            'current_page': page
        })
    
    # Get states and local governments for dropdowns
    states = State.query.order_by(State.name).all()
    local_governments = LocalGovernment.query.order_by(LocalGovernment.name).all()
    
    return render_template('admin/properties.html', 
                         properties=properties, 
                         search=search,
                         states=states,
                         local_governments=local_governments)

@admin_bp.route('/properties', methods=['POST'])
@admin_required
def create_property():
    data = request.get_json() if request.is_json else request.form
    
    try:
        property = Property(
            title=data.get('title'),
            description=data.get('description'),
            price=float(data.get('price')),
            property_type=data.get('property_type'),
            location=data.get('location'),  # Legacy field
            state_id=int(data.get('state_id')) if data.get('state_id') else None,
            local_government_id=int(data.get('local_government_id')) if data.get('local_government_id') else None,
            bedrooms=int(data.get('bedrooms', 0)),
            bathrooms=int(data.get('bathrooms', 0)),
            area_sqft=float(data.get('area_sqft', 0)),
            status=data.get('status', 'active')
        )
        
        db.session.add(property)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'CREATE_PROPERTY', f'Created property: {property.title}')
        
        if request.is_json:
            return jsonify({'success': True, 'property': property.to_dict()}), 201
        else:
            flash('Property created successfully', 'success')
            return redirect(url_for('admin.list_properties'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error creating property: {str(e)}', 'error')
            return redirect(url_for('admin.list_properties'))

@admin_bp.route('/properties/<int:property_id>')
@admin_required
def get_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    if request.is_json:
        return jsonify(property.to_dict())
    
    # Get states for the edit form
    states = State.query.all()
    return render_template('admin/property_detail.html', property=property, states=states)

@admin_bp.route('/properties/<int:property_id>', methods=['PUT'])
@admin_required
def update_property(property_id):
    property = Property.query.get_or_404(property_id)
    data = request.get_json() if request.is_json else request.form

    print("Update data:", data)
    
    try:
        property.title = data.get('title', property.title)
        property.description = data.get('description', property.description)
        property.price = float(data.get('price', property.price))
        property.property_type = data.get('property_type', property.property_type)
        property.location = data.get('location', property.location)  # Legacy field
        
        # Handle state_id - set to None if empty or null
        state_id = data.get('state_id')
        if state_id and str(state_id).strip():
            property.state_id = int(state_id)
        else:
            property.state_id = None
            
        # Handle local_government_id - set to None if empty or null
        lg_id = data.get('local_government_id')
        if lg_id and str(lg_id).strip():
            property.local_government_id = int(lg_id)
        else:
            property.local_government_id = None
            
        property.bedrooms = int(data.get('bedrooms', property.bedrooms))
        property.bathrooms = int(data.get('bathrooms', property.bathrooms))
        property.area_sqft = float(data.get('area_sqft', property.area_sqft))
        property.status = data.get('status', property.status)
        property.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'UPDATE_PROPERTY', f'Updated property: {property.title}')
        
        if request.is_json:
            return jsonify({'success': True, 'property': property.to_dict()})
        else:
            flash('Property updated successfully', 'success')
            return redirect(url_for('admin.get_property', property_id=property_id))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error updating property: {str(e)}', 'error')
            return redirect(url_for('admin.get_property', property_id=property_id))

@admin_bp.route('/properties/<int:property_id>', methods=['DELETE'])
@admin_required
def delete_property(property_id):
    property = Property.query.get_or_404(property_id)
    
    try:
        # Guard: If there are applications, only allow deletion when property is inactive
        applications_count = UserApplication.query.filter_by(property_id=property.id).count()
        if applications_count > 0 and (property.status or '').lower() != 'inactive':
            message = 'Property can only be deleted when status is Inactive.'
            if request.is_json:
                return jsonify({'error': message}), 400
            else:
                flash(message, 'error')
                return redirect(url_for('admin.get_property', property_id=property.id))
        
        # Delete associated images from filesystem
        for image in property.images:
            image_path = os.path.join('src/static/uploads', image.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # If applications exist (and status is inactive), clean them up to avoid FK constraint
        if applications_count > 0:
            UserApplication.query.filter_by(property_id=property.id).delete(synchronize_session=False)
        
        title = property.title
        db.session.delete(property)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'DELETE_PROPERTY', f'Deleted property: {title}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Property deleted successfully'})
        else:
            flash('Property deleted successfully', 'success')
            return redirect(url_for('admin.list_properties'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error deleting property: {str(e)}', 'error')
            return redirect(url_for('admin.list_properties'))

@admin_bp.route('/inquiries')
@admin_required
def list_inquiries():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = ContactInquiry.query
    if status_filter:
        if status_filter == 'unread':
            # Show both new and read inquiries (exclude responded)
            query = query.filter(ContactInquiry.status.in_(['new', 'read']))
        else:
            query = query.filter_by(status=status_filter)
    
    inquiries = query.order_by(ContactInquiry.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'inquiries': [inquiry.to_dict() for inquiry in inquiries.items],
            'total': inquiries.total,
            'pages': inquiries.pages,
            'current_page': page
        })
    
    return render_template('admin/inquiries.html', inquiries=inquiries, status_filter=status_filter)

@admin_bp.route('/inquiries/<int:inquiry_id>/status', methods=['POST'])
@admin_required
def update_inquiry_status(inquiry_id):
    new_status = request.json.get('status')
    
    if new_status not in ['new', 'read', 'responded']:
        return jsonify({'error': 'Invalid status'}), 400
    
    try:
        inquiry = ContactInquiry.query.get_or_404(inquiry_id)
        old_status = inquiry.status
        inquiry.status = new_status
        db.session.commit()
        
        # Log the status change
        log_admin_action(
            session.get('user_id'),
            'inquiry_status_updated',
            f'Changed inquiry #{inquiry_id} status from {old_status} to {new_status}'
        )
        
        return jsonify({
            'success': True,
            'message': f'Status updated to {new_status}',
            'status': new_status
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/inquiries/<int:inquiry_id>/mark-responded', methods=['POST'])
@admin_required
def mark_inquiry_responded(inquiry_id):
    
    try:
        inquiry = ContactInquiry.query.get_or_404(inquiry_id)
        inquiry.status = 'responded'
        db.session.commit()
        
        # Log the action
        log_admin_action(
            session.get('user_id'),
            'inquiry_responded',
            f'Marked inquiry #{inquiry_id} as responded'
        )
        
        return jsonify({
            'success': True,
            'message': 'Inquiry marked as responded'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/inquiries/<int:inquiry_id>', methods=['DELETE'])
@admin_required
def delete_inquiry(inquiry_id):
    try:
        inquiry = ContactInquiry.query.get_or_404(inquiry_id)
        inquiry_details = f"Name: {inquiry.name}, Email: {inquiry.email}"
        
        db.session.delete(inquiry)
        db.session.commit()
        
        # Log the deletion
        log_admin_action(
            session.get('user_id'),
            'inquiry_deleted',
            f'Deleted inquiry #{inquiry_id} ({inquiry_details})'
        )
        
        return jsonify({
            'success': True,
            'message': 'Inquiry deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/inquiries/<int:inquiry_id>/delete', methods=['POST'])
@admin_required
def delete_inquiry_post(inquiry_id):
    """Alternative delete route using POST method"""
    try:
        inquiry = ContactInquiry.query.get_or_404(inquiry_id)
        inquiry_details = f"Name: {inquiry.name}, Email: {inquiry.email}"
        
        db.session.delete(inquiry)
        db.session.commit()
        
        # Log the deletion
        log_admin_action(
            session.get('user_id'),
            'inquiry_deleted',
            f'Deleted inquiry #{inquiry_id} ({inquiry_details})'
        )
        
        return jsonify({
            'success': True,
            'message': 'Inquiry deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/applications')
@admin_required
def list_applications():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = UserApplication.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    applications = query.order_by(UserApplication.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'applications': [app.to_dict() for app in applications.items],
            'total': applications.total,
            'pages': applications.pages,
            'current_page': page
        })
    
    return render_template('admin/applications.html', applications=applications, status_filter=status_filter)

@admin_bp.route('/applications/<int:application_id>/approve', methods=['PUT','POST'])
@admin_required
def approve_application(application_id):
    """Approve or reject an application"""
    application = UserApplication.query.get_or_404(application_id)
    data = request.get_json(silent=True) or request.form
    
    new_status = (data.get('status') if data else None)
    if new_status not in ['approved', 'rejected']:
        return jsonify({'error': 'Invalid status. Must be approved or rejected'}), 400
    
    try:
        # Update application status
        application.status = new_status
        application.updated_at = datetime.utcnow()
        
        # Log admin action (use session user_id; current_user may be anonymous in admin session auth)
        admin_log = AdminLog(
            admin_id=session.get('user_id'),
            action=f"Application {new_status.title()}",
            description=f"Application ID {application_id} for property '{application.property.title}' by user {application.user.email}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')
        )
        
        db.session.add(admin_log)
        db.session.commit()
        
        # Send email notification to user
        try:
            from src.utils.production_email_service import send_email as _send_email
            user_email = application.user.email
            property_title = application.property.title
            property_location = application.property.get_location_display() if hasattr(application.property, 'get_location_display') else application.property.location
            base_url = request.url_root.rstrip('/')
            if new_status == 'approved':
                subject = f"✅ Your Application for {property_title} Has Been Approved!"
                email_body = f"""
                <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;\">
                    <div style=\"background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);\">
                        <div style=\"text-align: center; margin-bottom: 30px;\">
                            <h1 style=\"color: #28a745; margin: 0;\">🎉 Application Approved!</h1>
                        </div>
                        <p style=\"font-size: 16px; color: #333; line-height: 1.6;\">Dear Valued Customer,</p>
                        <p style=\"font-size: 16px; color: #333; line-height: 1.6;\">Congratulations! Your application for <strong>{property_title}</strong> in <strong>{property_location}</strong> has been <strong style=\"color: #28a745;\">APPROVED</strong>.</p>
                        <p style=\"font-size: 16px; color: #333; line-height: 1.6;\"><strong>Next Steps:</strong> Our agent will reach out within 24-48 hours.</p>
                        <div style=\"text-align: center; margin: 30px 0;\"><a href=\"{base_url}/properties/{application.property_id}\" style=\"background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;\">View Property</a></div>
                        <p style=\"font-size: 14px; color: #666; text-align: center; margin: 0;\">Best regards,<br><strong>Gidamart Team</strong></p>
                    </div>
                </div>
                """
            else:
                subject = f"📋 Update on Your Application for {property_title}"
                email_body = f"""
                <div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8f9fa;\">
                    <div style=\"background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);\">
                        <div style=\"text-align: center; margin-bottom: 30px;\">
                            <h1 style=\"color: #dc3545; margin: 0;\">📋 Application Update</h1>
                        </div>
                        <p style=\"font-size: 16px; color: #333; line-height: 1.6;\">Thank you for your interest in <strong>{property_title}</strong> in <strong>{property_location}</strong>. We are unable to proceed with this application at this time.</p>
                        <p style=\"font-size: 16px; color: #333; line-height: 1.6;\">We encourage you to browse other available properties that might suit your needs.</p>
                        <div style=\"text-align: center; margin: 30px 0;\"><a href=\"{base_url}/properties\" style=\"background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold;\">View More Properties</a></div>
                        <p style=\"font-size: 14px; color: #666; text-align: center; margin: 0;\">Best regards,<br><strong>Gidamart Team</strong></p>
                    </div>
                </div>
                """
            _send_email(to_email=user_email, subject=subject, body=email_body, is_html=True)
        except Exception as email_error:
            print(f"Error sending email notification: {str(email_error)}")
            pass
        
        return jsonify({
            'success': True,
            'message': f'Application {new_status} successfully',
            'application': application.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error updating application: {str(e)}'}), 500

@admin_bp.route('/properties/<int:property_id>/images', methods=['POST'])
@admin_required
def upload_property_images(property_id):
    property = Property.query.get_or_404(property_id)
    
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400
    
    files = request.files.getlist('images')
    uploaded_images = []
    errors = []
    
    try:
        from src.utils.image_processing import process_uploaded_image
        
        for file in files:
            if file and file.filename:
                # Process the image (handles HEIC conversion automatically)
                result = process_uploaded_image(
                    file=file,
                    upload_folder=current_app.config['UPLOAD_FOLDER'],
                    max_size=(1920, 1080),  # Reasonable max size for web
                    quality=85
                )
                
                if result['success']:
                    # Create database record
                    image = PropertyImage(
                        property_id=property_id,
                        image_filename=result['filename'],
                        is_primary=len(property.images) == 0,  # First image is primary
                        upload_order=len(property.images)
                    )
                    
                    db.session.add(image)
                    uploaded_images.append(image)
                    
                    print(f"✅ Uploaded {file.filename} -> {result['filename']} "
                          f"(Original: {result['original_format']}, "
                          f"Converted: {result['converted']})")
                else:
                    errors.append(f"{file.filename}: {result['error']}")
                    print(f"❌ Failed to upload {file.filename}: {result['error']}")
        
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'UPLOAD_IMAGES', 
                        f'Uploaded {len(uploaded_images)} images for property: {property.title}')
        
        # Prepare response
        response_data = {
            'success': True,
            'message': f'{len(uploaded_images)} images uploaded successfully',
            'images': [img.to_dict() for img in uploaded_images]
        }
        
        if errors:
            response_data['warnings'] = errors
            response_data['message'] += f' ({len(errors)} files had errors)'
        
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/images/<int:image_id>', methods=['DELETE'])
@admin_required
def delete_property_image(image_id):
    image = PropertyImage.query.get_or_404(image_id)
    
    try:
        # Delete file from filesystem
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image.image_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # If this was the primary image, make another image primary
        if image.is_primary and image.property.images:
            next_image = PropertyImage.query.filter(
                PropertyImage.property_id == image.property_id,
                PropertyImage.id != image.id
            ).first()
            if next_image:
                next_image.is_primary = True
        
        db.session.delete(image)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'DELETE_IMAGE', f'Deleted image for property: {image.property.title}')
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/images/<int:image_id>/primary', methods=['PUT'])
@admin_required
def set_primary_image(image_id):
    image = PropertyImage.query.get_or_404(image_id)
    
    try:
        # Remove primary status from other images
        PropertyImage.query.filter_by(property_id=image.property_id).update({'is_primary': False})
        
        # Set this image as primary
        image.is_primary = True
        
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'SET_PRIMARY_IMAGE', f'Set primary image for property: {image.property.title}')
        
        return jsonify({'success': True, 'message': 'Primary image updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/properties/<int:property_id>/json')
@admin_required
def get_property_json(property_id):
    property = Property.query.get_or_404(property_id)
    return jsonify({
        "id": property.id,
        "title": property.title,
        "property_type": property.property_type,
        "description": property.description,
        "price": property.price,
        "location": property.location,
        "state_id": property.state_id,
        "local_government_id": property.local_government_id,
        "bedrooms": property.bedrooms,
        "bathrooms": property.bathrooms,
        "area_sqft": property.area_sqft,
        "status": property.status
    })

# Location Management Routes
@admin_bp.route('/states')
@admin_required
def list_states():
    """List all states"""
    states = State.query.order_by(State.name).all()
    
    if request.is_json:
        return jsonify({
            'states': [state.to_dict() for state in states]
        })
    
    return render_template('admin/states.html', states=states)

@admin_bp.route('/api/states/<int:state_id>/local-governments')
@admin_required
def get_local_governments_by_state(state_id):
    """Get local governments for a specific state"""
    try:
        local_governments = LocalGovernment.query.filter_by(state_id=state_id).order_by(LocalGovernment.name).all()
        return jsonify({
            'success': True,
            'local_governments': [lg.to_dict() for lg in local_governments]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@admin_bp.route('/states', methods=['POST'])
@master_admin_required
def create_state():
    """Create new state - master admin only"""
    data = request.get_json() if request.is_json else request.form
    
    try:
        name = data.get('name')
        code = data.get('code')
        
        if State.query.filter_by(name=name).first():
            if request.is_json:
                return jsonify({'error': 'State name already exists'}), 400
            else:
                flash('State name already exists', 'error')
                return redirect(url_for('admin.list_states'))
        
        if State.query.filter_by(code=code).first():
            if request.is_json:
                return jsonify({'error': 'State code already exists'}), 400
            else:
                flash('State code already exists', 'error')
                return redirect(url_for('admin.list_states'))
        
        state = State(name=name, code=code)
        db.session.add(state)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'CREATE_STATE', f'Created state: {name}')
        
        if request.is_json:
            return jsonify({'success': True, 'state': state.to_dict()}), 201
        else:
            flash('State created successfully', 'success')
            return redirect(url_for('admin.list_states'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error creating state: {str(e)}', 'error')
            return redirect(url_for('admin.list_states'))

@admin_bp.route('/states/<int:state_id>', methods=['PUT'])
@master_admin_required
def update_state(state_id):
    """Update state - master admin only"""
    state = State.query.get_or_404(state_id)
    data = request.get_json() if request.is_json else request.form
    
    try:
        name = data.get('name')
        code = data.get('code')
        
        # Check if another state has the same name
        existing_name = State.query.filter(State.name == name, State.id != state_id).first()
        if existing_name:
            if request.is_json:
                return jsonify({'error': 'State name already exists'}), 400
            else:
                flash('State name already exists', 'error')
                return redirect(url_for('admin.list_states'))
        
        # Check if another state has the same code
        existing_code = State.query.filter(State.code == code, State.id != state_id).first()
        if existing_code:
            if request.is_json:
                return jsonify({'error': 'State code already exists'}), 400
            else:
                flash('State code already exists', 'error')
                return redirect(url_for('admin.list_states'))
        
        state.name = name
        state.code = code
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'UPDATE_STATE', f'Updated state: {name}')
        
        if request.is_json:
            return jsonify({'success': True, 'state': state.to_dict()})
        else:
            flash('State updated successfully', 'success')
            return redirect(url_for('admin.list_states'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error updating state: {str(e)}', 'error')
            return redirect(url_for('admin.list_states'))

@admin_bp.route('/states/<int:state_id>', methods=['DELETE'])
@master_admin_required
def delete_state(state_id):
    """Delete state - master admin only"""
    state = State.query.get_or_404(state_id)
    
    try:
        name = state.name
        
        # Check if state has local governments
        if state.local_governments:
            if request.is_json:
                return jsonify({'error': 'Cannot delete state with local governments. Delete local governments first.'}), 400
            else:
                flash('Cannot delete state with local governments. Delete local governments first.', 'error')
                return redirect(url_for('admin.list_states'))
        
        db.session.delete(state)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'DELETE_STATE', f'Deleted state: {name}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'State deleted successfully'})
        else:
            flash('State deleted successfully', 'success')
            return redirect(url_for('admin.list_states'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error deleting state: {str(e)}', 'error')
            return redirect(url_for('admin.list_states'))

@admin_bp.route('/local-governments/<int:lg_id>', methods=['PUT'])
@master_admin_required
def update_local_government(lg_id):
    """Update local government - master admin only"""
    lg = LocalGovernment.query.get_or_404(lg_id)
    data = request.get_json() if request.is_json else request.form
    
    try:
        name = data.get('name')
        state_id = int(data.get('state_id'))
        
        state = State.query.get_or_404(state_id)
        
        # Check if another LG has the same name in the same state
        existing_lg = LocalGovernment.query.filter(
            LocalGovernment.name == name, 
            LocalGovernment.state_id == state_id,
            LocalGovernment.id != lg_id
        ).first()
        if existing_lg:
            if request.is_json:
                return jsonify({'error': 'Local government already exists in this state'}), 400
            else:
                flash('Local government already exists in this state', 'error')
                return redirect(url_for('admin.list_local_governments'))
        
        lg.name = name
        lg.state_id = state_id
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'UPDATE_LOCAL_GOVERNMENT', f'Updated local government: {name} in {state.name}')
        
        if request.is_json:
            return jsonify({'success': True, 'local_government': lg.to_dict()})
        else:
            flash('Local government updated successfully', 'success')
            return redirect(url_for('admin.list_local_governments'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error updating local government: {str(e)}', 'error')
            return redirect(url_for('admin.list_local_governments'))

@admin_bp.route('/local-governments/<int:lg_id>', methods=['DELETE'])
@master_admin_required
def delete_local_government(lg_id):
    """Delete local government - master admin only"""
    lg = LocalGovernment.query.get_or_404(lg_id)
    
    try:
        name = lg.name
        state_name = lg.state.name
        
        db.session.delete(lg)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'DELETE_LOCAL_GOVERNMENT', f'Deleted local government: {name} from {state_name}')
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Local government deleted successfully'})
        else:
            flash('Local government deleted successfully', 'success')
            return redirect(url_for('admin.list_local_governments'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error deleting local government: {str(e)}', 'error')
            return redirect(url_for('admin.list_local_governments'))

@admin_bp.route('/local-governments')
@admin_required
def list_local_governments():
    """List all local governments"""
    state_id = request.args.get('state_id', type=int)
    
    query = LocalGovernment.query
    if state_id:
        query = query.filter_by(state_id=state_id)
    
    local_governments = query.order_by(LocalGovernment.name).all()
    
    if request.is_json:
        return jsonify({
            'local_governments': [lg.to_dict() for lg in local_governments]
        })
    
    states = State.query.order_by(State.name).all()
    return render_template('admin/local_governments.html', 
                         local_governments=local_governments, 
                         states=states, 
                         selected_state_id=state_id)

@admin_bp.route('/local-governments', methods=['POST'])
@master_admin_required
def create_local_government():
    """Create new local government - master admin only"""
    data = request.get_json() if request.is_json else request.form
    
    try:
        name = data.get('name')
        state_id = int(data.get('state_id'))
        
        state = State.query.get_or_404(state_id)
        
        if LocalGovernment.query.filter_by(name=name, state_id=state_id).first():
            if request.is_json:
                return jsonify({'error': 'Local government already exists in this state'}), 400
            else:
                flash('Local government already exists in this state', 'error')
                return redirect(url_for('admin.list_local_governments'))
        
        lg = LocalGovernment(name=name, state_id=state_id)
        db.session.add(lg)
        db.session.commit()
        
        log_admin_action(session.get('user_id'), 'CREATE_LOCAL_GOVERNMENT', f'Created local government: {name} in {state.name}')
        
        if request.is_json:
            return jsonify({'success': True, 'local_government': lg.to_dict()}), 201
        else:
            flash('Local government created successfully', 'success')
            return redirect(url_for('admin.list_local_governments'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error creating local government: {str(e)}', 'error')
            return redirect(url_for('admin.list_local_governments'))

# Newsletter Management Routes
@admin_bp.route('/newsletter/customers')
@admin_required
def list_newsletter_customers():
    """List all newsletter subscribers"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = CustomerEmail.query.filter_by(is_active=True)
    if search:
        query = query.filter(CustomerEmail.email.contains(search))
    
    customers = query.order_by(CustomerEmail.subscribed_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    if request.is_json:
        return jsonify({
            'customers': [customer.to_dict() for customer in customers.items],
            'total': customers.total,
            'pages': customers.pages,
            'current_page': page
        })
    
    # Get total count for display
    total_subscribers = CustomerEmail.query.filter_by(is_active=True).count()
    
    return render_template('admin/newsletter_customers.html', 
                         customers=customers, 
                         total_subscribers=total_subscribers,
                         search=search)

@admin_bp.route('/newsletter/sync-inquiry-emails', methods=['POST'])
@admin_required
def sync_inquiry_emails():
    """Sync all inquiry form emails with newsletter subscription to CustomerEmail table"""
    try:
        # Find all contact inquiries that opted for newsletter but aren't in CustomerEmail
        inquiries_with_newsletter = ContactInquiry.query.filter_by(subscribe_newsletter=True).all()
        
        added_count = 0
        reactivated_count = 0
        
        for inquiry in inquiries_with_newsletter:
            email = inquiry.email
            
            # Check if email already exists in CustomerEmail table
            existing_customer = CustomerEmail.query.filter_by(email=email).first()
            
            if not existing_customer:
                # Add new subscriber
                customer_email = CustomerEmail(
                    email=email,
                    source='inquiry_form'
                )
                db.session.add(customer_email)
                added_count += 1
            elif not existing_customer.is_active:
                # Reactivate if they were unsubscribed
                existing_customer.is_active = True
                reactivated_count += 1
        
        db.session.commit()
        
        # Log the sync action
        log_admin_action(
            session.get('user_id'),
            'NEWSLETTER_SYNC',
            f'Synced inquiry emails: {added_count} added, {reactivated_count} reactivated'
        )
        
        message = f'Successfully synced! Added {added_count} new subscribers, reactivated {reactivated_count} subscribers.'
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': message,
                'added_count': added_count,
                'reactivated_count': reactivated_count
            })
        else:
            flash(message, 'success')
            return redirect(url_for('admin.list_newsletter_customers'))
            
    except Exception as e:
        db.session.rollback()
        error_msg = f'Error syncing inquiry emails: {str(e)}'
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('admin.list_newsletter_customers'))

@admin_bp.route('/newsletter/send', methods=['GET', 'POST'])
@admin_required
def send_newsletter():
    """Send newsletter to all subscribers"""
    if request.method == 'POST':
        # Check if this is an AJAX request (JavaScript form submission)
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        data = request.get_json() if request.is_json else request.form
        
        newsletter_type = data.get('newsletter_type', '').strip()
        subject = data.get('subject', '').strip()
        
        print(f"🔧 Newsletter send attempt - Type: {newsletter_type}, Subject: {subject}")
        print(f"🔧 Form data received: {dict(data)}")
        print(f"🔧 Is AJAX request: {is_ajax}, Is JSON: {request.is_json}")
        
        if not newsletter_type:
            error_msg = 'Newsletter type is required'
            print(f"❌ Error: {error_msg}")
            if is_ajax:
                return jsonify({'error': error_msg}), 400
            else:
                flash(error_msg, 'error')
                return redirect(url_for('admin.send_newsletter'))
        
        try:
            # Get active subscribers based on newsletter type preferences
            if newsletter_type == 'custom':
                # For custom newsletters, send to all active subscribers
                subscribers = CustomerEmail.query.filter_by(is_active=True).all()
            else:
                # For specific newsletter types, filter by user preferences
                from src.models import User, db
                
                # Query to get subscribers who want this specific newsletter type
                if newsletter_type == 'weekly':
                    # Get subscribers who want weekly newsletters
                    subscribers = db.session.query(CustomerEmail).join(
                        User, CustomerEmail.email == User.email
                    ).filter(
                        CustomerEmail.is_active == True,
                        User.newsletter_subscribed == True,
                        User.weekly_newsletter == True
                    ).all()
                elif newsletter_type == 'monthly':
                    subscribers = db.session.query(CustomerEmail).join(
                        User, CustomerEmail.email == User.email
                    ).filter(
                        CustomerEmail.is_active == True,
                        User.newsletter_subscribed == True,
                        User.monthly_newsletter == True
                    ).all()
                elif newsletter_type == 'quarterly':
                    subscribers = db.session.query(CustomerEmail).join(
                        User, CustomerEmail.email == User.email
                    ).filter(
                        CustomerEmail.is_active == True,
                        User.newsletter_subscribed == True,
                        User.quarterly_newsletter == True
                    ).all()
                elif newsletter_type == 'yearly':
                    subscribers = db.session.query(CustomerEmail).join(
                        User, CustomerEmail.email == User.email
                    ).filter(
                        CustomerEmail.is_active == True,
                        User.newsletter_subscribed == True,
                        User.yearly_newsletter == True
                    ).all()
                else:
                    # Fallback to all active subscribers for unknown types
                    subscribers = CustomerEmail.query.filter_by(is_active=True).all()
                
                # Also include subscribers who don't have user accounts but opted in
                # These are subscribers from contact forms without user accounts
                non_user_subscribers = CustomerEmail.query.filter_by(is_active=True).filter(
                    ~CustomerEmail.email.in_(
                        db.session.query(User.email).filter(User.newsletter_subscribed == True)
                    )
                ).all()
                
                # Add non-user subscribers based on their CustomerEmail preferences
                for subscriber in non_user_subscribers:
                    if newsletter_type == 'weekly' and subscriber.weekly_subscription:
                        subscribers.append(subscriber)
                    elif newsletter_type == 'monthly' and subscriber.monthly_subscription:
                        subscribers.append(subscriber)
                    elif newsletter_type == 'quarterly' and subscriber.quarterly_subscription:
                        subscribers.append(subscriber)
                    elif newsletter_type == 'yearly' and subscriber.yearly_subscription:
                        subscribers.append(subscriber)
                
                # Remove duplicates
                seen_emails = set()
                unique_subscribers = []
                for subscriber in subscribers:
                    if subscriber.email not in seen_emails:
                        seen_emails.add(subscriber.email)
                        unique_subscribers.append(subscriber)
                subscribers = unique_subscribers
            
            print(f"👥 Found {len(subscribers)} active subscribers for newsletter")
            
            if not subscribers:
                error_msg = 'No active subscribers found'
                print(f"❌ Error: {error_msg}")
                if is_ajax:
                    return jsonify({'error': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return redirect(url_for('admin.send_newsletter'))
            
            # Create email list
            recipient_emails = [subscriber.email for subscriber in subscribers]
            print(f"📧 Recipient emails: {recipient_emails[:3]}{'...' if len(recipient_emails) > 3 else ''}")
            
            # Import the email service
            from src.utils.email_service import email_service
            print(f"📧 Email service loaded - From: {email_service.newsletter_from_email}")
            
            if newsletter_type == 'custom':
                # Custom newsletter - use provided subject and message
                message = data.get('message', '').strip()
                print(f"📝 Custom newsletter - Subject: '{subject}', Message length: {len(message)}")
                
                if not subject or not message:
                    error_msg = 'Subject and message are required for custom newsletters'
                    print(f"❌ Error: {error_msg}")
                    if is_ajax:
                        return jsonify({'error': error_msg}), 400
                    else:
                        flash(error_msg, 'error')
                        return redirect(url_for('admin.send_newsletter'))
                
                # Send custom newsletter
                print("🚀 Sending custom newsletter...")
                results = email_service.send_bulk_emails(
                    recipients=recipient_emails,
                    subject=subject,
                    body=message,
                    is_html=True,
                    from_email=email_service.newsletter_from_email
                )
                print(f"📊 Custom newsletter results: {results}")
            else:
                # Template-based newsletter
                print(f"📄 Template-based newsletter: {newsletter_type}")
                
                # Prepare template data
                template_data = {}
                
                # Add custom message if provided
                custom_message = data.get('custom_message', '').strip()
                if custom_message:
                    template_data['custom_message'] = custom_message
                    print(f"💬 Custom message added: {custom_message[:50]}...")
                
                # Get featured properties if specified
                featured_property_ids = data.get('featured_properties', '').strip()
                if featured_property_ids:
                    try:
                        property_ids = [int(id.strip()) for id in featured_property_ids.split(',') if id.strip()]
                        featured_properties = Property.query.filter(Property.id.in_(property_ids)).all()
                        template_data['featured_properties'] = featured_properties
                        print(f"🏠 Featured properties: {len(featured_properties)} properties")
                    except ValueError as ve:
                        print(f"⚠️ Invalid property IDs ignored: {ve}")
                
                # Add some basic statistics
                total_properties = Property.query.filter_by(status='active').count()
                template_data.update({
                    'total_properties': total_properties,
                    'new_properties_count': Property.query.filter_by(status='active').limit(5).count(),
                })
                print(f"📊 Template data prepared: {template_data}")
                
                # Send template-based newsletter
                print(f"🚀 Sending {newsletter_type} newsletter to {len(recipient_emails)} recipients")
                
                results = email_service.send_newsletter(
                    recipients=recipient_emails,
                    newsletter_type=newsletter_type,
                    template_data=template_data
                )
                
                print(f"📊 Template newsletter results: {results}")
            
            # Check results and respond accordingly
            success_count = results.get('success_count', 0)
            failed_count = results.get('failed_count', 0)
            
            print(f"📈 Final results - Success: {success_count}, Failed: {failed_count}")
            
            # Log the newsletter send
            log_admin_action(
                session.get('user_id'),
                'NEWSLETTER_SENT',
                f'Sent {newsletter_type} newsletter to {success_count} subscribers (failed: {failed_count})'
            )
            
            if success_count > 0:
                success_message = f'Newsletter sent successfully to {success_count} subscribers!'
                if failed_count > 0:
                    success_message += f' ({failed_count} failed)'
                
                print(f"✅ Success: {success_message}")
                
                if is_ajax:
                    return jsonify({
                        'success': True,
                        'message': success_message,
                        'recipient_count': success_count,
                        'failed_count': failed_count
                    })
                else:
                    flash(success_message, 'success')
                    return redirect(url_for('admin.list_newsletter_customers'))
            else:
                error_message = f'Failed to send newsletter. {failed_count} failed attempts.'
                if 'error' in results:
                    error_message += f' Error: {results["error"]}'
                
                print(f"❌ Complete failure: {error_message}")
                
                if is_ajax:
                    return jsonify({'error': error_message}), 500
                else:
                    flash(error_message, 'error')
                    return redirect(url_for('admin.send_newsletter'))
                
        except Exception as e:
            db.session.rollback()
            error_message = f'Error sending newsletter: {str(e)}'
            print(f"❌ Exception in send_newsletter: {error_message}")
            import traceback
            traceback.print_exc()
            
            if is_ajax:
                return jsonify({'error': error_message}), 500
            else:
                flash(error_message, 'error')
                return redirect(url_for('admin.send_newsletter'))
    
    # GET request - show the form
    total_subscribers = CustomerEmail.query.filter_by(is_active=True).count()
    return render_template('admin/send_newsletter.html', total_subscribers=total_subscribers)

@admin_bp.route('/newsletter/customers/<int:customer_id>/unsubscribe', methods=['POST'])
@admin_required
def unsubscribe_customer(customer_id):
    """Unsubscribe a customer from the newsletter"""
    try:
        customer = CustomerEmail.query.get_or_404(customer_id)
        customer.is_active = False
        db.session.commit()
        
        log_admin_action(
            session.get('user_id'),
            'CUSTOMER_UNSUBSCRIBED',
            f'Unsubscribed customer: {customer.email}'
        )
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Customer unsubscribed successfully'
            })
        else:
            flash('Customer unsubscribed successfully', 'success')
            return redirect(url_for('admin.list_newsletter_customers'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error unsubscribing customer: {str(e)}', 'error')
            return redirect(url_for('admin.list_newsletter_customers'))

@admin_bp.route('/newsletter/customers/<int:customer_id>/resubscribe', methods=['POST'])
@admin_required
def resubscribe_customer(customer_id):
    """Resubscribe a customer to the newsletter"""
    try:
        customer = CustomerEmail.query.get_or_404(customer_id)
        customer.is_active = True
        db.session.commit()
        
        log_admin_action(
            session.get('user_id'),
            'CUSTOMER_RESUBSCRIBED',
            f'Resubscribed customer: {customer.email}'
        )
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Customer resubscribed successfully'
            })
        else:
            flash('Customer resubscribed successfully', 'success')
            return redirect(url_for('admin.list_newsletter_customers'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error resubscribing customer: {str(e)}', 'error')
            return redirect(url_for('admin.list_newsletter_customers'))

@admin_bp.route('/newsletter/customers/<int:customer_id>', methods=['DELETE'])
@admin_required
def delete_newsletter_customer(customer_id):
    """Permanently delete a customer email"""
    try:
        customer = CustomerEmail.query.get_or_404(customer_id)
        email = customer.email
        
        db.session.delete(customer)
        db.session.commit()
        
        log_admin_action(
            session.get('user_id'),
            'CUSTOMER_EMAIL_DELETED',
            f'Deleted customer email: {email}'
        )
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Customer email deleted successfully'
            })
        else:
            flash('Customer email deleted successfully', 'success')
            return redirect(url_for('admin.list_newsletter_customers'))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error deleting customer email: {str(e)}', 'error')
            return redirect(url_for('admin.list_newsletter_customers'))

@admin_bp.route('/newsletter/customers/<int:customer_id>/preferences', methods=['GET', 'POST'])
@admin_required
def customer_preferences(customer_id):
    """Get or update customer newsletter preferences"""
    customer = CustomerEmail.query.get_or_404(customer_id)
    
    if request.method == 'GET':
        return jsonify({
            'success': True,
            'customer': {
                'id': customer.id,
                'email': customer.email,
                'weekly_subscription': customer.weekly_subscription,
                'monthly_subscription': customer.monthly_subscription,
                'quarterly_subscription': customer.quarterly_subscription,
                'yearly_subscription': customer.yearly_subscription
            }
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            # Update preferences
            customer.weekly_subscription = data.get('weekly_subscription', False)
            customer.monthly_subscription = data.get('monthly_subscription', False)
            customer.quarterly_subscription = data.get('quarterly_subscription', False)
            customer.yearly_subscription = data.get('yearly_subscription', False)
            
            db.session.commit()
            
            log_admin_action(
                session.get('user_id'),
                'CUSTOMER_PREFERENCES_UPDATED',
                f'Updated preferences for {customer.email}: W:{customer.weekly_subscription}, M:{customer.monthly_subscription}, Q:{customer.quarterly_subscription}, Y:{customer.yearly_subscription}'
            )
            
            return jsonify({
                'success': True,
                'message': 'Preferences updated successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@admin_bp.route('/newsletter/customers/add', methods=['POST'])
@admin_required
def add_newsletter_customer():
    """Manually add a customer to the newsletter"""
    data = request.get_json() if request.is_json else request.form
    
    email = data.get('email', '').strip().lower()
    
    if not email:
        if request.is_json:
            return jsonify({'error': 'Email is required'}), 400
        else:
            flash('Email is required', 'error')
            return redirect(url_for('admin.list_newsletter_customers'))
    
    # Validate email format
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        if request.is_json:
            return jsonify({'error': 'Please enter a valid email address'}), 400
        else:
            flash('Please enter a valid email address', 'error')
            return redirect(url_for('admin.list_newsletter_customers'))
    
    try:
        # Check if email already exists
        existing_customer = CustomerEmail.query.filter_by(email=email).first()
        
        if existing_customer:
            if existing_customer.is_active:
                if request.is_json:
                    return jsonify({'error': 'Email is already subscribed to the newsletter'}), 400
                else:
                    flash('Email is already subscribed to the newsletter', 'warning')
                    return redirect(url_for('admin.list_newsletter_customers'))
            else:
                # Reactivate existing inactive subscription
                existing_customer.is_active = True
                existing_customer.subscribed_at = datetime.utcnow()
                db.session.commit()
                
                log_admin_action(
                    session.get('user_id'),
                    'CUSTOMER_MANUALLY_RESUBSCRIBED',
                    f'Manually reactivated newsletter subscription for: {email}'
                )
                
                if request.is_json:
                    return jsonify({
                        'success': True,
                        'message': 'Email subscription reactivated successfully',
                        'customer': existing_customer.to_dict()
                    })
                else:
                    flash('Email subscription reactivated successfully', 'success')
                    return redirect(url_for('admin.list_newsletter_customers'))
        else:
            # Create new subscription
            new_customer = CustomerEmail(
                email=email,
                source='admin_manual',
                is_active=True
            )
            
            db.session.add(new_customer)
            db.session.commit()
            
            log_admin_action(
                session.get('user_id'),
                'CUSTOMER_MANUALLY_ADDED',
                f'Manually added newsletter subscriber: {email}'
            )
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Email added to newsletter successfully',
                    'customer': new_customer.to_dict()
                })
            else:
                flash('Email added to newsletter successfully', 'success')
                return redirect(url_for('admin.list_newsletter_customers'))
                
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Error adding email to newsletter: {str(e)}', 'error')
            return redirect(url_for('admin.list_newsletter_customers'))

@admin_bp.route('/debug/email-test')
@admin_required
def debug_email_test():
    """Debug email functionality - accessible via admin panel"""
    
    try:
        from src.utils.email_service import EmailService
        import smtplib
        import os
        
        # Collect debug information
        debug_info = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'smtp_config': {
                'server': os.environ.get('SMTP_SERVER', 'NOT SET'),
                'port': os.environ.get('SMTP_PORT', 'NOT SET'),
                'username': os.environ.get('SMTP_USERNAME', 'NOT SET'),
                'password_set': bool(os.environ.get('SMTP_PASSWORD')),
                'from_email': os.environ.get('FROM_EMAIL', 'NOT SET')
            },
            'tests': []
        }
        
        # Test 1: SMTP Connection
        smtp_test = {'name': 'SMTP Connection', 'status': 'FAILED', 'details': []}
        
        try:
            smtp_server = os.environ.get('SMTP_SERVER')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            
            if not smtp_username or not smtp_password:
                smtp_test['details'].append('SMTP credentials not configured')
                debug_info['tests'].append(smtp_test)
                return render_template('admin/email_debug.html', debug_info=debug_info)
            
            # Test SMTP connection
            smtp_test['details'].append(f'Connecting to {smtp_server}:{smtp_port}...')
            server = smtplib.SMTP(smtp_server, smtp_port)
            smtp_test['details'].append('✅ SMTP connection established')
            
            server.starttls()
            smtp_test['details'].append('✅ TLS enabled')
            
            server.login(smtp_username, smtp_password)
            smtp_test['details'].append('✅ SMTP authentication successful')
            
            server.quit()
            smtp_test['details'].append('✅ SMTP test completed')
            smtp_test['status'] = 'PASSED'
            
        except Exception as e:
            smtp_test['details'].append(f'❌ SMTP Error: {str(e)}')
            
        debug_info['tests'].append(smtp_test)
        
        # Test 2: Email Service
        email_test = {'name': 'Email Service', 'status': 'FAILED', 'details': []}
        
        try:
            email_service = EmailService()
            email_test['details'].append('✅ EmailService instantiated')
            
            # Try sending test email
            result = email_service.send_email(
                to_email=smtp_username,
                subject="Gidamart Email Test",
                body="This is a test email from the debug function.",
                is_html=False
            )
            
            if result:
                email_test['details'].append('✅ Test email sent successfully')
                email_test['status'] = 'PASSED'
            else:
                email_test['details'].append('❌ Test email failed')
                
        except Exception as e:
            email_test['details'].append(f'❌ Email Service Error: {str(e)}')
            
        debug_info['tests'].append(email_test)
        
        # Test 3: Newsletter Service
        newsletter_test = {'name': 'Newsletter Service', 'status': 'FAILED', 'details': []}
        
        try:
            email_service = EmailService()
            
            results = email_service.send_newsletter(
                recipients=[smtp_username],
                newsletter_type="weekly",
                template_data={"test_mode": True}
            )
            
            newsletter_test['details'].append(f'Newsletter results: {results}')
            
            if results.get('success_count', 0) > 0:
                newsletter_test['details'].append('✅ Newsletter test successful')
                newsletter_test['status'] = 'PASSED'
            else:
                newsletter_test['details'].append('❌ Newsletter test failed')
                if 'error' in results:
                    newsletter_test['details'].append(f'Error: {results["error"]}')
                    
        except Exception as e:
            newsletter_test['details'].append(f'❌ Newsletter Error: {str(e)}')
            
        # Test 4: Single Newsletter Email Test (Like Password Reset)
        single_newsletter_test = {'name': 'Single Newsletter Email', 'status': 'FAILED', 'details': []}
        
        try:
            email_service = EmailService()
            
            # Test sending newsletter to just one recipient (like password reset)
            single_newsletter_test['details'].append('Testing single newsletter email...')
            
            results = email_service.send_newsletter(
                recipients=[smtp_username],  # Single recipient like password reset
                newsletter_type="weekly",
                template_data={"test_mode": True}
            )
            
            single_newsletter_test['details'].append(f'Single newsletter results: {results}')
            
            if results.get('success_count', 0) > 0:
                single_newsletter_test['details'].append('✅ Single newsletter test successful')
                single_newsletter_test['status'] = 'PASSED'
            else:
                single_newsletter_test['details'].append('❌ Single newsletter test failed')
                if 'error' in results:
                    single_newsletter_test['details'].append(f'Error: {results["error"]}')
                    
        except Exception as e:
            single_newsletter_test['details'].append(f'❌ Single Newsletter Error: {str(e)}')
            
        debug_info['tests'].append(single_newsletter_test)
        
        # Test 5: Check Subscriber Count
        subscriber_test = {'name': 'Subscriber Analysis', 'status': 'INFO', 'details': []}
        
        try:
            from src.models import CustomerEmail
            
            total_subscribers = CustomerEmail.query.filter_by(is_active=True).count()
            all_subscribers = CustomerEmail.query.all()
            
            subscriber_test['details'].append(f'Total active subscribers: {total_subscribers}')
            subscriber_test['details'].append(f'Total all subscribers: {len(all_subscribers)}')
            
            # Show first few subscriber emails for verification
            active_subscribers = CustomerEmail.query.filter_by(is_active=True).limit(5).all()
            subscriber_test['details'].append('First 5 active subscribers:')
            for sub in active_subscribers:
                subscriber_test['details'].append(f'  - {sub.email} (Active: {sub.is_active})')
            
            if total_subscribers == 0:
                subscriber_test['details'].append('❌ No active subscribers found!')
                subscriber_test['status'] = 'FAILED'
            else:
                subscriber_test['details'].append('✅ Subscribers found')
                subscriber_test['status'] = 'PASSED'
                
        except Exception as e:
            subscriber_test['details'].append(f'❌ Subscriber Check Error: {str(e)}')
            subscriber_test['status'] = 'FAILED'
            
        debug_info['tests'].append(subscriber_test)
        
        return render_template('admin/email_debug.html', debug_info=debug_info)
        
    except Exception as e:
        flash(f'Debug test error: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/debug/recaptcha-test', methods=['GET', 'POST'])
@admin_required
def debug_recaptcha_test():
    """Debug reCAPTCHA functionality"""
    
    from src.utils.anti_spam import get_recaptcha_site_key, get_recaptcha_v3_site_key, is_recaptcha_enabled, is_dual_recaptcha_enabled
    
    test_results = []
    
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email')
        recaptcha_v2_response = request.form.get('g-recaptcha-response')
        recaptcha_v3_response = request.form.get('g-recaptcha-v3-response')
        
        test_results.append(f"📧 Test email: {email}")
        test_results.append(f"🔒 reCAPTCHA v2 response: {'✅ Present' if recaptcha_v2_response else '❌ Missing'}")
        test_results.append(f"🔒 reCAPTCHA v3 response: {'✅ Present' if recaptcha_v3_response else '❌ Missing'}")
        
        if recaptcha_v2_response:
            test_results.append(f"🔒 v2 response length: {len(recaptcha_v2_response)} characters")
        if recaptcha_v3_response:
            test_results.append(f"🔒 v3 response length: {len(recaptcha_v3_response)} characters")
        
        # Test anti-spam validation
        try:
            from src.utils.anti_spam import anti_spam
            
           
            
            is_valid, message = anti_spam.is_submission_valid(
                request.form.to_dict(),
                recaptcha_v2_response,
                recaptcha_v3_response
            )
            
            test_results.append(f"🔧 Validation result: {'✅ PASSED' if is_valid else '❌ FAILED'}")
            test_results.append(f"🔧 Message: {message}")
            
            if is_valid:
                flash('reCAPTCHA test passed successfully!', 'success')
            else:
                flash(f'reCAPTCHA test failed: {message}', 'error')
                
        except Exception as e:
            test_results.append(f"❌ Validation error: {str(e)}")
            flash(f'reCAPTCHA test error: {str(e)}', 'error')
    
    return render_template('admin/recaptcha_debug.html',
                         recaptcha_site_key=get_recaptcha_site_key(),
                         recaptcha_v3_site_key=get_recaptcha_v3_site_key(),
                         recaptcha_enabled=is_recaptcha_enabled(),
                         dual_recaptcha_enabled=is_dual_recaptcha_enabled(),
                         test_results=test_results)

