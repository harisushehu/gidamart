import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app, render_template
from datetime import datetime
import calendar
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('SMTP_PORT', '587'))
        self.smtp_username = os.environ.get('SMTP_USERNAME')
        self.smtp_password = os.environ.get('SMTP_PASSWORD')
        # Use the authenticated email address for newsletters
        self.newsletter_from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        self.from_email = os.environ.get('FROM_EMAIL', self.smtp_username)
        
    def send_email(self, to_email, subject, body, is_html=False, from_email=None):
        """
        Send an email with enhanced error handling for production hosting
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Email body content
            is_html (bool): Whether the body is HTML content
            from_email (str): Custom from email address
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Check if email configuration is available
            if not self.smtp_username or not self.smtp_password:
                print("❌ Email configuration not found. SMTP credentials missing.")
                return False
            
            # Use custom from_email if provided, otherwise use default
            sender_email = from_email or self.from_email
            
            print(f"📧 Attempting to send email to {to_email}")
            print(f"📧 Using SMTP: {self.smtp_server}:{self.smtp_port}")
            print(f"📧 Authentication: {self.smtp_username}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add body to email
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Create SMTP session with enhanced error handling
            try:
                print(f"🔌 Connecting to SMTP server...")
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                print(f"✅ SMTP connection established")
                
                print(f"🔐 Starting TLS...")
                server.starttls()  # Enable security
                print(f"✅ TLS enabled")
                
                print(f"🔑 Authenticating...")
                server.login(self.smtp_username, self.smtp_password)
                print(f"✅ SMTP authentication successful")
                
                # Send email
                print(f"📤 Sending email...")
                text = msg.as_string()
                server.sendmail(self.smtp_username, to_email, text)
                print(f"✅ Email sent successfully")
                
                server.quit()
                print(f"🔚 SMTP connection closed")
                
                print(f"✅ Email sent successfully to {to_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ SMTP Authentication failed: {str(e)}")
                print(f"🔍 Check your Gmail App Password: {self.smtp_password[:4]}...{self.smtp_password[-4:]}")
                return False
                
            except smtplib.SMTPConnectError as e:
                print(f"❌ SMTP Connection failed: {str(e)}")
                print(f"🔍 Host may be blocking SMTP connections to {self.smtp_server}:{self.smtp_port}")
                return False
                
            except smtplib.SMTPServerDisconnected as e:
                print(f"❌ SMTP Server disconnected: {str(e)}")
                return False
                
            except smtplib.SMTPException as e:
                print(f"❌ SMTP Error: {str(e)}")
                return False
            
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {str(e)}")
            import traceback
            print("Full traceback:")
            traceback.print_exc()
            return False
    
    def send_bulk_emails(self, recipients, subject, body, is_html=False, from_email=None):
        """
        Send emails to multiple recipients
        
        Args:
            recipients (list): List of email addresses
            subject (str): Email subject
            body (str): Email body content
            is_html (bool): Whether the body is HTML content
            from_email (str): Custom from email address
            
        Returns:
            dict: Results with success count, failed count, and failed emails
        """
        results = {
            'success_count': 0,
            'failed_count': 0,
            'failed_emails': []
        }
        
        for email in recipients:
            try:
                if self.send_email(email, subject, body, is_html, from_email):
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1
                    results['failed_emails'].append(email)
            except Exception as e:
                print(f"Error sending to {email}: {str(e)}")
                results['failed_count'] += 1
                results['failed_emails'].append(email)
        
        return results
    
    def send_newsletter(self, recipients, newsletter_type, template_data=None):
        """
        Send newsletter using predefined templates
        
        Args:
            recipients (list): List of email addresses
            newsletter_type (str): Type of newsletter (weekly, monthly, quarterly, yearly)
            template_data (dict): Data to populate the template
            
        Returns:
            dict: Results with success count, failed count, and failed emails
        """
        print(f"🔧 Starting newsletter send: type={newsletter_type}, recipients={len(recipients)}")
        
        # Prepare template data
        if not template_data:
            template_data = {}
        
        # Add current date information
        now = datetime.now()
        template_data.update({
            'current_year': now.year,
            'current_month': calendar.month_name[now.month],
            'current_quarter': (now.month - 1) // 3 + 1,
            'next_year': now.year + 1
        })
        
        # Determine template and subject based on newsletter type
        template_map = {
            'weekly': {
                'template': 'email/newsletter_weekly.html',
                'subject': f'Gidamart Weekly Update - {calendar.month_name[now.month]} {now.day}, {now.year}'
            },
            'monthly': {
                'template': 'email/newsletter_monthly.html',
                'subject': f'Gidamart Monthly Report - {calendar.month_name[now.month]} {now.year}'
            },
            'quarterly': {
                'template': 'email/newsletter_quarterly.html',
                'subject': f'Gidamart Quarterly Review - Q{(now.month - 1) // 3 + 1} {now.year}'
            },
            'yearly': {
                'template': 'email/newsletter_yearly.html',
                'subject': f'Gidamart Annual Report - Year {now.year} Review'
            }
        }
        
        if newsletter_type not in template_map:
            error_msg = f"Invalid newsletter type: {newsletter_type}"
            print(f"❌ {error_msg}")
            return {
                'success_count': 0,
                'failed_count': len(recipients),
                'failed_emails': recipients,
                'error': error_msg
            }
        
        newsletter_config = template_map[newsletter_type]
        print(f"📧 Newsletter config: {newsletter_config['subject']}")
        
        try:
            # Check if we're in an application context
            if current_app:
                print(f"🌐 Using Flask template rendering for {newsletter_config['template']}")
                # Render the email template
                html_content = render_template(newsletter_config['template'], **template_data)
                print(f"✅ Template rendered successfully ({len(html_content)} characters)")
            else:
                print(f"⚠️ No Flask app context, using fallback content")
                # Fallback to basic HTML content if not in app context
                html_content = self._create_fallback_newsletter_content(newsletter_type, template_data)
                print(f"✅ Fallback content created ({len(html_content)} characters)")
            
            print(f"📤 Sending emails using from address: {self.newsletter_from_email}")
            
            # Send bulk emails using authenticated address
            results = self.send_bulk_emails(
                recipients=recipients,
                subject=newsletter_config['subject'],
                body=html_content,
                is_html=True,
                from_email=self.newsletter_from_email
            )
            
            print(f"📊 Send results: {results}")
            return results
            
        except Exception as e:
            error_msg = f"Error rendering/sending newsletter: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success_count': 0,
                'failed_count': len(recipients),
                'failed_emails': recipients,
                'error': error_msg
            }
    
    def _create_fallback_newsletter_content(self, newsletter_type, template_data):
        """Create a basic HTML newsletter when templates aren't available"""
        custom_message = template_data.get('custom_message', '')
        current_year = template_data.get('current_year', datetime.now().year)
        
        content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Gidamart Newsletter</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px;">
                <h1 style="color: #007bff; margin: 0; font-size: 2.5em;">GIDAMART</h1>
                <p style="color: #666; margin: 10px 0 0 0; font-size: 1.1em;">Your Trusted Real Estate Partner</p>
            </div>
            
            <div style="margin-bottom: 30px;">
                <h2 style="color: #007bff;">🏠 {newsletter_type.title()} Update</h2>
                
                <p>Dear Valued Subscriber,</p>
                
                <p>Thank you for subscribing to our {newsletter_type} newsletter. We appreciate your continued interest in Gidamart properties and market insights.</p>
                
                {f'<p>{custom_message}</p>' if custom_message else ''}
                
                <div style="background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #007bff;">Featured Properties</h3>
                    <p>Visit our website to explore the latest property listings and investment opportunities.</p>
                </div>
                
                <p>For more information about our properties and services, please visit our website or contact our team.</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://gidamart.com" style="background-color: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Visit Our Website</a>
                </div>
            </div>
            
            <div style="border-top: 2px solid #e9ecef; padding-top: 20px; text-align: center; color: #666; font-size: 0.9em;">
                <p><strong>Stay Connected with Gidamart</strong></p>
                <p>© {current_year} Gidamart. All rights reserved.</p>
                <p style="font-size: 12px; color: #999;">You're receiving this email because you subscribed to our newsletter.</p>
            </div>
        </body>
        </html>
        """
        
        return content
    
    def _simulate_email(self, to_email, subject, body):
        """
        Simulate sending email by printing to console
        """
        print(f"\n=== EMAIL SIMULATION ===")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body: {body[:200]}...")  # Truncate long emails
        print(f"========================\n")
        return True
    
    def send_password_reset_email(self, to_email, new_password):
        """
        Send password reset email with the new password
        """
        subject = "Gidamart - Password Reset"
        
        body = f"""Hello,

Your password has been reset as requested. Your new password is:

{new_password}

For your security, please log in with this new password and change it to something more memorable in your account settings.

Best regards,
Gidamart Team

---
This is an automated message. Please do not reply to this email.
"""
        
        return self.send_email(to_email, subject, body)

# Create a global instance with lazy initialization
def get_email_service():
    """Get a properly initialized email service instance"""
    from dotenv import load_dotenv
    load_dotenv()  # Ensure environment variables are loaded
    return EmailService()

# Update the global instance to ensure proper initialization
email_service = get_email_service()
