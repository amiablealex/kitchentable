import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

logger = logging.getLogger(__name__)

def send_password_reset_email(recipient_email, reset_token, app_url):
    """
    Send password reset email to user
    
    Args:
        recipient_email: User's email address
        reset_token: Password reset token
        app_url: Base URL of the application (e.g., https://kitchen.yourdomain.com)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Skip email sending if not configured
    if not Config.SMTP_ENABLED:
        logger.warning(f"SMTP not configured. Reset link for {recipient_email}: {app_url}/reset-password/{reset_token}")
        return False
    
    try:
        # Create reset link
        reset_link = f"{app_url}/reset-password/{reset_token}"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Reset Your Kitchen Table Password"
        msg['From'] = Config.SMTP_FROM_EMAIL
        msg['To'] = recipient_email
        
        # Plain text version
        text_body = f"""
Hi there,

You requested to reset your password for The Kitchen Table.

Click the link below to reset your password:
{reset_link}

This link will expire in 1 hour.

If you didn't request this, you can safely ignore this email.

---
The Kitchen Table
        """
        
        # HTML version
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Handlee', cursive, Arial, sans-serif;
            line-height: 1.6;
            color: #3D2B1F;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background: #F9F6F2;
            border-radius: 16px;
            padding: 30px;
            border: 2px solid #EAE3DC;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .title {{
            font-family: 'Grand Hotel', cursive, Georgia, serif;
            font-size: 2em;
            color: #D9534F;
            margin: 10px 0;
        }}
        .button {{
            display: inline-block;
            background: #D9534F;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 25px;
            margin: 20px 0;
            font-weight: 600;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #EAE3DC;
            color: #7A6A5D;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="font-size: 3em;">🏠</div>
            <h1 class="title">The Kitchen Table</h1>
        </div>
        
        <p>Hi there,</p>
        
        <p>You requested to reset your password for The Kitchen Table.</p>
        
        <p>Click the button below to reset your password:</p>
        
        <div style="text-align: center;">
            <a href="{reset_link}" class="button">Reset Password</a>
        </div>
        
        <p style="color: #7A6A5D; font-size: 0.9em;">
            Or copy and paste this link into your browser:<br>
            <a href="{reset_link}" style="color: #D9534F;">{reset_link}</a>
        </p>
        
        <div class="footer">
            <p>This link will expire in 1 hour.</p>
            <p>If you didn't request this password reset, you can safely ignore this email. Your password will remain unchanged.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Attach parts
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Password reset email sent to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send password reset email to {recipient_email}: {str(e)}")
        return False


def test_email_config():
    """
    Test email configuration by attempting to connect to SMTP server
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not Config.SMTP_ENABLED:
        return False, "SMTP not configured in environment variables"
    
    try:
        with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
        return True, "Email configuration is working correctly"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed - check username/password"
    except smtplib.SMTPException as e:
        return False, f"SMTP error: {str(e)}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"
