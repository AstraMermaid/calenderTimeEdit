import re
import icalendar
import requests
import sys
from datetime import timedelta

# --- CONFIGURATION ---
ICS_URL = "https://cloud.timeedit.net/bth/web/sched1/ri67oQ5y6X2Z8QQ579895ZQ5ylZ135y2ZX4Y255Q827Xq5l9X0W16Tuo71XVnXol5X896oW8Z5469oogZXb8mcXX9W7W223WQXbqQ5r0ZQQbeZ6u61cn.ics"
OUTPUT_FILE = 'modified_calendar.ics'

COURSE_MAP = {
    'MA1497': 'Transform', 'FY1438': 'Termo',
    'ET2632': 'Projekt 2', 'MT1517': 'Projekt 1'
}

NAME_MAP = {
    'JCH': 'Johan Richter', 'MEO': 'Mattias Eriksson', 'WKA': 'Wlodek Kulesza',
    'RKH': 'Raisa Khamitova', 'IGE': 'Irina Gertsovich', 'JSB': 'Josef Ström',
    'CBG': 'Carolina Bergeling', 'ABR': 'Alessandro Bertoni', 'MJD': 'Majid Joshani',
    'MMU': 'Mohammed Samy Massoum'
}

def modify_event(event):
    # Extract existing data
    summary = str(event.get('summary', ''))
    description = str(event.get('description', ''))
    location = str(event.get('location', ''))
    
    # --- 1. FILTERING ---
    
    # A. Remove unwanted specific topics
    if any(x in summary or x in description for x in ['MA0007', 'Mattestuga']):
        return None

    # B. The "Grupp 2" Exclusivity Rule
    # Combine all text to search for group mentions
    full_text = f"{summary} {description}".lower()
    # If "grupp" or "group" is mentioned, but NOT "grupp 2" / "group 2", discard it.
    if ("grupp" in full_text or "group" in full_text):
        if "grupp 2" not in full_text and "group 2" not in full_text:
            return None

    # --- 2. TIME ADJUSTMENT (Academic Quarter) ---
    if event.get('dtstart'):
        event['dtstart'].dt += timedelta(minutes=15)
        
    # Safety: ensure start isn't shifted past or onto the end time
    if event.get('dtstart') and event.get('dtend'):
        if event['dtstart'].dt >= event['dtend'].dt:
            event['dtstart'].dt -= timedelta(minutes=15)

    # --- 3. PROCESSING SUMMARY (Formatting Names) ---
    parts = [p.strip() for p in summary.split(',')]
    found_instructors = []
    event_type = "Gruppövning" # Default fallback
    
    if parts:
        code = parts[0]
        # Look for instructor initials in the summary string
        for p in parts:
            if p in NAME_MAP:
                found_instructors.append(NAME_MAP[p])
            elif any(keyword in p for keyword in ['Föreläsning', 'Laboration', 'Övning', 'Handledning']):
                event_type = p

        # Apply friendly names from COURSE_MAP
        for prefix, friendly_name in COURSE_MAP.items():
            if code.startswith(prefix):
                event['summary'] = f"{friendly_name}, {event_type}"
                break
    
    # --- 4. CLEAN DESCRIPTION ---
    # Remove technical IDs and clean up whitespace
    clean_desc = re.sub(r'ID \d+', '', description).strip().replace('\n', ' ').strip(', ')
    
    desc_elements = []
    if clean_desc:
        desc_elements.append(clean_desc)
    if found_instructors:
        desc_elements.append(", ".join(found_instructors))
    
    # Re-build the description with instructor names at the end
    event['description'] = " | ".join(desc_elements)
    
    return event

def main():
    try:
        print(f"Downloading calendar from TimeEdit...")
        response = requests.get(ICS_URL)
        response.raise_for_status()
        
        # Load the source calendar
        old_cal = icalendar.Calendar.from_ical(response.content)
        
        # Create a brand new calendar object
        new_cal = icalendar.Calendar()
        new_cal.add('prodid', '-//Modified Calendar//mxm.dk//')
        new_cal.add('version', '2.0')

        event_count = 0
        for component in old_cal.walk('VEVENT'):
            modified = modify_event(component)
            if modified:
                new_cal.add_component(modified)
                event_count += 1

        # Write to file
        with open(OUTPUT_FILE, 'wb') as f:
            f.write(new_cal.to_ical())
            
        print(f"✨ Success! Saved {event_count} events to {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
