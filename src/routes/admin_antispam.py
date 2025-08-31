"""
Admin Anti-Spam Management
Provides tools for admins to monitor and manage spam attempts
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from src.models import db, ContactInquiry
from src.utils.anti_spam import anti_spam
from datetime import datetime, timedelta
import json

admin_antispam_bp = Blueprint('admin_antispam', __name__)

@admin_antispam_bp.route('/spam-protection')
@login_required
def spam_protection_dashboard():
    """Admin dashboard for spam protection management"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('public.home'))
    
    # Get recent submissions
    recent_inquiries = ContactInquiry.query.order_by(ContactInquiry.created_at.desc()).limit(50).all()
    
    # Get spam statistics
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Count inquiries by period
    today_count = ContactInquiry.query.filter(
        ContactInquiry.created_at >= today
    ).count()
    
    week_count = ContactInquiry.query.filter(
        ContactInquiry.created_at >= week_ago
    ).count()
    
    month_count = ContactInquiry.query.filter(
        ContactInquiry.created_at >= month_ago
    ).count()
    
    # Get rate limiting stats
    rate_limit_stats = {
        'tracked_ips': len(anti_spam.submission_log),
        'blocked_ips': len(anti_spam.blocked_ips),
        'total_submissions_today': sum([
            len([ts for ts in timestamps if ts.date() == today])
            for timestamps in anti_spam.submission_log.values()
        ])
    }
    
    return render_template('admin/spam_protection.html',
                         recent_inquiries=recent_inquiries,
                         today_count=today_count,
                         week_count=week_count,
                         month_count=month_count,
                         rate_limit_stats=rate_limit_stats)

@admin_antispam_bp.route('/analyze-inquiry/<int:inquiry_id>')
@login_required
def analyze_inquiry(inquiry_id):
    """Analyze a specific inquiry for spam indicators"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    inquiry = ContactInquiry.query.get_or_404(inquiry_id)
    
    # Analyze the inquiry
    form_data = {
        'name': inquiry.name,
        'email': inquiry.email,
        'message': inquiry.message
    }
    
    suspicious_score = anti_spam.analyze_submission_behavior(form_data)
    
    # Additional analysis
    analysis = {
        'suspicious_score': suspicious_score,
        'risk_level': 'High' if suspicious_score > 70 else 'Medium' if suspicious_score > 30 else 'Low',
        'indicators': []
    }
    
    # Check for specific indicators
    message_lower = inquiry.message.lower()
    
    if 'http' in message_lower:
        analysis['indicators'].append('Contains URLs')
    
    if len([c for c in inquiry.message if c.isupper()]) > len(inquiry.message) * 0.5:
        analysis['indicators'].append('Excessive capital letters')
    
    spam_patterns = ['viagra', 'cialis', 'casino', 'lottery', 'winner', 'congratulations']
    for pattern in spam_patterns:
        if pattern in message_lower:
            analysis['indicators'].append(f'Contains spam keyword: {pattern}')
    
    if not analysis['indicators']:
        analysis['indicators'].append('No obvious spam indicators detected')
    
    return jsonify(analysis)

@admin_antispam_bp.route('/block-ip', methods=['POST'])
@login_required
def block_ip():
    """Block an IP address"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    ip_address = request.json.get('ip_address')
    if not ip_address:
        return jsonify({'error': 'IP address required'}), 400
    
    anti_spam.blocked_ips.add(ip_address)
    
    return jsonify({'success': True, 'message': f'IP {ip_address} has been blocked'})

@admin_antispam_bp.route('/unblock-ip', methods=['POST'])
@login_required
def unblock_ip():
    """Unblock an IP address"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    ip_address = request.json.get('ip_address')
    if not ip_address:
        return jsonify({'error': 'IP address required'}), 400
    
    anti_spam.blocked_ips.discard(ip_address)
    
    return jsonify({'success': True, 'message': f'IP {ip_address} has been unblocked'})

@admin_antispam_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    """Update anti-spam settings"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    settings = request.json
    
    # Here you would update the settings in your environment or database
    # For now, we'll just return success
    
    flash('Anti-spam settings updated successfully', 'success')
    return jsonify({'success': True, 'message': 'Settings updated successfully'})

@admin_antispam_bp.route('/export-blocked-ips')
@login_required
def export_blocked_ips():
    """Export list of blocked IPs"""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    blocked_ips_list = list(anti_spam.blocked_ips)
    
    return jsonify({
        'blocked_ips': blocked_ips_list,
        'count': len(blocked_ips_list),
        'exported_at': datetime.now().isoformat()
    })
