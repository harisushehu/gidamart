"""
Anti-Spam and Security Utilities
Provides comprehensive protection against bots and spam submissions
"""

import os
import time
import json
import hashlib
import requests
from datetime import datetime, timedelta
from flask import request, session, current_app, flash, redirect, url_for
from functools import wraps

class AntiSpamProtection:
    """Comprehensive anti-spam protection system"""
    
    def __init__(self):
        self.submission_log = {}  # In-memory storage for rate limiting
        self.blocked_ips = set()
        self.honeypot_field_name = "website"  # Common honeypot field name
        
    def get_client_ip(self):
        """Get the real client IP address"""
        # Check for forwarded IP (common in shared hosting)
        if 'X-Forwarded-For' in request.headers:
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif 'X-Real-IP' in request.headers:
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr
    
    def is_honeypot_filled(self, form_data):
        """Check if honeypot field is filled (indicates bot)"""
        honeypot_enabled = os.environ.get('HONEYPOT_ENABLED', 'True').lower() == 'true'
        if not honeypot_enabled:
            return False
        
        # Check multiple common honeypot field names
        honeypot_fields = ['website', 'url', 'homepage', 'link', 'email_confirm', 'phone_2']
        
        for field in honeypot_fields:
            if field in form_data and form_data[field].strip():
                return True
        return False
    
    def verify_recaptcha(self, recaptcha_response, recaptcha_v3_response=None):
        """Verify reCAPTCHA response (supports v2, v3, or dual mode)"""
        secret_key = os.environ.get('RECAPTCHA_SECRET_KEY')
        v3_secret_key = os.environ.get('RECAPTCHA_V3_SECRET_KEY')
        dual_mode = os.environ.get('RECAPTCHA_DUAL_MODE', 'false').lower() == 'true'
        
        print(f"🔧 reCAPTCHA Debug: dual_mode={dual_mode}, v2_key_set={bool(secret_key)}, v3_key_set={bool(v3_secret_key)}")
        print(f"🔧 reCAPTCHA Responses: v2_response={bool(recaptcha_response)}, v3_response={bool(recaptcha_v3_response)}")
        
        if not secret_key and not v3_secret_key:
            print("⚠️ No reCAPTCHA keys configured - allowing submission")
            return True
        
        # If dual mode is enabled and we have both keys and both responses
        if dual_mode and secret_key and v3_secret_key and recaptcha_response and recaptcha_v3_response:
            print("🔄 Using dual reCAPTCHA mode")
            return self._verify_dual_recaptcha(recaptcha_response, recaptcha_v3_response, secret_key, v3_secret_key)
        
        # Priority: Use v2 if we have a v2 response and v2 key (even if v3 is also configured)
        if secret_key and recaptcha_response and not recaptcha_v3_response:
            print("🔒 Using reCAPTCHA v2 verification")
            return self._verify_recaptcha_v2(recaptcha_response, secret_key)
        
        # Use v3 if we have v3 response and v3 key
        if v3_secret_key and recaptcha_v3_response:
            print("🔒 Using reCAPTCHA v3 verification")
            return self._verify_recaptcha_v3(recaptcha_v3_response, v3_secret_key)
        
        # Fallback: if only v3 key is configured but we got a v2 response, try v3 anyway
        if not dual_mode and v3_secret_key and recaptcha_response and not recaptcha_v3_response:
            print("🔄 Fallback: Trying v3 verification with v2 response")
            return self._verify_recaptcha_v3(recaptcha_response, v3_secret_key)
        
        print("❌ No valid reCAPTCHA response provided or configuration mismatch")
        return False
    
    def _verify_recaptcha_v2(self, recaptcha_response, secret_key):
        """Verify reCAPTCHA v2 response"""
        try:
            verification_url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': secret_key,
                'response': recaptcha_response,
                'remoteip': self.get_client_ip()
            }
            
            response = requests.post(verification_url, data=data, timeout=10)
            result = response.json()
            
            success = result.get('success', False)
            print(f"reCAPTCHA v2 verification: success={success}")
            
            return success
        except Exception as e:
            print(f"reCAPTCHA v2 verification error: {e}")
            return False
    
    def _verify_recaptcha_v3(self, recaptcha_response, secret_key):
        """Verify reCAPTCHA v3 response with score checking"""
        try:
            verification_url = 'https://www.google.com/recaptcha/api/siteverify'
            data = {
                'secret': secret_key,
                'response': recaptcha_response,
                'remoteip': self.get_client_ip()
            }
            
            response = requests.post(verification_url, data=data, timeout=10)
            result = response.json()
            
            success = result.get('success', False)
            score = result.get('score', 0.0)
            action = result.get('action', '')
            
            min_score = float(os.environ.get('RECAPTCHA_MIN_SCORE', 0.5))
            
            print(f"reCAPTCHA v3 verification: success={success}, score={score}, action={action}")
            
            # Verify both success and score threshold
            return success and score >= min_score
        except Exception as e:
            print(f"reCAPTCHA v3 verification error: {e}")
            return False
    
    def _verify_dual_recaptcha(self, v2_response, v3_response, v2_secret, v3_secret):
        """Verify both reCAPTCHA v2 and v3 for maximum security"""
        try:
            verification_url = 'https://www.google.com/recaptcha/api/siteverify'
            
            # Verify reCAPTCHA v3 first
            v3_data = {
                'secret': v3_secret,
                'response': v3_response,
                'remoteip': self.get_client_ip()
            }
            
            v3_response_obj = requests.post(verification_url, data=v3_data, timeout=10)
            v3_result = v3_response_obj.json()
            
            v3_success = v3_result.get('success', False)
            v3_score = v3_result.get('score', 0.0)
            min_score = float(os.environ.get('RECAPTCHA_MIN_SCORE', '0.5'))
            
            print(f"reCAPTCHA v3 verification: success={v3_success}, score={v3_score}")
            
            # If v3 score is high enough, we don't need v2
            if v3_success and v3_score >= min_score:
                print("reCAPTCHA v3 passed - skipping v2 verification")
                return True
            
            # If v3 failed or score is low, check v2
            if not v2_response:
                print("reCAPTCHA v3 failed and no v2 response provided")
                return False
            
            v2_data = {
                'secret': v2_secret,
                'response': v2_response,
                'remoteip': self.get_client_ip()
            }
            
            v2_response_obj = requests.post(verification_url, data=v2_data, timeout=10)
            v2_result = v2_response_obj.json()
            
            v2_success = v2_result.get('success', False)
            print(f"reCAPTCHA v2 verification: success={v2_success}")
            
            return v2_success
            
        except Exception as e:
            print(f"Dual reCAPTCHA verification error: {e}")
            return False
    
    def check_rate_limit(self, identifier=None):
        """Check if the current IP/user is rate limited"""
        rate_limit_enabled = os.environ.get('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
        if not rate_limit_enabled:
            return True
        
        if identifier is None:
            identifier = self.get_client_ip()
        
        current_time = datetime.now()
        hour_limit = int(os.environ.get('MAX_SUBMISSIONS_PER_IP_PER_HOUR', 5))
        day_limit = int(os.environ.get('MAX_SUBMISSIONS_PER_IP_PER_DAY', 20))
        
        # Initialize tracking for this identifier
        if identifier not in self.submission_log:
            self.submission_log[identifier] = []
        
        # Clean old entries (older than 24 hours)
        self.submission_log[identifier] = [
            timestamp for timestamp in self.submission_log[identifier]
            if current_time - timestamp < timedelta(hours=24)
        ]
        
        # Check hourly limit
        hour_ago = current_time - timedelta(hours=1)
        recent_submissions = [
            timestamp for timestamp in self.submission_log[identifier]
            if timestamp > hour_ago
        ]
        
        if len(recent_submissions) >= hour_limit:
            return False
        
        # Check daily limit
        if len(self.submission_log[identifier]) >= day_limit:
            return False
        
        return True
    
    def log_submission(self, identifier=None):
        """Log a submission for rate limiting"""
        if identifier is None:
            identifier = self.get_client_ip()
        
        if identifier not in self.submission_log:
            self.submission_log[identifier] = []
        
        self.submission_log[identifier].append(datetime.now())
    
    def analyze_submission_behavior(self, form_data):
        """Analyze submission for suspicious behavior"""
        suspicious_score = 0
        
        # Check for extremely fast submission (less than 3 seconds)
        if 'form_start_time' in session:
            time_taken = time.time() - session['form_start_time']
            if time_taken < 3:
                suspicious_score += 50
        
        # Check for common spam patterns
        text_fields = ['message', 'description', 'comment', 'content']
        for field in text_fields:
            if field in form_data:
                text = form_data[field].lower()
                # Common spam indicators
                spam_patterns = ['viagra', 'cialis', 'casino', 'lottery', 'winner', 'congratulations', 
                               'click here', 'buy now', 'limited time', 'act now', 'free money']
                
                for pattern in spam_patterns:
                    if pattern in text:
                        suspicious_score += 20
                
                # Check for excessive links
                if text.count('http') > 2:
                    suspicious_score += 30
                
                # Check for excessive caps
                if len([c for c in text if c.isupper()]) > len(text) * 0.5:
                    suspicious_score += 25
        
        return suspicious_score
    
    def is_submission_valid(self, form_data, recaptcha_response=None, recaptcha_v3_response=None):
        """Comprehensive validation of form submission with dual reCAPTCHA support"""
        print(f"🔧 Starting submission validation")
        print(f"🔧 Form fields: {list(form_data.keys())}")
        
        # Check honeypot
        if self.is_honeypot_filled(form_data):
            print("❌ Blocked: Honeypot field filled")
            return False, "Suspicious activity detected"
        print("✅ Honeypot check passed")
        
        # Check rate limiting
        if not self.check_rate_limit():
            print("❌ Blocked: Rate limit exceeded")
            return False, "Too many submissions. Please try again later."
        print("✅ Rate limit check passed")
        
        # Check reCAPTCHA (dual mode if enabled)
        print(f"🔧 Checking reCAPTCHA: v2_response={bool(recaptcha_response)}, v3_response={bool(recaptcha_v3_response)}")
        
        # Skip reCAPTCHA if neither response is provided (for testing)
        if not recaptcha_response and not recaptcha_v3_response:
            print("⚠️ No reCAPTCHA responses provided - checking if required")
            # Check if reCAPTCHA is actually required
            if os.environ.get('RECAPTCHA_SECRET_KEY') or os.environ.get('RECAPTCHA_V3_SECRET_KEY'):
                print("❌ reCAPTCHA is required but not provided")
                return False, "Please complete the security verification"
            else:
                print("✅ No reCAPTCHA configured - allowing submission")
        else:
            # We have at least one reCAPTCHA response
            if not self.verify_recaptcha(recaptcha_response, recaptcha_v3_response):
                print("❌ Blocked: reCAPTCHA verification failed")
                return False, "Please complete the security verification"
            print("✅ reCAPTCHA verification passed")
        
        # Analyze behavior
        suspicious_score = self.analyze_submission_behavior(form_data)
        print(f"🔧 Suspicious behavior score: {suspicious_score}")
        if suspicious_score > 70:
            print(f"❌ Blocked: Suspicious behavior score too high: {suspicious_score}")
            return False, "Submission appears to be automated"
        print("✅ Behavior analysis passed")
        
        # Log successful submission
        self.log_submission()
        
        print("✅ All validation checks passed")
        return True, "Valid submission"

# Global instance
anti_spam = AntiSpamProtection()

def require_anti_spam_protection(f):
    """Decorator to protect routes with anti-spam measures (supports dual reCAPTCHA)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if request.method == 'POST':
                # Get reCAPTCHA responses (both v2 and v3 if available)
                recaptcha_v2_response = request.form.get('g-recaptcha-response')
                recaptcha_v3_response = request.form.get('g-recaptcha-v3-response')
                
                print(f"🔧 Anti-spam check for {request.endpoint}")
                print(f"🔧 v2 response: {bool(recaptcha_v2_response)} ({'present' if recaptcha_v2_response else 'missing'})")
                print(f"🔧 v3 response: {bool(recaptcha_v3_response)} ({'present' if recaptcha_v3_response else 'missing'})")
                
                # Validate submission
                is_valid, message = anti_spam.is_submission_valid(
                    request.form.to_dict(), 
                    recaptcha_v2_response,
                    recaptcha_v3_response
                )
                
                print(f"🔧 Validation result: valid={is_valid}, message='{message}'")
                
                if not is_valid:
                    print(f"❌ Blocking submission: {message}")
                    # Return error response
                    if request.is_json:
                        return {'success': False, 'message': message}, 400
                    else:
                        flash(message, 'error')
                        return redirect(request.url)
                
                print("✅ Anti-spam check passed")
        
        except Exception as e:
            print(f"❌ Error in anti-spam protection: {str(e)}")
            # In case of error, allow the request to proceed to avoid blocking legitimate users
            print("⚠️ Proceeding without anti-spam check due to error")
        
        return f(*args, **kwargs)
    return decorated_function

def init_form_timestamp():
    """Initialize form timestamp for measuring submission speed"""
    session['form_start_time'] = time.time()

def get_recaptcha_site_key():
    """Get reCAPTCHA site key for templates"""
    return os.environ.get('RECAPTCHA_SITE_KEY', '')

def get_recaptcha_v3_site_key():
    """Get reCAPTCHA v3 site key for templates"""
    return os.environ.get('RECAPTCHA_V3_SITE_KEY', '')

def is_recaptcha_enabled():
    """Check if reCAPTCHA is enabled (v2 or v3)"""
    return bool(os.environ.get('RECAPTCHA_SITE_KEY') or os.environ.get('RECAPTCHA_V3_SITE_KEY'))

def is_dual_recaptcha_enabled():
    """Check if dual reCAPTCHA mode is enabled"""
    return (os.environ.get('RECAPTCHA_DUAL_MODE', 'false').lower() == 'true' and 
            bool(os.environ.get('RECAPTCHA_V3_SITE_KEY')))
