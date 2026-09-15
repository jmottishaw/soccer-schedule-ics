"""Generate soccer_schedule.ics from the LISA GameSchedule public API.

Fetches the league schedule for the configured team, merges optional
exhibition games from exhibition.csv, and writes a subscribable ICS file.
Output is deterministic for unchanged input so the GitHub Actions publish
step only commits when the schedule actually changes.
"""
import csv
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytz
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vDate, vDatetime

# --- Season / team configuration (update each season) ---
COMPETITION = "19"            # U17/18 competition, 2026/27 Fall/Winter
DIVISION_ID = "-1"            # all divisions; the team filter is sufficient
TEAM_ID = "1242"              # Lakehill FC U17
SEASON_START_YEAR = 2026      # Aug-Dec -> this year, Jan-Jul -> next
WEEK_MIN = "2026|8|10:2026|8|16"
WEEK_MAX = "2027|3|29:2027|4|4"
CAL_NAME = "Lakehill FC U17 Schedule"
CAL_DESC = "Event schedule for Lakehill FC U17 (U17/18 Boys Div 2)"

API_URL = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
BASE_DIR = Path(__file__).resolve().parent  # file paths anchored to the repo, not the cwd
TZ = pytz.timezone("America/Los_Angeles")
GAME_LENGTH = timedelta(hours=2)
TBD_WINDOW = timedelta(days=6)
MONTH_MAP = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}


def load_exhibition_games(path="exhibition.csv"):
    """Read optional exhibition/friendly games; returns [] if the file is absent."""
    try:
        with open(BASE_DIR / path, mode="r", newline="") as csvfile:
            return [row for row in csv.DictReader(csvfile) if row.get("Date")]
    except FileNotFoundError:
        print("No exhibition games found. Skipping.")
        return []


def fetch_league_games():
    """Query the GameSchedule API and return the schedule rows as soup elements."""
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    filters = (
        "<FILTERS>"
        "<DATERANGE><NAME>DATERANGE</NAME><VALUE>-1</VALUE></DATERANGE>"
        "<CLUB><NAME>CLUB</NAME><VALUE>-1</VALUE></CLUB>"
        f"<DIVISION><NAME>DIVISION</NAME><VALUE>{DIVISION_ID}</VALUE></DIVISION>"
        f"<TEAM><NAME>TEAM</NAME><VALUE>{TEAM_ID}</VALUE></TEAM>"
        "<FIELD><NAME>FIELD</NAME><VALUE>-1</VALUE></FIELD>"
        "<GAMES><NAME>GAMES</NAME><VALUE>UNPLAYED</VALUE></GAMES>"
        "</FILTERS>"
    )
    payload = {
        "strCompetition": COMPETITION,
        "strFiltersXML": filters,
        "strWeekMax": WEEK_MAX,
        "strWeekMin": WEEK_MIN,
    }

    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch data. Status code: {response.status_code}\nResponse: {response.text}")

    p_content = response.json().get("d", {}).get("p_Content", None)
    if not p_content:
        raise Exception("No content found in API response.")

    soup = BeautifulSoup(p_content, "html.parser")
    return soup.find_all("div", class_="Schedule_Row")


def add_event(calendar, summary, start, end=None, location=None, description=None, all_day=False):
    """Add one event with a stable UID so calendar clients don't churn on refresh."""
    uid_base = re.sub(r"[^A-Za-z0-9]+", "-", f"{start:%Y%m%d}-{summary}").strip("-").lower()
    event = Event()
    event.add("uid", f"{uid_base}@soccer-schedule-ics")
    # DTSTAMP derived from the game date (not run time) keeps output deterministic.
    event.add("dtstamp", start.astimezone(pytz.utc))
    event.add("summary", summary)
    if all_day:
        event.add("dtstart", vDate(start.date()))
    else:
        event.add("dtstart", vDatetime(start))
        event.add("dtend", vDatetime(end))
    if location:
        event.add("location", location)
    if description:
        event.add("description", description)
    calendar.add_component(event)


def add_league_game(calendar, game):
    """Parse one Schedule_Row and add it to the calendar (skips BYE games)."""
    date_div = game.find("div", class_="Schedule_Date")
    date_text = date_div.b.text.strip()
    time_str = date_div.find_next("div").text.strip()

    month_str, day_str = date_text.split(" - ")[0].split(" ", 1)
    day = int(day_str)
    month = MONTH_MAP[month_str]
    event_year = SEASON_START_YEAR if month >= 8 else SEASON_START_YEAR + 1

    home_div = game.find("div", class_="Schedule_Home_Text")
    away_div = game.find("div", class_="Schedule_Away_Text")
    home_team = home_div.text.strip() if home_div else "--"
    guest_team = away_div.text.strip() if away_div else "--"

    if home_team == "--" or guest_team == "--":
        print(f"Skipping BYE game on {month_str} {day}, {event_year}")
        return

    print(f"Processing: {home_team} vs {guest_team} on {month_str} {day}, {event_year} at {time_str or 'TBD'}")

    if not time_str or time_str == "TBD":
        # Only surface undated games close enough that families need a placeholder.
        event_date = TZ.localize(datetime(event_year, month, day))
        if datetime.now(TZ) <= event_date <= datetime.now(TZ) + TBD_WINDOW:
            add_event(
                calendar,
                f"{home_team} vs {guest_team} (TBD)",
                event_date,
                location=home_team,
                description=f"Home: {home_team}, Guest: {guest_team}. Time TBD.",
                all_day=True,
            )
        return

    event_time = datetime.strptime(time_str, "%I:%M %p")
    start = TZ.localize(datetime(event_year, month, day, event_time.hour, event_time.minute))

    field_div = game.find("div", class_="Schedule_Field_Name")
    field = field_div.text.strip() if field_div else "No Field Assigned"

    add_event(
        calendar,
        f"{home_team} vs {guest_team}",
        start,
        end=start + GAME_LENGTH,
        location=field,
        description=f"Home: {home_team}, Guest: {guest_team}",
    )


def add_exhibition_game(calendar, row):
    """Add one exhibition.csv row (Date,Time,Home Team,Guest Team,Field)."""
    start = TZ.localize(datetime.strptime(f"{row['Date']} {row['Time']}", "%Y-%m-%d %I:%M %p"))
    home_team = row["Home Team"].strip()
    guest_team = row["Guest Team"].strip()
    print(f"Processing exhibition: {home_team} vs {guest_team} on {row['Date']} at {row['Time']}")
    add_event(
        calendar,
        f"{home_team} vs {guest_team} (Exhibition)",
        start,
        end=start + GAME_LENGTH,
        location=row.get("Field", "").strip() or "No Field Assigned",
        description=f"Exhibition game. Home: {home_team}, Guest: {guest_team}",
    )


def generate_ics():
    calendar = Calendar()
    calendar.add("prodid", "-//soccer-schedule-ics//github.com/jmottishaw//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("x-wr-calname", CAL_NAME)
    calendar.add("x-wr-caldesc", CAL_DESC)
    calendar.add("x-wr-timezone", "America/Los_Angeles")

    for game in fetch_league_games():
        try:
            add_league_game(calendar, game)
        except Exception as e:
            print(f"Error processing game: {e}")

    for row in load_exhibition_games():
        try:
            add_exhibition_game(calendar, row)
        except Exception as e:
            print(f"Error processing exhibition game {row}: {e}")

    with open(BASE_DIR / "soccer_schedule.ics", "wb") as ics_file:
        ics_file.write(calendar.to_ical())

    print("Calendar successfully generated: soccer_schedule.ics")


if __name__ == "__main__":
    generate_ics()
