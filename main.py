import requests
import json
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vDatetime
from datetime import datetime, timedelta, timezone

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

    # Make the POST request
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
    
    json_response = response.json()
    p_content = json_response.get('d', {}).get('p_Content', None)
    
    if not p_content:
        raise Exception("No content found in response.")
    
    # Parse HTML content
    soup = BeautifulSoup(p_content, 'html.parser')
    games = soup.find_all("div", class_="Schedule_Row")
    
    # Create a new calendar
    calendar = Calendar()

    # Set Calendar properties
    calendar.add('prodid', 'ics.py - http://git.io/lLljaA')
    calendar.add('x-wr-calname', 'LSA U14BT3 Hart Schedule')
    calendar.add('x-wr-caldesc', 'Event schedule for LSA U14BT3 Hart team')
    calendar.add('x-wr-timezone', 'America/Los_Angeles')

    # Define the timezone offset for America/Los_Angeles
    tz_offset = timezone(timedelta(hours=-8))  # Standard time offset (PST)

    # Month mapping for determining the year
    month_map = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}

    for game in games:
        date_text = game.find("div", class_="Schedule_Date").b.text.strip()  # Date
        time_str = game.find("div", class_="Schedule_Date").find_next("div").text.strip()  # Time
        
        if not time_str or time_str == "TBD":
            continue
        
        month_str, day_str = date_text.split(' - ')[0].split(' ', 1)  # e.g., 'Sep 7'
        day = int(day_str)  # Get the day as an integer
        month = month_map[month_str]
        event_year = 2024 if month >= 8 else 2025
        
        # Create a timezone-aware datetime object
        event_date = datetime(event_year, month, day, hour=int(time_str.split(':')[0]), minute=int(time_str.split(':')[1][:2]), tzinfo=tz_offset)
        end_date = event_date + timedelta(hours=2)  # Assuming events last 2 hours

        # Home and Guest teams
        field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"
        home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
        guest_team = game.find("div", class_="Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"
        
        # Create event
        event = Event()
        event.add('summary', f"{home_team} vs {guest_team}")
        event.add('dtstart', vDatetime(event_date))
        event.add('dtend', vDatetime(end_date))
        event.add('location', field)
        event.add('description', f"Home: {home_team}, Guest: {guest_team}")
        
        # Add event to calendar
        calendar.add_component(event)

    # Save the .ics file
    with open('soccer_schedule.ics', 'w') as ics_file:
        ics_file.write(calendar.to_ical().decode('utf-8'))

if __name__ == "__main__":
    generate_ics()
