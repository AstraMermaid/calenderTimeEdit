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
    summary = str(event.get('summary', ''))
    description = str(event.get('description', ''))
    
    # 1. FILTERING
    if any(x in summary or x in description for x in ['MA0007', 'Mattestuga']):
        return None

    # 2. TIME ADJUSTMENT (Shift Start ONLY)
    # The end time remains unchanged, effectively shortening the duration.
    if event.get('dtstart'):
        event['dtstart'].dt += timedelta(minutes=15)
    
    # Note: event['dtend'] is intentionally left untouched here.

    # 3. PROCESSING SUMMARY & INSTRUCTORS
    parts = [p.strip() for p in summary.split(',')]
    found_instructors = []
    event_type = "Gruppövning" 
    
    if parts:
        code = parts[0]
        for p in parts:
            if p in NAME_MAP:
                found_instructors.append(NAME_MAP[p])
            elif any(k in p for k in ['Föreläsning', 'Laboration', 'Övning', 'Handledning']):
                event_type = p

        for prefix, friendly_name in COURSE_MAP.items():
            if code.startswith(prefix):
                event['summary'] = f"{friendly_name}, {event_type}"
                break
    
    # 4. CLEAN DESCRIPTION
    clean_desc = re.sub(r'ID \d+', '', description).strip().replace('\n', ' ').strip(', ')
    desc_elements = [clean_desc] if clean_desc else []
    
    if found_instructors:
        desc_elements.append(", ".join(found_instructors))
        
    event['description'] = " | ".join(desc_elements)
    return event
    
def main():
    try:
        print("Starting calendar update with 15-minute shift...")
        response = requests.get(ICS_URL)
        response.raise_for_status()
        
        cal = icalendar.Calendar.from_ical(response.content)
        new_cal = icalendar.Calendar()
        
        for key, value in cal.items():
            new_cal.add(key, value)

        for component in cal.walk('VEVENT'):
            modified = modify_event(component)
            if modified:
                new_cal.add_component(modified)

        with open(OUTPUT_FILE, 'wb') as f:
            f.write(new_cal.to_ical())
        print(f"✨ Success! {OUTPUT_FILE} updated with time shifts.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

