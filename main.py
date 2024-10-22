import requests
import json
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime, timedelta
import subprocess

def generate_ics():
    # Request the schedule data
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    payload = {
        "ixCompetition": "6",
        "strFiltersXML": """
            <FILTERS>
                <DATERANGE>
                    <NAME>DATERANGE</NAME>
                    <VALUE>-1</VALUE>
                </DATERANGE>
                <CLUB>
                    <NAME>CLUB</NAME>
                    <VALUE>-1</VALUE>
                </CLUB>
                <DIVISION>
                    <NAME>DIVISION</NAME>
                    <VALUE>69</VALUE>
                </DIVISION>
                <TEAM>
                    <NAME>TEAM</NAME>
                    <VALUE>410</VALUE>
                </TEAM>
                <FIELD>
                    <NAME>FIELD</NAME>
                    <VALUE>-1</VALUE>
                </FIELD>
            </FILTERS>
        """
    }

    # Make the POST request with a 30-second timeout
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
    
    # Parse the response
    json_response = response.json()
    p_content = json_response.get('d', {}).get('p_Content', None)
    
    if not p_content:
        raise Exception("No content found in response.")
    
    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(p_content, 'html.parser')
    games = soup.find_all("div", class_="Schedule_Row")
    
    # Create a new calendar
    calendar = Calendar()

    # Calendar properties
    calendar.add('prodid', 'ics.py - http://git.io/lLljaA')
    calendar.add('x-wr-calname', 'LSA U14BT3 Hart Schedule')
    calendar.add('x-wr-caldesc', 'Game schedule for LSA U14BT3 Hart')
    calendar.add('x-wr-timezone', 'America/Los_Angeles')

    # Timezone definition
    timezone = """
    BEGIN:VTIMEZONE
    TZID:America/Los_Angeles
    BEGIN:DAYLIGHT
    DTSTART:20240310T030000
    TZOFFSETFROM:-0800
    TZOFFSETTO:-0700
    RRULE:FREQ=YEARLY;BYDAY=2SU;BYMONTH=3
    TZNAME:PDT
    END:DAYLIGHT
    BEGIN:STANDARD
    DTSTART:20241103T010000
    TZOFFSETFROM:-0700
    TZOFFSETTO:-0800
    RRULE:FREQ=YEARLY;BYDAY=1SU;BYMONTH=11
    TZNAME:PST
    END:STANDARD
    END:VTIMEZONE
    """
    calendar.add_component(timezone)

    # Month mapping for determining the year
    month_map = {
        'Jan': 1,
        'Feb': 2,
        'Mar': 3,
        'Apr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Aug': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dec': 12
    }

    # Process each game and add it to the calendar
    for game in games:
        date_text = game.find("div", class_="Schedule_Date").b.text.strip()  # Date
        time = game.find("div", class_="Schedule_Date").find_next("div").text.strip()  # Time
        
        if not time or time == "TBD":
            continue
        
        # Extract month and day from the date_text
        month_str, day_str = date_text.split(' - ')[0].split(' ', 1)  # e.g., 'Sep 7'
        day = int(day_str)  # Get the day as an integer
        
        # Determine the year based on the month
        month = month_map[month_str]
        if month >= 8:  # August (8) to December (12)
            event_year = 2024
        else:  # January (1) to May (5)
            event_year = 2025
        
        # Create event date with the determined year
        event_date = datetime(event_year, month, day, hour=int(time.split(':')[0]), minute=int(time.split(':')[1][:2]))  # Set time correctly
        end_date = event_date + timedelta(hours=2)  # Assuming events last 2 hours

        # Home and Guest teams
        field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"
        home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
        guest_team = game.find("div", class_="Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"
        
        # Create a new event for each game
        event = Event()
        event.name = f"{home_team} vs {guest_team}"
        event.begin = event_date
        event.end = end_date  # Set end time
        event.location = field
        event.description = f"Home: {home_team}, Guest: {guest_team}"
        
        # Add the event to the calendar
        calendar.events.add(event)

    # Save the .ics file using serialize()
    with open('soccer_schedule.ics', 'w') as ics_file:
        ics_file.write(calendar.serialize())  # Use serialize() method

    # Set Git user identity before committing
    subprocess.run(["git", "config", "--global", "user.email", "actions@github.com"])  # Use a generic email for commits
    subprocess.run(["git", "config", "--global", "user.name", "GitHub Actions"])  # Use a generic name for commits

    # Commit the new .ics file to the main branch
    subprocess.run(["git", "add", "soccer_schedule.ics"])

    # Check for changes and commit
    commit_result = subprocess.run(
        ["git", "commit", "-m", "Update soccer_schedule.ics"],
        capture_output=True, text=True
    )

    # If no changes to commit, handle it
    if commit_result.returncode != 0:
        if "nothing to commit" in commit_result.stderr:
            print("No changes to commit")
        else:
            raise Exception("Failed to commit changes: " + commit_result.stderr)

    # Push the changes
    subprocess.run(["git", "push", "origin", "main"])

if __name__ == "__main__":
    generate_ics()
