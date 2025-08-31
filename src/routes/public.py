from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.models import db, User, Property, PropertyImage, ContactInquiry, UserApplication, State, LocalGovernment, CustomerEmail
from src.utils.email_service import email_service
from src.utils.anti_spam import require_anti_spam_protection, init_form_timestamp, get_recaptcha_site_key, get_recaptcha_v3_site_key, is_recaptcha_enabled, is_dual_recaptcha_enabled
from datetime import datetime
import secrets
import string

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
    state_id = request.args.get('state_id', type=int)
    local_government_id = request.args.get('local_government_id', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    bedrooms = request.args.get('bedrooms', type=int)
    
    # Build query with filters
    query = Property.query.filter_by(status='active')
    
    if property_type:
        query = query.filter_by(property_type=property_type)
    
    if location:
        query = query.filter(Property.location.contains(location))
    
    if state_id:
        query = query.filter(Property.state_id == state_id)
        
    if local_government_id:
        query = query.filter(Property.local_government_id == local_government_id)
    
    if min_price:
        query = query.filter(Property.price >= min_price)
    
    if max_price:
        query = query.filter(Property.price <= max_price)
    
    if bedrooms:
        query = query.filter(Property.bedrooms >= bedrooms)
    
    properties = query.order_by(Property.created_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )
    
    # Get states and local governments for filter dropdowns
    states = State.query.order_by(State.name).all()
    local_governments = LocalGovernment.query.order_by(LocalGovernment.name).all()
    
    if request.is_json:
        return jsonify({
            'properties': [prop.to_dict() for prop in properties.items],
            'total': properties.total,
            'pages': properties.pages,
            'current_page': page
        })
    
    return render_template('public/properties.html', 
                         properties=properties,
                         states=states,
                         local_governments=local_governments,
                         filters={
                             'type': property_type,
                             'location': location,
                             'state_id': state_id,
                             'local_government_id': local_government_id,
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
@require_anti_spam_protection
def contact():
    if request.method == 'GET':
        # Initialize form timestamp for bot detection
        init_form_timestamp()
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        try:
            # Handle newsletter subscription
            subscribe_newsletter = data.get('subscribe_newsletter') in [True, 'true', '1', 'on']
            
            inquiry = ContactInquiry(
                name=data.get('name'),
                email=data.get('email'),
                phone=data.get('phone'),
                property_id=data.get('property_id') if data.get('property_id') else None,
                message=data.get('message'),
                subscribe_newsletter=subscribe_newsletter
            )
            
            db.session.add(inquiry)
            
            # If user wants to subscribe to newsletter, add their email to CustomerEmail table
            if subscribe_newsletter:
                email = data.get('email')
                # Check if email already exists in CustomerEmail table
                existing_customer = CustomerEmail.query.filter_by(email=email).first()
                
                if not existing_customer:
                    # Add new subscriber
                    customer_email = CustomerEmail(
                        email=email,
                        source='inquiry_form'
                    )
                    db.session.add(customer_email)
                elif not existing_customer.is_active:
                    # Reactivate if they were unsubscribed
                    existing_customer.is_active = True
            
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
    
    return render_template('public/contact.html', 
                         recaptcha_site_key=get_recaptcha_site_key(),
                         recaptcha_v3_site_key=get_recaptcha_v3_site_key(),
                         recaptcha_enabled=is_recaptcha_enabled(),
                         dual_recaptcha_enabled=is_dual_recaptcha_enabled())

@public_bp.route('/register', methods=['GET', 'POST'])
@require_anti_spam_protection
def register():
    if request.method == 'GET':
        # Initialize form timestamp for bot detection
        init_form_timestamp()
    
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
    
    return render_template('public/register.html',
                         recaptcha_site_key=get_recaptcha_v3_site_key(),
                         recaptcha_v3_site_key=get_recaptcha_v3_site_key(),
                         recaptcha_enabled=is_recaptcha_enabled())

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
@require_anti_spam_protection
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



def generate_random_password(length=12):
    """Generate a random password"""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(characters) for _ in range(length))



@public_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = data.get('email')
        
        if not email:
            if request.is_json:
                return jsonify({'error': 'Email is required'}), 400
            else:
                flash('Email is required', 'error')
                return render_template('public/forgot_password.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate new random password
            new_password = generate_random_password()
            
            # Update user's password
            user.set_password(new_password)
            db.session.commit()
            
            # Send email with new password
            email_sent = email_service.send_password_reset_email(email, new_password)
            
            if email_sent:
                if request.is_json:
                    return jsonify({
                        'success': True, 
                        'message': 'A new password has been sent to your email address.'
                    })
                else:
                    flash('A new password has been sent to your email address. Please check your email.', 'success')
                    return redirect(url_for('public.login'))
            else:
                if request.is_json:
                    return jsonify({'error': 'Failed to send email. Please try again later.'}), 500
                else:
                    flash('Failed to send email. Please try again later.', 'error')
        else:
            # Don't reveal if email exists or not for security
            if request.is_json:
                return jsonify({
                    'success': True, 
                    'message': 'If an account with that email exists, a new password has been sent.'
                })
            else:
                flash('If an account with that email exists, a new password has been sent.', 'info')
                return redirect(url_for('public.login'))
    
    return render_template('public/forgot_password.html')

@public_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if not session.get('user_id'):
        flash('Please login to change your password', 'error')
        return redirect(url_for('public.login'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        user = User.query.get(session.get('user_id'))
        
        if not user.check_password(current_password):
            if request.is_json:
                return jsonify({'error': 'Current password is incorrect'}), 400
            else:
                flash('Current password is incorrect', 'error')
        elif new_password != confirm_password:
            if request.is_json:
                return jsonify({'error': 'New passwords do not match'}), 400
            else:
                flash('New passwords do not match', 'error')
        elif len(new_password) < 6:
            if request.is_json:
                return jsonify({'error': 'Password must be at least 6 characters long'}), 400
            else:
                flash('Password must be at least 6 characters long', 'error')
        else:
            user.set_password(new_password)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Password changed successfully'})
            else:
                flash('Password changed successfully', 'success')
                return redirect(url_for('public.home'))
    
    return render_template('public/change_password.html')

@public_bp.route('/profile')
def profile():
    if not session.get('user_id'):
        flash('Please login to view your profile', 'error')
        return redirect(url_for('public.login'))
    
    user = User.query.get(session.get('user_id'))
    applications = UserApplication.query.filter_by(user_id=user.id).order_by(UserApplication.created_at.desc()).all()
    
    if request.is_json:
        return jsonify({
            'user': user.to_dict(),
            'applications': [app.to_dict() for app in applications]
        })
    
    return render_template('public/profile.html', user=user, applications=applications)

@public_bp.route('/api/states/<int:state_id>/local-governments')
def get_local_governments_by_state(state_id):
    """Public API endpoint to get local governments by state"""
    try:
        local_governments = LocalGovernment.query.filter_by(state_id=state_id).order_by(LocalGovernment.name).all()
        return jsonify({
            'success': True,
            'local_governments': [{'id': lg.id, 'name': lg.name} for lg in local_governments]
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@public_bp.route('/profile/newsletter', methods=['GET', 'POST'])
def newsletter_preferences():
    """Manage user newsletter preferences"""
    if not session.get('user_id'):
        flash('Please login to manage your newsletter preferences', 'error')
        return redirect(url_for('public.login'))
    
    user = User.query.get(session.get('user_id'))
    
    if request.method == 'POST':
        try:
            # Update newsletter preferences
            user.newsletter_subscribed = 'newsletter_subscribed' in request.form
            user.weekly_newsletter = 'weekly_newsletter' in request.form
            user.monthly_newsletter = 'monthly_newsletter' in request.form
            user.quarterly_newsletter = 'quarterly_newsletter' in request.form
            user.yearly_newsletter = 'yearly_newsletter' in request.form
            
            db.session.commit()
            
            # Also update or create CustomerEmail record
            from src.models import CustomerEmail
            customer_email = CustomerEmail.query.filter_by(email=user.email).first()
            
            if user.newsletter_subscribed:
                if not customer_email:
                    # Create new CustomerEmail record
                    customer_email = CustomerEmail(
                        email=user.email,
                        subscribed_at=datetime.utcnow(),
                        is_active=True,
                        source='user_dashboard',
                        weekly_subscription=user.weekly_newsletter,
                        monthly_subscription=user.monthly_newsletter,
                        quarterly_subscription=user.quarterly_newsletter,
                        yearly_subscription=user.yearly_newsletter
                    )
                    db.session.add(customer_email)
                else:
                    # Update existing CustomerEmail record
                    customer_email.is_active = True
                    customer_email.weekly_subscription = user.weekly_newsletter
                    customer_email.monthly_subscription = user.monthly_newsletter
                    customer_email.quarterly_subscription = user.quarterly_newsletter
                    customer_email.yearly_subscription = user.yearly_newsletter
            else:
                # User unsubscribed - deactivate CustomerEmail record
                if customer_email:
                    customer_email.is_active = False
            
            db.session.commit()
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'message': 'Newsletter preferences updated successfully'
                })
            else:
                flash('Newsletter preferences updated successfully', 'success')
                return redirect(url_for('public.profile'))
                
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error updating newsletter preferences: {str(e)}'
            
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg, 'error')
    
    if request.is_json:
        return jsonify({
            'user': {
                'email': user.email,
                'newsletter_subscribed': user.newsletter_subscribed,
                'weekly_newsletter': user.weekly_newsletter,
                'monthly_newsletter': user.monthly_newsletter,
                'quarterly_newsletter': user.quarterly_newsletter,
                'yearly_newsletter': user.yearly_newsletter
            }
        })
    
    return render_template('public/newsletter_preferences.html', user=user)

# Email token-based routes
@public_bp.route('/newsletter/unsubscribe')
def newsletter_unsubscribe():
    """Handle newsletter unsubscribe with token"""
    from src.utils.email_tokens import email_token_manager
    from src.models import User, CustomerEmail
    
    token = request.args.get('token')
    if not token:
        flash('Invalid unsubscribe link.', 'error')
        return redirect(url_for('public.index'))
    
    # Verify token
    payload = email_token_manager.verify_token(token)
    if not payload:
        flash('Invalid or expired unsubscribe link.', 'error')
        return redirect(url_for('public.index'))
    
    email = payload.get('email')
    user_id = payload.get('user_id')
    
    try:
        # Update CustomerEmail subscription
        customer_email = CustomerEmail.query.filter_by(email=email).first()
        if customer_email:
            customer_email.is_active = False
            customer_email.unsubscribe_date = datetime.utcnow()
        
        # Update User preferences if user exists
        if user_id:
            user = User.query.get(user_id)
            if user:
                user.newsletter_subscribed = False
                user.weekly_newsletter = False
                user.monthly_newsletter = False
                user.quarterly_newsletter = False
                user.yearly_newsletter = False
        
        db.session.commit()
        flash('You have been successfully unsubscribed from all newsletters.', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Unsubscribe error: {e}")
        flash('An error occurred while unsubscribing. Please try again.', 'error')
    
    return render_template('public/unsubscribe_success.html', email=email)

@public_bp.route('/newsletter/preferences', methods=['GET', 'POST'])
def newsletter_preferences_token():
    """Handle newsletter preferences with token"""
    from src.utils.email_tokens import email_token_manager
    
    token = request.args.get('token')
    if not token:
        # If no token, redirect to login for authenticated access
        if 'user_id' not in session:
            flash('Please log in to manage your newsletter preferences.', 'info')
            return redirect(url_for('public.login'))
        else:
            # Redirect to regular preferences page
            return redirect(url_for('public.newsletter_preferences'))
    
    # Verify token
    payload = email_token_manager.verify_token(token)
    if not payload:
        flash('Invalid or expired preferences link. Please log in to manage your preferences.', 'error')
        if 'user_id' not in session:
            return redirect(url_for('public.login'))
        else:
            return redirect(url_for('public.newsletter_preferences'))
    
    email = payload.get('email')
    user_id = payload.get('user_id')
    
    # Find user by email or user_id
    user = None
    if user_id:
        user = User.query.get(user_id)
    elif email:
        user = User.query.filter_by(email=email).first()
    
    if not user:
        flash('User account not found. Please create an account to manage preferences.', 'warning')
        return redirect(url_for('public.register'))
    
    # Log in the user automatically for this session
    session['user_id'] = user.id
    session['email'] = user.email
    flash(f'You are now logged in to manage your newsletter preferences.', 'info')
    
    # Redirect to the regular preferences page
    return redirect(url_for('public.newsletter_preferences'))
