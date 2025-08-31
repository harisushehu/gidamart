"""
Email Token Management System
Handles secure tokens for email unsubscribe and preference management
"""

import os
import time
import hashlib
import hmac
from urllib.parse import urlencode, parse_qs
from flask import url_for, current_app
import base64
import json

class EmailTokenManager:
    def __init__(self):
        # Use a secret key for token generation - should be same as Flask secret key
        self.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
        self.token_expiry = 30 * 24 * 3600  # 30 days in seconds
    
    def generate_token(self, email, action='preferences', user_id=None):
        """
        Generate a secure token for email-based actions
        
        Args:
            email (str): User's email address
            action (str): Action type ('preferences', 'unsubscribe')
            user_id (int): User ID if user is registered
            
        Returns:
            str: Secure token
        """
        # Create payload with timestamp
        payload = {
            'email': email,
            'action': action,
            'user_id': user_id,
            'timestamp': int(time.time())
        }
        
        # Convert to JSON and encode
        payload_json = json.dumps(payload, sort_keys=True)
        payload_encoded = base64.urlsafe_b64encode(payload_json.encode()).decode()
        
        # Create HMAC signature
        signature = hmac.new(
            self.secret_key.encode(),
            payload_encoded.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Combine payload and signature
        token = f"{payload_encoded}.{signature}"
        return token
    
    def verify_token(self, token):
        """
        Verify and decode a token
        
        Args:
            token (str): Token to verify
            
        Returns:
            dict: Decoded payload if valid, None if invalid
        """
        try:
            # Split token into payload and signature
            parts = token.split('.')
            if len(parts) != 2:
                return None
            
            payload_encoded, signature = parts
            
            # Verify signature
            expected_signature = hmac.new(
                self.secret_key.encode(),
                payload_encoded.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Decode payload
            payload_json = base64.urlsafe_b64decode(payload_encoded.encode()).decode()
            payload = json.loads(payload_json)
            
            # Check expiry
            token_age = int(time.time()) - payload.get('timestamp', 0)
            if token_age > self.token_expiry:
                return None
            
            return payload
            
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
    
    def generate_unsubscribe_link(self, email, user_id=None, base_url=None):
        """
        Generate a complete unsubscribe link
        
        Args:
            email (str): User's email address
            user_id (int): User ID if registered
            base_url (str): Base URL for the application
            
        Returns:
            str: Complete unsubscribe URL
        """
        token = self.generate_token(email, 'unsubscribe', user_id)
        
        if base_url:
            return f"{base_url}/newsletter/unsubscribe?token={token}"
        else:
            # Use Flask's url_for if in app context
            try:
                return url_for('public.newsletter_unsubscribe', token=token, _external=True)
            except:
                # Fallback for when not in app context
                return f"/newsletter/unsubscribe?token={token}"
    
    def generate_preferences_link(self, email, user_id=None, base_url=None):
        """
        Generate a complete preferences management link
        
        Args:
            email (str): User's email address
            user_id (int): User ID if registered
            base_url (str): Base URL for the application
            
        Returns:
            str: Complete preferences URL
        """
        token = self.generate_token(email, 'preferences', user_id)
        
        if base_url:
            return f"{base_url}/newsletter/preferences?token={token}"
        else:
            # Use Flask's url_for if in app context
            try:
                return url_for('public.newsletter_preferences_token', token=token, _external=True)
            except:
                # Fallback for when not in app context
                return f"/newsletter/preferences?token={token}"

# Global instance
email_token_manager = EmailTokenManager()

def get_unsubscribe_link(email, user_id=None):
    """Helper function to get unsubscribe link"""
    return email_token_manager.generate_unsubscribe_link(email, user_id)

def get_preferences_link(email, user_id=None):
    """Helper function to get preferences link"""
    return email_token_manager.generate_preferences_link(email, user_id)
