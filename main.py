from icalendar import vDate

def generate_ics():
    # Request the schedule data (unchanged)
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

    # Fetch the data (unchanged)
    response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}")
    
    json_response = response.json()
    p_content = json_response.get('d', {}).get('p_Content', None)
    if not p_content:
        raise Exception("No content found in response.")
    
    # Parse HTML content (unchanged)
    soup = BeautifulSoup(p_content, 'html.parser')
    games = soup.find_all("div", class_="Schedule_Row")
    
    # Create the calendar (unchanged)
    calendar = Calendar()
    calendar.add('prodid', 'ics.py - http://git.io/lLljaA')
    calendar.add('version', '2.0')
    calendar.add('calscale', 'GREGORIAN')
    calendar.add('x-wr-calname', 'LSA U14BT3 Hart Schedule')
    calendar.add('x-wr-caldesc', 'Event schedule for LSA U14BT3 Hart team')
    calendar.add('x-wr-timezone', 'America/Los_Angeles')

    tz = pytz.timezone('America/Los_Angeles')
    month_map = {m: i for i, m in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1)}

    # Track if a "TBD" game has been added
    tbd_game_added = False

    for game in games:
        try:
            date_text = game.find("div", class_="Schedule_Date").b.text.strip()
            time_str = game.find("div", class_="Schedule_Date").find_next("div").text.strip()

            month_str, day_str = date_text.split(' - ')[0].split(' ', 1)
            day = int(day_str)
            month = month_map[month_str]
            event_year = 2024 if month >= 8 else 2025

            if time_str == "TBD" and not tbd_game_added:
                # Create a placeholder event for "TBD" games, if within 6 days
                event_date = tz.localize(datetime(event_year, month, day))
                if datetime.now(tz) <= event_date <= (datetime.now(tz) + timedelta(days=6)):
                    home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
                    guest_team = game.find("div", "Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"

                    event = Event()
                    event.add('summary', f"{home_team} vs {guest_team} (TBD)")
                    event.add('dtstart', vDate(event_date.date()))  # All-day event
                    event.add('location', home_team)  # Set home team as location if no field is provided
                    event.add('description', f"Home: {home_team}, Guest: {guest_team}. Time and location TBD.")
                    calendar.add_component(event)

                    # Mark the "TBD" game as added
                    tbd_game_added = True
                continue

            if time_str == "TBD":
                continue  # Skip additional "TBD" games if already handled

            # Proceed with regular event creation (unchanged for games with time)
            event_time = datetime.strptime(time_str, "%I:%M %p")
            event_date = tz.localize(datetime(event_year, month, day, event_time.hour, event_time.minute))
            end_date = event_date + timedelta(hours=2)

            field = game.find("div", class_="Schedule_Field_Name").text.strip() if game.find("div", class_="Schedule_Field_Name") else "No Field Assigned"
            home_team = game.find("div", class_="Schedule_Home_Text").text.strip() if game.find("div", class_="Schedule_Home_Text") else "--"
            guest_team = game.find("div", "Schedule_Away_Text").text.strip() if game.find("div", "Schedule_Away_Text") else "--"

            event = Event()
            event.add('summary', f"{home_team.replace('LSA U14BT3 Hart', 'Lakehill U14 Tier 3')} vs {guest_team.replace('LSA U14BT3 Hart', 'Lakehill U14 Tier 3')}")
            event.add('dtstart', vDatetime(event_date))
            event.add('dtend', vDatetime(end_date))
            event.add('location', field)
            event.add('description', f"Home: {home_team.replace('LSA U14BT3 Hart', 'Lakehill')}, Guest: {guest_team.replace('LSA U14BT3 Hart', 'Lakehill')}")

            calendar.add_component(event)

        except Exception as e:
            print(f"Error processing game: {e}")
            continue

    # Save the .ics file (unchanged)
    with open('soccer_schedule.ics', 'wb') as ics_file:
        ics_file.write(calendar.to_ical())

if __name__ == "__main__":
    generate_ics()
