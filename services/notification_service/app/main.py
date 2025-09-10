import logging
import os
from fastapi import FastAPI
from app.routes import router
from services.notification_service.app.config import AppMetadata, AppConfiguration
from mangum import Mangum

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context) -> None:
    app_metadata = AppMetadata()
    app_config = AppConfiguration()
    notification_client = NotificationClient(app_config.sender_email, app_config.region)

    detail_type = event.get("detail-type")
    detail = event.get("detail", {})

    if detail_type == "booking.confirmed":
        quest_email = detail.get("guest_email")
        property_name = detail.get("property_name")
        check_in = detail.get("check_in")

        if guest_email and property_name and check_in:
            subject = "Your booking is confirmed!"
            message = f"Thank you for booking {property_name}. Your check-in date is {check_in}."
            notification_client.send_email(guest_email, subject, message)

    elif detail_type == "review.created":
        host_email = detail.get("host_email")
        reviewer_name = detail.get("reviewer_name")
        rating = detail.get("rating")


        if host_email and reviewer_name and rating:
            subject = "You've received a new review"
            message = f"{reviewer_name} rated you {rating}/5. View it in your dashboard."
            notification_client.send_email(host_email, subject, message)
    
    else:
        logging.error("Unknown notification type")