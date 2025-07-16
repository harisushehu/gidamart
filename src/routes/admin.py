from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
from src.models import db, User, Property, PropertyImage, ContactInquiry, UserApplication
import os
from datetime import datetime
import uuid

admin_bp = Blueprint('admin', __name__)

# Helper function to check if user is admin
def is_admin():
    return session.get('user_id') and session.get('is_admin')

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email, is_admin=True).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = True
            session['user_email'] = user.email
            
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
    total_applications = UserApplication.query.count()
    pending_applications = UserApplication.query.filter_by(status='pending').count()
    
    stats = {
        'total_properties': total_properties,
        'active_properties': active_properties,
        'total_inquiries': total_inquiries,
        'new_inquiries': new_inquiries,
        'total_applications': total_applications,
        'pending_applications': pending_applications
    }
    
    # Get recent properties
    recent_properties = Property.query.order_by(Property.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', stats=stats, recent_properties=recent_properties)

@admin_bp.route('/properties')
@admin_required
def list_properties():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = Property.query
    if search:
        query = query.filter(Property.title.contains(search) | Property.location.contains(search))
    
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
    
    return render_template('admin/properties.html', properties=properties, search=search)

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
            location=data.get('location'),
            bedrooms=int(data.get('bedrooms', 0)),
            bathrooms=int(data.get('bathrooms', 0)),
            area_sqft=float(data.get('area_sqft', 0)),
            status=data.get('status', 'active')
        )
        
        db.session.add(property)
        db.session.commit()
        
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
    
    return render_template('admin/property_detail.html', property=property)

@admin_bp.route('/properties/<int:property_id>', methods=['PUT'])
@admin_required
def update_property(property_id):
    property = Property.query.get_or_404(property_id)
    data = request.get_json() if request.is_json else request.form
    
    try:
        property.title = data.get('title', property.title)
        property.description = data.get('description', property.description)
        property.price = float(data.get('price', property.price))
        property.property_type = data.get('property_type', property.property_type)
        property.location = data.get('location', property.location)
        property.bedrooms = int(data.get('bedrooms', property.bedrooms))
        property.bathrooms = int(data.get('bathrooms', property.bathrooms))
        property.area_sqft = float(data.get('area_sqft', property.area_sqft))
        property.status = data.get('status', property.status)
        property.updated_at = datetime.utcnow()
        
        db.session.commit()
        
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
        # Delete associated images from filesystem
        for image in property.images:
            image_path = os.path.join('src/static/uploads', image.image_filename)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        db.session.delete(property)
        db.session.commit()
        
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



@admin_bp.route('/properties/<int:property_id>/images', methods=['POST'])
@admin_required
def upload_property_images(property_id):
    property = Property.query.get_or_404(property_id)
    
    if 'images' not in request.files:
        return jsonify({'error': 'No images provided'}), 400
    
    files = request.files.getlist('images')
    uploaded_images = []
    
    try:
        for file in files:
            if file and file.filename:
                # Secure the filename
                filename = secure_filename(file.filename)
                
                # Generate unique filename
                file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                if file_extension not in ['jpg', 'jpeg', 'png', 'gif']:
                    continue
                
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                
                # Save the file
                file.save(file_path)
                
                # Create database record
                image = PropertyImage(
                    property_id=property_id,
                    image_filename=unique_filename,
                    is_primary=len(property.images) == 0,  # First image is primary
                    upload_order=len(property.images)
                )
                
                db.session.add(image)
                uploaded_images.append(image)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{len(uploaded_images)} images uploaded successfully',
            'images': [img.to_dict() for img in uploaded_images]
        })
        
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
        
        return jsonify({'success': True, 'message': 'Primary image updated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

