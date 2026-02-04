"""
UMD Transportation Request Tool

Tool for requesting accessibility rides via email.
"""

from tools.tooling import tool

import os
import smtplib
import ssl
import time
import logging
from email.message import EmailMessage
from datetime import datetime, timezone
from typing import Dict

#timezones
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

#UMD SMTP Relay Configuration (should not be modified)
SMTP_HOST = "marley.umd.edu"
SMTP_PORT = 587
SMTP_USER = "request-ride"
SMTP_PASS = "TQ2EXWqk2uSjjfl0nE2c4v6Rw" 
FROM_NAME = "Transportation Scheduling"
FROM_EMAIL = "noreply@umd.edu" #can be any @umd.edu address

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5


def make_message(
    to_email: str,
    subject: str,
    plain_text: str,
    html_text: str
) -> EmailMessage:
    #create email message (plain text and HTML versions)
    msg = EmailMessage()
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    msg.set_content(plain_text)
    msg.add_alternative(html_text, subtype="html")
    
    return msg


def send_email(msg: EmailMessage) -> None:
    #send email via SMTP (including retry logic)
    if not SMTP_USER or not SMTP_PASS:
        raise RuntimeError("SMTP credentials not configured in SMTP_USER/SMTP_PASS.")

    context = ssl.create_default_context()

    attempt = 0
    while True:
        attempt += 1
        try:
            logging.info("Connecting to SMTP %s:%s (attempt %d)...", SMTP_HOST, SMTP_PORT, attempt)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.ehlo()
                if SMTP_PORT == 587:
                    smtp.starttls(context=context)
                    smtp.ehlo()
                smtp.login(SMTP_USER, SMTP_PASS)
                smtp.send_message(msg)
            logging.info("Email sent to %s", msg["To"])
            break
        except Exception as e:
            logging.exception("Failed to send email on attempt %d: %s", attempt, e)
            if attempt >= MAX_RETRIES:
                logging.error("Exceeded max retries, try again later.")
                raise
            time.sleep(RETRY_DELAY_SECONDS)


@tool
def request_bus_ride(
    student_name: str,
    university_id: str,
    route_name: str,
    pickup: str,
    depart_time: str,
    extra_notes: str = ""
) -> Dict[str, str]:
    """
    Request an accessibility ride from UMD transportation by sending a formatted email.
    
    This tool sends a formatted ride request email to the university transportation
    department with student information, destination, pickup location, and departure time.
    
    Args:
        student_name (str): Full name of the student requesting the ride (e.g., "Jane Smith")
        university_id (str): UMD University ID number (e.g., "123456789")
        route_name (str): Destination or route name (e.g., "McKeldin Mall", "College Park Metro")
        pickup (str): Pickup location on campus (e.g., "Cambridge Hall", "Stamp Student Union")
        depart_time (str): ISO format datetime string for desired departure (e.g., "2024-12-05T14:30:00")
        extra_notes (str): Additional information or special requirements (optional, e.g., "Uses wheelchair", "Have 2 large bags")
    
    Returns:
        dict:
            - status: "success" if request was sent, "error" if failed
            - message: Descriptive message about the request result
            - sent_to: Email address the request was sent to (only on success)
    """
    
    #UMD Transportation email: shuttledrm@umd.edu 
    transportation_email = "anishar@umd.edu"  #replace with above email after testing
    
    try:
        #parse datetime string
        depart_dt = datetime.fromisoformat(depart_time)
        
        #ensure timezone-aware
        if depart_dt.tzinfo is None:
            if ZoneInfo is not None:
                depart_dt = depart_dt.replace(tzinfo=ZoneInfo("America/New_York"))
            else:
                depart_dt = depart_dt.replace(tzinfo=timezone.utc)

        #fix year for datetime
        now = datetime.now(timezone.utc)
        if depart_dt.year < now.year or (depart_dt.year == now.year and depart_dt < now):
            depart_dt = depart_dt.replace(year=now.year)
            if depart_dt < now:
                depart_dt = depart_dt.replace(year=now.year + 1)
        
        subject = f"Ride Request: {route_name} — {depart_dt.strftime('%b %d, %Y %H:%M')}"
        
        #plain text email
        plain = (
            f"Hello,\n\n"
            f"I would like to request an accessibility ride. See below for details:\n\n"
            f"Student Name: {student_name}\n"
            f"University ID: {university_id}\n"
            f"Destination: {route_name}\n"
            f"Pickup Location: {pickup}\n"
            f"Requested Departure Time: {depart_dt.strftime('%Y-%m-%d %H:%M %Z')}\n"
        )
        
        if extra_notes:
            plain += f"Additional Notes: {extra_notes}\n"
        
        plain += (
            f"\nThank you very much,\n"
            f"{student_name}"
        )
        
        #HTML email
        html = f"""
        <html>
          <body>
            <p>Hello,</p>
            <p>I would like to request an accessibility ride. See below for details:</p>
            <ul>
              <li><strong>Student Name:</strong> {student_name}</li>
              <li><strong>University ID:</strong> {university_id}</li>
              <li><strong>Destination:</strong> {route_name}</li>
              <li><strong>Pickup Location:</strong> {pickup}</li>
              <li><strong>Requested Departure Time:</strong> {depart_dt.strftime('%Y-%m-%d %H:%M %Z')}</li>
        """
        
        if extra_notes:
            html += f"<li><strong>Additional Notes:</strong> {extra_notes}</li>"
        
        html += """
            </ul>
            <p>Thank you very much,<br>
            """ + student_name + """</p>
          </body>
        </html>
        """

        msg = make_message(
            to_email=transportation_email,
            subject=subject,
            plain_text=plain,
            html_text=html
        )
        send_email(msg)
        
        return {
            "status": "success",
            "message": f"Ride request successfully submitted for {student_name} on {depart_dt.strftime('%B %d, %Y at %I:%M %p')}",
            "sent_to": transportation_email
        }
        
    except ValueError as e:
        error_msg = f"Invalid datetime format: {e}. Use ISO format like '2024-12-05T14:30:00'"
        logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }
    except Exception as e:
        error_msg = f"Failed to send ride request: {str(e)}"
        logging.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }


TOOL_SPEC = request_bus_ride.tool_spec()
