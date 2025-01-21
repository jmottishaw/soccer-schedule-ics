import requests
import json
import csv
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vDatetime, vDate
from datetime import datetime, timedelta
import pytz

def generate_ics():
    # Load exhibition games
    exhibition_games = []
    try:
        with open('exhibition.csv', mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                exhibition_games.append(row)
    except FileNotFoundError:
        print("No exhibition games found. Skipping.")

    # API Endpoint
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"

    # Headers (Ensure they match what Chrome sent)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    # 🔹 Updated Payload (Formatted for Readability)
    payload = {
        "strCompetition": "6|7|10|9",  # Multiple competitions
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
                <GAMES>
                    <NAME>GAMES</NAME>
                    <VALUE>UNPLAYED</VALUE>
                </GAMES>
            </FILTERS>
        """,
        "strWeekMax": "2025|6|30:2025|7|6",
        "strWeekMin": "2024|7|29:2024|8|4"
    }

    # Send request to API
    response = requests.post(url, headers=headers, json=payload, timeout=60)

    # Check API response
    if response.status_code != 200:
        raise Exception(f"❌ Failed to fetch data. Status code: {response.status_code}\nResponse: {response.text}")

    json_response = response.json()
    p_content = json_response.get('d', {}).get('p_Content', None)
    if not p_content:
        raise Exception("❌ No content found in API response.")

    # Parse HTML content
    soup = BeautifulSoup(p_content, 'html.parser')
    games = soup.find_all("div", class_="Schedule_Row")

    # Create the calendar
    calendar = Calendar()
    calendar.add('prodid', 'ics.py - http://git.io/lLljaA')
    calendar.add('version', '2.0')
    calendar.add('calscale', 'GREGORIAN')
    calendar.add('x-wr-calname', 'LSA U14BT3 Hart Schedule')
    calendar.add('x-wr-caldesc', 'Event schedule for LSA U14BT3 Hart team')
    calendar.add('x-wr-timezone', 'America/Los_Angeles')

    tz = pytz.timezone('America/Los_Angeles')
    month_map = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}

    for game in games:
        try:
            date_text = game.find("div", class_="Schedule_Date").b.text.strip()
            time_str = game.find("div", class_="Schedule_Date").find_next("div").text.strip()

            month_str, day_str = date_text.split(' - ')[0].split(' ', 1)
            day = int(day_str)
            month = month_map[month_str]
            event_year = 2024 if month >= 8 else 2025

            home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
            guest_team = game.find("div", "Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"

            # Skip BYE games
            if home_team == "--" or guest_team == "--":
                print(f"Skipping BYE game on {month_str} {day}, {event_year}")
                continue

            print(f"Processing: {home_team} vs {guest_team} on {month_str} {day}, {event_year} at {time_str}")

            if not time_str or time_str == "TBD":
                event_date = tz.localize(datetime(event_year, month, day))
                if datetime.now(tz) <= event_date <= (datetime.now(tz) + timedelta(days=6)):
                    event = Event()
                    event.add('summary', f"{home_team} vs {guest_team} (TBD)")
                    event.add('dtstart', vDate(event_date.date()))
                    event.add('location', home_team)
                    event.add('description', f"Home: {home_team}, Guest: {guest_team}. Time TBD.")
                    calendar.add_component(event)
                continue

            event_time = datetime.strptime(time_str, "%I:%M %p")
            event_date = tz.localize(datetime(event_year, month, day, event_time.hour, event_time.minute))
            end_date = event_date + timedelta(hours=2)

            field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"

            event = Event()
            event.add('summary', f"{home_team} vs {guest_team}")
            event.add('dtstart', vDatetime(event_date))
            event.add('dtend', vDatetime(end_date))
            event.add('location', field)
            event.add('description', f"Home: {home_team}, Guest: {guest_team}")

            calendar.add_component(event)

        except Exception as e:
            print(f"❌ Error processing game: {e}")
            continue

    # Save the .ics file
    with open('soccer_schedule.ics', 'wb') as ics_file:
        ics_file.write(calendar.to_ical())

    print("✅ Calendar successfully generated: soccer_schedule.ics")

if __name__ == "__main__":
    generate_ics()
