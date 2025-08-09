"""
Email service for sending verification and notification emails.
Uses Python's built-in smtplib and email libraries.
"""

import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from app.config.settings import settings


class EmailService:
    """Service for sending emails using SMTP"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        self.template_dir = Path(__file__).parent.parent / "templates" / "emails"
    
    def _load_template(self, template_name: str, **kwargs) -> tuple[str, str]:
        """
        Load HTML and text email templates and render with variables
        
        Args:
            template_name: Name of template without extension (e.g., 'verification')
            **kwargs: Variables to substitute in template
            
        Returns:
            Tuple of (html_content, text_content)
        """
        html_path = self.template_dir / f"{template_name}.html"
        text_path = self.template_dir / f"{template_name}.txt"
        
        # Load HTML template
        html_content = ""
        if html_path.exists():
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read().format(**kwargs)
        
        # Load text template
        text_content = ""
        if text_path.exists():
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read().format(**kwargs)
        
        return html_content, text_content
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str = None) -> bool:
        """
        Send an email using SMTP
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email content
            text_body: Plain text email content (optional)
        
        Returns:
            True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Add text part if provided
            if text_body:
                text_part = MIMEText(text_body, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable encryption
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False
    
    def send_verification_email(self, to_email: str, username: str, verification_token: str) -> bool:
        """
        Send email verification email
        
        Args:
            to_email: User's email address
            username: User's username
            verification_token: Verification token
        
        Returns:
            True if email was sent successfully
        """
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        subject = "Verify your Democrasite account"
        
        # Load and render templates
        html_body, text_body = self._load_template(
            "verification",
            username=username,
            verification_url=verification_url
        )
        
        return self._send_email(to_email, subject, html_body, text_body)
    
    def send_password_reset_email(self, to_email: str, username: str, reset_token: str) -> bool:
        """
        Send password reset email (for future implementation)
        
        Args:
            to_email: User's email address
            username: User's username  
            reset_token: Password reset token
        
        Returns:
            True if email was sent successfully
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Reset your Democrasite password"
        
        # Load and render templates
        html_body, text_body = self._load_template(
            "password_reset",
            username=username,
            reset_url=reset_url
        )
        
        return self._send_email(to_email, subject, html_body, text_body)


# Utility functions
def generate_verification_token() -> str:
    """Generate a cryptographically secure verification token"""
    return secrets.token_urlsafe(32)


def is_token_expired(expires_at: datetime) -> bool:
    """Check if a verification token has expired"""
    return datetime.now(timezone.utc) > expires_at


def get_token_expiration() -> datetime:
    """Get the expiration time for a new verification token"""
    return datetime.now(timezone.utc) + timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS)


# Global email service instance
email_service = EmailService()