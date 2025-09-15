import logging
import sys
from config import AppConfiguration

from ses_client import NotificationClient


logger = logging.getLogger()
logger.setLevel(logging.INFO)

if not logger.hasHandlers():
    logger_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(logger_handler)

    

def handler(event, context) -> None:
    app_config = AppConfiguration()
    notification_client = NotificationClient(app_config.sender_email, app_config.region)

    detail_type = event.get("detail-type")
    detail = event.get("detail", {})
    
    logger.info(f"Received event: {event}")

    if detail_type == "BookingConfirmed":
        guest_email = detail.get("guest_email")
        property_name = detail.get("property_name")
        check_in = detail.get("check_in")
        host_email = detail.get("host_email")

        if guest_email and property_name and check_in:
            subject = "Your booking is confirmed!"
            message = f"Thank you for booking {property_name}. Your check-in date is {check_in}."
            try:
                notification_client.send_email(guest_email, subject, message)
                logger.info(f"Booking confirmation email sent to {guest_email}")
            except Exception as e:
                logger.error(f"Failed to send booking email to {guest_email}: {e}")
        else:
            logger.warning(f"Missing booking fields in event: {detail}")

        # Optionally notify the host as well
        if host_email and property_name and check_in:
            subject_host = "New booking received"
            message_host = f"You have a new booking for {property_name} with check-in on {check_in}."
            try:
                notification_client.send_email(host_email, subject_host, message_host)
                logger.info(f"Booking notification email sent to host {host_email}")
            except Exception as e:
                logger.error(f"Failed to send host booking email to {host_email}: {e}")

    elif detail_type == "ReviewCreated":
        host_email = detail.get("host_email")
        reviewer_name = detail.get("reviewer_name")
        rating = detail.get("rating")


        if host_email and reviewer_name and rating:
            subject = "You've received a new review"
            message = f"{reviewer_name} rated you {rating}/5. View it in your dashboard."
            try:
                notification_client.send_email(host_email, subject, message)
                logger.info(f"Review notification email sent to {host_email}")
            except Exception as e:
                logger.error(f"Failed to send review email to {host_email}: {e}")

        else:
            logger.warning(f"Missing review fields in event: {detail}")
    
    else:
        logging.error(f"Unknown notification type: {detail_type}")
