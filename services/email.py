import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import logging
from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME.get_secret_value()
        self.smtp_password = settings.SMTP_PASSWORD.get_secret_value()
        self.sender_email = settings.SENDER_EMAIL

    def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body_text: str,
        body_html: str = None
    ) -> bool:
        """
        Send email via SMTP
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body_text: Plain text body
            body_html: HTML body (optional)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.info(f"📧 Preparing to send email")
        logger.info(f"   To: {to_emails}")
        logger.info(f"   Subject: {subject}")
        logger.info(f"   From: {self.sender_email}")
        logger.info(f"   SMTP Host: {self.smtp_host}:{self.smtp_port}")
        logger.info(f"   SMTP Username: {self.smtp_username[:10]}...")
        
        try:
            # Create message
            logger.info("📝 Creating email message...")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(to_emails)

            # Add text part
            text_part = MIMEText(body_text, 'plain', 'utf-8')
            msg.attach(text_part)
            logger.info("✅ Added plain text part to email")

            # Add HTML part if provided
            if body_html:
                html_part = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(html_part)
                logger.info("✅ Added HTML part to email")

            # Connect to SMTP server
            logger.info(f"🔌 Connecting to SMTP server: {self.smtp_host}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                logger.info("🔐 Starting TLS encryption...")
                server.starttls()  # Enable TLS encryption
                
                logger.info("🔑 Authenticating with SMTP server...")
                server.login(self.smtp_username, self.smtp_password)
                logger.info("✅ SMTP authentication successful")
                
                # Send email
                logger.info("📤 Sending email message...")
                server.send_message(msg)
                logger.info("✅ Email message sent successfully")
                
            logger.info(f"🎉 Email sent successfully to {to_emails}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP authentication failed: {e}")
            logger.error(f"   Check your SMTP_USERNAME and SMTP_PASSWORD")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"❌ SMTP recipients refused: {e}")
            logger.error(f"   Check if recipient emails are verified in AWS SES")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ SMTP error: {e}")
            logger.error(f"   SMTP error code: {getattr(e, 'smtp_code', 'Unknown')}")
            logger.error(f"   SMTP error message: {getattr(e, 'smtp_error', 'Unknown')}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error sending email: {e}", exc_info=True)
            return False

    def send_password_reset_email(
        self,
        to_email: str,
        reset_link: str
    ) -> bool:
        """
        Send password reset email
        
        Args:
            to_email: Recipient email address
            reset_link: Password reset link
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        logger.info(f"🔐 Sending password reset email to: {to_email}")
        logger.info(f"   Reset link: {reset_link}")
        
        subject = "Password Reset Request"
        
        body_text = f"""
Hello,

You have requested to reset your password. Please click the link below to reset your password:

{reset_link}

This link will expire in 15 minutes.

If you did not request this password reset, please ignore this email.

Best regards,
GIB Foundation Team
        """.strip()

        body_html = f"""
<html>
<body>
    <h2>Password Reset Request</h2>
    <p>Hello,</p>
    <p>You have requested to reset your password. Please click the link below to reset your password:</p>
    <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
    <p>This link will expire in 15 minutes.</p>
    <p>If you did not request this password reset, please ignore this email.</p>
    <br>
    <p>Best regards,<br>GIB Foundation Team</p>
</body>
</html>
        """.strip()

        logger.info("📝 Password reset email content prepared")
        return self.send_email(
            to_emails=[to_email],
            subject=subject,
            body_text=body_text,
            body_html=body_html
        )


# Create a global instance
email_service = EmailService()
