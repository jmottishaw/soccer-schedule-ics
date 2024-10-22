# Assuming the month is in the format 'Sep', 'Oct', etc.
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

# Get the current year
current_year = datetime.now().year  # Get the current year

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

    # Create a new event for each game
    event = Event()
    event.name = f"{home_team} vs {guest_team}"
    event.begin = event_date
    event.location = field
    event.description = f"Home: {home_team}, Guest: {guest_team}"
    
    # Add the event to the calendar
    calendar.events.add(event)
