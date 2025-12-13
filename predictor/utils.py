from twilio.rest import Client
from django.conf import settings
import logging
import re

logger = logging.getLogger(__name__)

def format_phone_number(phone_number):
    """
    Format phone number to E.164 format
    """
    try:
        # Log the original phone number
        logger.info(f"Original phone number: {phone_number}")
        
        # Remove any non-digit characters except +
        digits = re.sub(r'[^\d+]', '', phone_number)
        logger.info(f"Digits after cleaning: {digits}")
        
        # Handle different formats
        if digits.startswith('+254'):
            # Already in correct format
            formatted_number = digits
        elif digits.startswith('254'):
            # Add + prefix
            formatted_number = '+' + digits
        elif digits.startswith('0'):
            # Replace leading 0 with +254
            formatted_number = '+254' + digits[1:]
        else:
            # Assume it's a local number, add +254
            formatted_number = '+254' + digits
            
        logger.info(f"Final formatted number: {formatted_number}")
        
        # Validate the final format
        if not re.match(r'^\+254[17]\d{8}$', formatted_number):
            logger.warning(f"Phone number {formatted_number} may not be in the correct format for Twilio")
            return None
            
        return formatted_number
    except Exception as e:
        logger.error(f"Error formatting phone number: {str(e)}")
        return None

def send_sms(to_number, message):
    """
    Send SMS using Twilio
    """
    try:
        # Log Twilio configuration (safely)
        logger.info("Checking Twilio configuration...")
        logger.info(f"Account SID configured: {bool(settings.TWILIO_ACCOUNT_SID)}")
        logger.info(f"Auth Token configured: {bool(settings.TWILIO_AUTH_TOKEN)}")
        logger.info(f"Phone Number configured: {bool(settings.TWILIO_PHONE_NUMBER)}")

        # Validate Twilio credentials
        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
            logger.error("Twilio credentials not properly configured")
            return False, "Twilio credentials not properly configured"

        # Initialize Twilio client
        logger.info("Initializing Twilio client...")
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Format phone number
        formatted_number = format_phone_number(to_number)
        if not formatted_number:
            logger.error(f"Invalid phone number format: {to_number}")
            return False, "Invalid phone number format. Must be a valid Kenyan number."
            
        logger.info(f"Attempting to send SMS to: {formatted_number}")
        logger.info(f"Using Twilio number: {settings.TWILIO_PHONE_NUMBER}")

        try:
            # Send message
            logger.info("Creating Twilio message...")
            message = client.messages.create(
                body=message,
                from_=settings.TWILIO_PHONE_NUMBER,
                to=formatted_number
            )
            
            logger.info(f"SMS sent successfully to {formatted_number}")
            logger.info(f"Message SID: {message.sid}")
            return True, "SMS sent successfully"
            
        except Exception as e:
            error_message = str(e)
            logger.error(f"Twilio API error: {error_message}")
            
            # Handle specific Twilio errors
            if "21612" in error_message:
                return False, "SMS sending failed: Your Twilio account is not authorized to send SMS to this country. Please verify your Twilio account for international SMS."
            elif "21211" in error_message:
                return False, "SMS sending failed: Invalid phone number format."
            elif "21214" in error_message:
                return False, "SMS sending failed: The 'To' phone number is not mobile."
            elif "21215" in error_message:
                return False, "SMS sending failed: The 'To' phone number is not verified."
            else:
                return False, f"SMS sending failed: {error_message}"
        
    except Exception as e:
        error_message = f"Failed to send SMS to {to_number}. Error: {str(e)}"
        logger.error(error_message)
        logger.error(f"Error type: {type(e).__name__}")
        return False, error_message 