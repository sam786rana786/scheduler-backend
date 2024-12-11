from datetime import datetime
from typing import Dict

def get_booking_confirmation_template(event_details: Dict) -> Dict[str, str]:
    """
    Generate HTML and plain text templates for booking confirmation
    """
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563EB;">Booking Confirmed!</h2>
                
                <p>Your meeting with {event_details['host_name']} has been scheduled.</p>
                
                <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1F2937;">{event_details['title']}</h3>
                    
                    <p style="margin-bottom: 8px;">
                        <strong>Date:</strong> {event_details['date']}
                    </p>
                    
                    <p style="margin-bottom: 8px;">
                        <strong>Time:</strong> {event_details['time']}
                    </p>
                    
                    <p style="margin-bottom: 8px;">
                        <strong>Duration:</strong> {event_details['duration']}
                    </p>
                    
                    <p style="margin-bottom: 8px;">
                        <strong>Location:</strong> {event_details['location']}
                    </p>
                </div>

                <p>Need to make changes? Contact {event_details['host_name']} to reschedule or cancel.</p>
                
                <div style="margin-top: 40px; font-size: 14px; color: #6B7280;">
                    <p>Add this event to your calendar:</p>
                    <p>
                        <a href="{event_details.get('google_calendar_link', '#')}" style="color: #2563EB; text-decoration: none; margin-right: 20px;">Google Calendar</a>
                        <a href="{event_details.get('outlook_calendar_link', '#')}" style="color: #2563EB; text-decoration: none;">Outlook Calendar</a>
                    </p>
                </div>
            </div>
        </body>
    </html>
    """

    text_content = f"""
    Booking Confirmed!

    Your meeting with {event_details['host_name']} has been scheduled.

    {event_details['title']}
    
    Date: {event_details['date']}
    Time: {event_details['time']}
    Duration: {event_details['duration']}
    Location: {event_details['location']}

    Need to make changes? Contact {event_details['host_name']} to reschedule or cancel.
    """

    return {
        "html": html_content,
        "text": text_content
    }