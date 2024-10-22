import requests
import json
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vDatetime, Timezone, TimezoneStandard, TimezoneDaylight
from datetime import datetime, timedelta, timezone

def generate_ics():
    # Request the schedule data
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0',
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
    
    # Add calendar properties
    calendar.add('prodid', 'ics.py - http://git.io/lLljaA')
    calendar.add('version', '2.0')
    calendar.add('calscale', 'GREGORIAN')
    calendar.add('x-wr-calname', 'LSA U14BT3 Hart Schedule')
    calendar.add('x-wr-caldesc', 'Event schedule for LSA U14BT3 Hart team')
    calendar.add('x-wr-timezone', 'America/Los_Angeles')

    # Add Timezone information for America/Los_Angeles
    tz = Timezone()
    tz.add('tzid', 'America/Los_Angeles')

    # Standard time (PST)
    standard = TimezoneStandard()
    standard.add('dtstart', datetime(2024, 11, 3, 2, 0, 0))  # Daylight savings end date (2024)
    standard.add('tzoffsetfrom', timedelta(hours=-7))  # Offset during daylight savings (PDT)
    standard.add('tzoffsetto', timedelta(hours=-8))  # Offset during standard time (PST)
    standard.add('tzname', 'PST')
    tz.add_component(standard)

    # Daylight savings time (PDT)
    daylight = TimezoneDaylight()
    daylight.add('dtstart', datetime(2024, 3, 10, 2, 0, 0))  # Daylight savings start date (2024)
    daylight.add('tzoffsetfrom', timedelta(hours=-8))  # Offset during standard time (PST)
    daylight.add('tzoffsetto', timedelta(hours=-7))  # Offset during daylight savings (PDT)
    daylight.add('tzname', 'PDT')
    tz.add_component(daylight)

    calendar.add_component(tz)

    # Mapping of month abbreviations to numbers
    month_map = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}

    for game in games:
        # Extract date and time
        date_text = game.find("div", class_="Schedule_Date").b.text.strip()
        time_str = game.find("div", class_="Schedule_Date").find_next("div").text.strip()
        
        if not time_str or time_str == "TBD":
            continue  # Skip events without a defined time
        
        month_str, day_str = date_text.split(' - ')[0].split(' ', 1)
        day = int(day_str)
        month = month_map.get(month_str, None)

        if month is None:
            print(f"Invalid month string: {month_str}")
            continue

        # Use 2024 as the base year, adjust year if necessary
        event_year = 2024 if month >= 8 else 2025

        try:
            # Create timezone-aware datetime object in UTC-08:00
            event_date = datetime(event_year, month, day, hour=int(time_str.split(':')[0]), minute=int(time_str.split(':')[1][:2]), tzinfo=timezone(timedelta(hours=-8)))
            end_date = event_date + timedelta(hours=2)  # Assume 2-hour duration
        except Exception as e:
            print(f"Error parsing date: {e}")
            continue

        # Extract team and field info
        field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"
        home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
        guest_team = game.find("div", class_="Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"
        
        # Create the event
        event = Event()
        event.add('summary', f"{home_team} vs {guest_team}")
        event.add('dtstart', vDatetime(event_date))
        event.add('dtend', vDatetime(end_date))
        event.add('location', field)
        event.add('description', f"Home: {home_team}, Guest: {guest_team}")

        # Add the event to the calendar
        calendar.add_component(event)

    # Save the .ics file
    with open('soccer_schedule.ics', 'wb') as ics_file:
        ics_file.write(calendar.to_ical())

if __name__ == "__main__":
    generate_ics()
