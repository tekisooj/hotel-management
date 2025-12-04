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

    elif detail_type == "BookingCancelled":
        guest_email = detail.get("guest_email")
        property_name = detail.get("property_name")
        check_in = detail.get("check_in")

        if guest_email:
            subject = "Your booking has been cancelled"
            message_parts = ["We wanted to let you know your booking was cancelled."]
            if property_name:
                message_parts.append(f"Property: {property_name}.")
            if check_in:
                message_parts.append(f"Original check-in date: {check_in}.")
            message = " ".join(message_parts)
            try:
                notification_client.send_email(guest_email, subject, message)
                logger.info(f"Booking cancellation email sent to {guest_email}")
            except Exception as e:
                logger.error(f"Failed to send cancellation email to {guest_email}: {e}")
        else:
            logger.warning(f"Missing guest email for cancellation event: {detail}")

    elif detail_type == "PropertyUnavailable":
        guest_email = detail.get("guest_email")
        property_name = detail.get("property_name")
        room_name = detail.get("room_name")
        host_name = detail.get("host_name")
        host_email = detail.get("host_email")
        host_phone = detail.get("host_phone")
        check_in = detail.get("check_in")

        if guest_email:
            subject = "Your upcoming stay is no longer available"
            message_parts = [
                "We’re sorry to inform you that your upcoming booking is no longer available."
            ]
            if property_name:
                message_parts.append(f"Property: {property_name}.")
            if room_name:
                message_parts.append(f"Room: {room_name}.")
            if check_in:
                message_parts.append(f"Check-in date: {check_in}.")
            if host_name or host_email or host_phone:
                message_parts.append("Host contact:")
                host_contact = " ".join(
                    part for part in [host_name, host_email, host_phone] if part
                )
                message_parts.append(host_contact)
            message = " ".join(message_parts)
            try:
                notification_client.send_email(guest_email, subject, message)
                logger.info(f"Property unavailable email sent to {guest_email}")
            except Exception as e:
                logger.error(f"Failed to send property unavailable email to {guest_email}: {e}")
        else:
            logger.warning(f"Missing guest email for property unavailable event: {detail}")

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
