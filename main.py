import requests
import json
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vDatetime, Timezone, TimezoneStandard, TimezoneDaylight
from datetime import datetime, timedelta
import pytz

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
    calendar.add('version', '2.0')  # Required by iCalendar spec
    calendar.add('calscale', 'GREGORIAN')  # Ensures standard calendar format
    calendar.add('x-wr-calname', 'LSA U14BT3 Hart Schedule')  # Calendar name
    calendar.add('x-wr-caldesc', 'Event schedule for LSA U14BT3 Hart team')  # Calendar description
    calendar.add('x-wr-timezone', 'America/Los_Angeles')  # Timezone declaration

    # Timezone setup using pytz
    tz = pytz.timezone('America/Los_Angeles')

    # Month mapping for determining the year
    month_map = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}

    for game in games:
        try:
            # Extract date and time
            date_text = game.find("div", class_="Schedule_Date").b.text.strip()  # Date
            time_str = game.find("div", class_="Schedule_Date").find_next("div").text.strip()  # Time
            
            if not time_str or time_str == "TBD":
                continue  # Skip events without a defined time

            month_str, day_str = date_text.split(' - ')[0].split(' ', 1)  # e.g., 'Sep 7'
            day = int(day_str)  # Extract day as an integer
            month = month_map[month_str]  # Map month abbreviation to a number
            event_year = 2024 if month >= 8 else 2025  # Assume events after August are in the current year, others in the next

            # Parse time and create timezone-aware datetime object using pytz
            hour, minute = map(int, time_str.split(':'))
            event_date = tz.localize(datetime(event_year, month, day, hour, minute))

            # Event end time (assumed to be 2 hours later)
            end_date = event_date + timedelta(hours=2)
            
            # Extract team and field info
            field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"
            home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
            guest_team = game.find("div", class_="Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"
            
            # Create the event
            event = Event()
            event.add('summary', f"{home_team} vs {guest_team}")  # Event title
            event.add('dtstart', vDatetime(event_date))  # Event start time
            event.add('dtend', vDatetime(end_date))  # Event end time
            event.add('location', field)  # Event location
            event.add('description', f"Home: {home_team}, Guest: {guest_team}")  # Description with teams

            # Add the event to the calendar
            calendar.add_component(event)

        except Exception as e:
            print(f"Error processing game: {e}")
            continue

    # Save the .ics file
    with open('soccer_schedule.ics', 'wb') as ics_file:
        ics_file.write(calendar.to_ical())

if __name__ == "__main__":
    generate_ics()
