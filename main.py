import requests
import json
from bs4 import BeautifulSoup
from ics import Calendar, Event
from datetime import datetime
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

    # Make the POST request
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

    # Process each game and add it to the calendar
    for game in games:
        date = game.find("div", class_="Schedule_Date").b.text.strip()  # Date
        time = game.find("div", class_="Schedule_Date").find_next("div").text.strip()  # Time
        if not time or time == "TBD":
            continue
        
        # Field, Home, Guest
        field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"
        home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
        guest_team = game.find("div", class_="Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"
        
        # Combine date and time into a datetime object
        event_date = datetime.strptime(f"{date} {time}", "%b %d - %A %I:%M %p")
        
        # Create a new event for each game
        event = Event()
        event.name = f"{home_team} vs {guest_team}"
        event.begin = event_date
        event.location = field
        event.description = f"Home: {home_team}, Guest: {guest_team}"
        
        # Add the event to the calendar
        calendar.events.add(event)

    # Save the .ics file
    with open('soccer_schedule.ics', 'w') as ics_file:
        ics_file.write(str(calendar))

    # Commit the new .ics file to the main branch
    subprocess.run(["git", "add", "soccer_schedule.ics"])
    subprocess.run(["git", "commit", "-m", "Update soccer_schedule.ics"])
    subprocess.run(["git", "push", "origin", "main"])

if __name__ == "__main__":
    generate_ics()
