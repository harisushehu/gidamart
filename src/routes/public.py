from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, Property, PropertyImage, ContactInquiry, UserApplication
from datetime import datetime

public_bp = Blueprint('public', __name__)

@public_bp.route('/')
def home():
    # Get featured properties (latest 6 active properties)
    featured_properties = Property.query.filter_by(status='active').order_by(Property.created_at.desc()).limit(6).all()
    
    return render_template('public/home.html', featured_properties=featured_properties)

@public_bp.route('/properties')
def properties():
    page = request.args.get('page', 1, type=int)
    property_type = request.args.get('type', '')
    location = request.args.get('location', '')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms = request.args.get('bedrooms', type=int)
    
    # Build query with filters
    query = Property.query.filter_by(status='active')
    
    if property_type:
        query = query.filter_by(property_type=property_type)
    
    if location:
        query = query.filter(Property.location.contains(location))
    
    if min_price:
        query = query.filter(Property.price >= min_price)
    
    if max_price:
        query = query.filter(Property.price <= max_price)
    
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)
    
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
    
    return render_template('public/properties.html', 
                         properties=properties,
                         filters={
                             'type': property_type,
                             'location': location,
                             'min_price': min_price,
                             'max_price': max_price,
                             'bedrooms': bedrooms
                         })

@public_bp.route('/properties/<int:property_id>')
def property_detail(property_id):
    property = Property.query.filter_by(id=property_id, status='active').first_or_404()
    
    # Get related properties (same location or type)
    related_properties = Property.query.filter(
        Property.id != property_id,
        Property.status == 'active',
        (Property.location.contains(property.location.split(',')[0]) | 
         (Property.property_type == property.property_type))
    ).limit(4).all()
    
    if request.is_json:
        return jsonify({
            'property': property.to_dict(),
            'related_properties': [prop.to_dict() for prop in related_properties]
        })
    
    return render_template('public/property_detail.html', 
                         property=property, 
                         related_properties=related_properties)

@public_bp.route('/services')
def services():
    return render_template('public/services.html')

@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            inquiry = ContactInquiry(
                name=data.get('name'),
                email=data.get('email'),
                phone=data.get('phone'),
                property_id=data.get('property_id') if data.get('property_id') else None,
                message=data.get('message')
            )
            
            db.session.add(inquiry)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Your inquiry has been sent successfully!'})
            else:
                flash('Your inquiry has been sent successfully!', 'success')
                return redirect(url_for('public.contact'))
                
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            else:
                flash(f'Error sending inquiry: {str(e)}', 'error')
    
    return render_template('public/contact.html')

@public_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'error': 'Email already registered'}), 400
            else:
                flash('Email already registered', 'error')
                return render_template('public/register.html')
        
        try:
            user = User(email=email)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # Auto login after registration
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['user_email'] = user.email
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Registration successful!'})
            else:
                flash('Registration successful!', 'success')
                return redirect(url_for('public.home'))
                
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': str(e)}), 400
            else:
                flash(f'Registration error: {str(e)}', 'error')
    
    return render_template('public/register.html')

@public_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            session['user_email'] = user.email
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful'})
            else:
                flash('Login successful', 'success')
                return redirect(url_for('public.home'))
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid credentials'}), 401
            else:
                flash('Invalid credentials', 'error')
    
    return render_template('public/login.html')

@public_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('public.home'))

@public_bp.route('/apply/<int:property_id>', methods=['POST'])
def apply_property(property_id):
    if not session.get('user_id'):
        if request.is_json:
            return jsonify({'error': 'Please login to apply'}), 401
        else:
            flash('Please login to apply', 'error')
            return redirect(url_for('public.login'))
    
    property = Property.query.filter_by(id=property_id, status='active').first_or_404()
    user_id = session.get('user_id')
    
    # Check if user already applied
    existing_application = UserApplication.query.filter_by(
        user_id=user_id, 
        property_id=property_id
    ).first()
    
    if existing_application:
        if request.is_json:
            return jsonify({'error': 'You have already applied for this property'}), 400
        else:
            flash('You have already applied for this property', 'error')
            return redirect(url_for('public.property_detail', property_id=property_id))
    
    data = request.get_json() if request.is_json else request.form
    
    try:
        application = UserApplication(
            user_id=user_id,
            property_id=property_id,
            message=data.get('message', '')
        )
        
        db.session.add(application)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Application submitted successfully!'})
        else:
            flash('Application submitted successfully!', 'success')
            return redirect(url_for('public.property_detail', property_id=property_id))
            
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        else:
            flash(f'Error submitting application: {str(e)}', 'error')
            return redirect(url_for('public.property_detail', property_id=property_id))

@public_bp.route('/search')
def search():
    query = request.args.get('q', '')
    
    if not query:
        return redirect(url_for('public.properties'))
    
    # Search in title, description, and location
    properties = Property.query.filter(
        Property.status == 'active',
        (Property.title.contains(query) | 
         Property.description.contains(query) | 
         Property.location.contains(query))
    ).order_by(Property.created_at.desc()).all()
    
    if request.is_json:
        return jsonify({
            'properties': [prop.to_dict() for prop in properties],
            'query': query,
            'count': len(properties)
        })
    
    return render_template('public/search_results.html', 
                         properties=properties, 
                         query=query)

