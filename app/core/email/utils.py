from datetime import datetime
from typing import Dict

def generate_calendar_links(event_details: Dict) -> Dict[str, str]:
    """
    Generate calendar links for Google Calendar and Outlook
    
    Args:
        event_details: Dictionary containing event details
            {
                'title': str,
                'date': str,
                'time': str,
                'duration': str,
                'location': str,
                'description': str
            }
    """
    # Parse start time
    start_time = datetime.strptime(f"{event_details['date']} {event_details['time']}", 
                                 "%A, %B %d, %Y %I:%M %p")
    
    # Parse duration
    duration_mins = int(event_details['duration'].split()[0])
    
    # Format description
    description = f"""
    Meeting with {event_details['host_name']}
    
    Location: {event_details['location']}
    Duration: {event_details['duration']}
    
    {event_details.get('description', '')}
    """
    
    # Generate Google Calendar link
    google_link = (
        "https://calendar.google.com/calendar/render"
        f"?action=TEMPLATE"
        f"&text={event_details['title']}"
        f"&dates={start_time.strftime('%Y%m%dT%H%M%S')}/{start_time.strftime('%Y%m%dT%H%M%S')}"
        f"&details={description}"
        f"&location={event_details['location']}"
    )
    
    # Generate Outlook link
    outlook_link = (
        "https://outlook.live.com/calendar/0/deeplink/compose"
        f"?subject={event_details['title']}"
        f"&startdt={start_time.isoformat()}"
        f"&enddt={start_time.isoformat()}"
        f"&body={description}"
        f"&location={event_details['location']}"
    )
    
    return {
        "google_calendar_link": google_link,
        "outlook_calendar_link": outlook_link
    }