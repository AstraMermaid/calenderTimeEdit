import re
import icalendar
import requests
import sys
from datetime import timedelta

# --- CONFIGURATION ---
ICS_URLS = [
    "https://cloud.timeedit.net/bth/web/sched1/ri681Q2t6Z5Z9QQ5b18QQZ45y1Z736d03X6YZu5Qe97n218172868jElD6Q5j572l76Fj2826m6B282Z06089t8AC6A7362C04006C2.ics",
    "https://cloud.timeedit.net/bth/web/sched1/ri691Q456X1Z29Q599825XQ5yyZ430115XlY155Q417Xy6Z1Zoq1l6XXXW589Xc9Q2o8WXX2l4615XWX57oT6oW9n47W0VZo8gbu3oQequrm6cZbQbZZnQQ150.ics",
]
OUTPUT_FILE = 'modified_calendar.ics'

COURSE_MAP = {
    'ET2632': 'Projekt 2',
    'ET1531': 'Reglerteknik',
    'IY2649': 'Technology venture 1: innovation och affärsutveckling',
    'FY2505': 'Elektromagnetisk fältteori',
    'ET1557': 'Signaler och system, grundkurs',
    'ET2615': 'Elkraft och energiteknik',
    'ET2626': 'Signaler och system, fortsättningskurs',
}

NAME_MAP = {
    'SJO':'Sven Johansson', 'WKA': 'Wlodek Kulesza',
    'RKH': 'Raisa Khamitova', 'IGE': 'Irina Gertsovich', 'JSB': 'Josef Ström',
    'CBG': 'Carolina Bergeling', 'ABR': 'Alessandro Bertoni', 'MJD': 'Majid Joshani',
    'MMU': 'Mohammed Samy Massoum',
    'YIV': 'Yevhen Ivanenko', 'MOH': 'Mojtaba Hosseini', 'HAK': 'Matilda Håkansson',
    'KHE': 'Kennet Henningsson', 'ELO': 'Eva Lövstål', 'AKE': 'Åke Nyström',
    'SKK': 'Siamak Khatibi',
}

EVENT_TYPES = ['Föreläsning', 'Laboration', 'Övning', 'Handledning',
               'Seminarium', 'Workshop', 'Examination']

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
            elif any(keyword in p for keyword in EVENT_TYPES):
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
        # Create a brand new calendar object
        new_cal = icalendar.Calendar()
        new_cal.add('prodid', '-//Modified Calendar//mxm.dk//')
        new_cal.add('version', '2.0')

        event_count = 0
        for url in ICS_URLS:
            print("Downloading calendar from TimeEdit...")
            response = requests.get(url)
            response.raise_for_status()

            # Load the source calendar
            old_cal = icalendar.Calendar.from_ical(response.content)

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
