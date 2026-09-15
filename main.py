"""Generate soccer_schedule.ics from the LISA GameSchedule public API.

Fetches the league schedule for the configured team, merges optional
exhibition games from exhibition.csv, and writes a subscribable ICS file.
Output is deterministic for unchanged input so the publish step can skip
commits when nothing changed. The script exits non-zero (and publishes
nothing) if the API reports an error or returns no schedule rows, so a
transient outage never replaces subscribers' calendars with an empty one.
"""
import csv
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytz
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, vDatetime

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
TZ_NAME = "America/Los_Angeles"
TZ = pytz.timezone(TZ_NAME)
GAME_LENGTH = timedelta(hours=2)
TBD_WINDOW = timedelta(days=6)
TIME_FORMATS = ("%I:%M %p", "%I:%M%p", "%H:%M")
MONTH_MAP = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}
MONTH_MAP["Sept"] = 9


class ScheduleError(Exception):
    """Raised when the fetched schedule can't be trusted enough to publish."""


def clean_text(text):
    """Collapse the stray double spaces the API puts in some team names."""
    return " ".join(text.split())


def parse_time(time_str):
    """Return (hour, minute) or None when the string isn't a real kickoff time."""
    for fmt in TIME_FORMATS:
        try:
            t = datetime.strptime(time_str, fmt)
            return t.hour, t.minute
        except ValueError:
            continue
    return None


def load_exhibition_games(path="exhibition.csv"):
    """Read optional exhibition/friendly games; returns [] if the file is absent."""
    try:
        # utf-8-sig swallows the BOM Excel writes for "CSV UTF-8" so the Date header matches
        with open(BASE_DIR / path, mode="r", newline="", encoding="utf-8-sig") as csvfile:
            rows = [row for row in csv.DictReader(csvfile) if row.get("Date")]
    except FileNotFoundError:
        print("No exhibition.csv found. Skipping.")
        return []
    if not rows:
        print("exhibition.csv has no games. Skipping.")
    return rows


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
        "<GAMES><NAME>GAMES</NAME><VALUE>-1</VALUE></GAMES>"  # all games, so history stays on the calendar
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
        raise ScheduleError(f"Failed to fetch data. Status code: {response.status_code}\nResponse: {response.text}")

    data = response.json().get("d", {})
    if data.get("p_Error"):
        raise ScheduleError(f"API returned an error: {data['p_Error']}")
    p_content = data.get("p_Content")
    if not p_content:
        raise ScheduleError("No content found in API response.")

    rows = BeautifulSoup(p_content, "html.parser").find_all("div", class_="Schedule_Row")
    if not rows:
        raise ScheduleError("API returned no schedule rows (wrong IDs, season over, or page changed).")
    return rows


def add_event(calendar, summary, start, end=None, location=None, description=None, all_day=False, url=None):
    """Add one event with a stable UID so calendar clients don't churn on refresh.

    The UID encodes the start (date, or date+time for timed games), so a
    rescheduled game becomes a new event rather than an update, and DTSTAMP
    (derived from the start, never from run time) can't move backwards for a
    given UID. A field-only change keeps the UID; subscription clients replace
    the whole feed so that still propagates.
    """
    stamp = f"{start:%Y%m%d}" if all_day else f"{start:%Y%m%dT%H%M}"
    uid_base = re.sub(r"[^A-Za-z0-9]+", "-", f"{stamp}-{summary}").strip("-").lower()
    event = Event()
    event.add("uid", f"{uid_base}@soccer-schedule-ics")
    event.add("dtstamp", start.astimezone(pytz.utc))
    event.add("summary", summary)
    if all_day:
        event.add("dtstart", start.date())  # plain date -> DTSTART;VALUE=DATE
    else:
        event.add("dtstart", vDatetime(start))
        event.add("dtend", vDatetime(end))
    if location:
        event.add("location", location)
    if description:
        event.add("description", description)
    if url:
        event.add("url", url)
    calendar.add_component(event)


def add_league_game(calendar, game):
    """Parse one Schedule_Row and add it to the calendar (skips BYE games)."""
    date_div = game.find("div", class_="Schedule_Date")
    date_text = date_div.b.text.strip()
    time_div = date_div.find("div")  # the time sits inside the date cell; don't wander past it
    time_str = time_div.text.strip() if time_div else ""

    month_str, day_str = date_text.split(" - ")[0].split(" ", 1)
    day = int(day_str)
    month = MONTH_MAP[month_str]
    event_year = SEASON_START_YEAR if month >= 8 else SEASON_START_YEAR + 1
    game_date = date(event_year, month, day)

    home_div = game.find("div", class_="Schedule_Home_Text")
    away_div = game.find("div", class_="Schedule_Away_Text")
    home_team = clean_text(home_div.text) if home_div else "--"
    guest_team = clean_text(away_div.text) if away_div else "--"

    if home_team == "--" or guest_team == "--":
        print(f"Skipping BYE game on {game_date}")
        return

    field_div = game.find("div", class_="Schedule_Field_Name")
    field = clean_text(field_div.text) if field_div else ""
    if field == "No Field Assigned":
        field = ""
    map_match = re.search(r"open\('([^']+)'", field_div.get("onclick", "")) if field_div else None
    map_url = map_match.group(1) if map_match else None

    # Played games carry "1 - 4" as the score box's own text, with the round in a child div
    score_div = game.find("div", class_="Schedule_Score_Box")
    score = clean_text(score_div.find(string=True, recursive=False) or "") if score_div else ""
    round_div = game.find("div", class_="Schedule_VS_Description")
    round_label = clean_text(round_div.text) if round_div else ""
    status_div = game.find("div", class_="Schedule_Status_Text")
    status = clean_text(status_div.text) if status_div else ""  # e.g. Postponed, Cancelled
    notes_div = game.find("div", class_="Schedule_Notes_Text")
    notes = clean_text(notes_div.text).strip("()").strip() if notes_div else ""

    # The site repurposes the field-name div to hold the status word itself when
    # there's no venue (e.g. field text is literally "Postponed") - don't show that as a location.
    if status and field.lower() == status.lower():
        field = ""
        map_url = None

    if status:
        summary = f"{status.upper()}: {home_team} vs {guest_team}"
    elif score:
        summary = f"{home_team} {score} {guest_team}"
    else:
        summary = f"{home_team} vs {guest_team}"
    description = "\n".join(p for p in (
        f"Home: {home_team}, Guest: {guest_team}",
        round_label,
        notes,
        map_url,
    ) if p)

    kickoff = parse_time(time_str)
    print(f"Processing: {summary} on {game_date} at {time_str or 'TBD'}")
    if kickoff is None and time_str and time_str != "TBD":
        print(f"  Unrecognised time '{time_str}'; treating as TBD")

    if kickoff is None:
        today = datetime.now(TZ).date()
        # A postponed/cancelled game stays on its original date as a record; an
        # unscheduled one only gets a placeholder close enough that families need it.
        if status or today <= game_date <= today + TBD_WINDOW:
            add_event(
                calendar,
                summary if status else f"{summary} (TBD)",
                TZ.localize(datetime(event_year, month, day)),
                location=field or None,
                description=description if status else f"{description}\nTime TBD.",
                all_day=True,
                url=map_url,
            )
        return

    start = TZ.localize(datetime(event_year, month, day, *kickoff))
    add_event(
        calendar,
        summary,
        start,
        end=start + GAME_LENGTH,
        location=field or "No Field Assigned",
        description=description,
        url=map_url,
    )


def add_exhibition_game(calendar, row):
    """Add one exhibition.csv row (Date,Time,Home Team,Guest Team,Field)."""
    kickoff = parse_time(row["Time"].strip())
    if kickoff is None:
        raise ValueError(f"unrecognised time '{row['Time']}'")
    start = TZ.localize(datetime.combine(date.fromisoformat(row["Date"].strip()), datetime.min.time()))
    start = start.replace(hour=kickoff[0], minute=kickoff[1])
    home_team = clean_text(row["Home Team"])
    guest_team = clean_text(row["Guest Team"])
    print(f"Processing exhibition: {home_team} vs {guest_team} on {row['Date']} at {row['Time']}")
    add_event(
        calendar,
        f"{home_team} vs {guest_team} (Exhibition)",
        start,
        end=start + GAME_LENGTH,
        location=clean_text(row.get("Field", "")) or "No Field Assigned",
        description=f"Exhibition game. Home: {home_team}, Guest: {guest_team}",
    )


def generate_ics():
    calendar = Calendar()
    calendar.add("prodid", "-//soccer-schedule-ics//github.com/jmottishaw//EN")
    calendar.add("version", "2.0")
    calendar.add("calscale", "GREGORIAN")
    calendar.add("x-wr-calname", CAL_NAME)
    calendar.add("x-wr-caldesc", CAL_DESC)
    calendar.add("x-wr-timezone", TZ_NAME)
    calendar.add("x-published-ttl", "PT1H")

    rows = fetch_league_games()
    failures = 0
    for game in rows:
        try:
            add_league_game(calendar, game)
        except Exception as e:
            failures += 1
            print(f"Error processing game: {e}")
    if failures == len(rows):
        raise ScheduleError(f"All {failures} schedule rows failed to parse; page layout probably changed.")

    for row in load_exhibition_games():
        try:
            add_exhibition_game(calendar, row)
        except Exception as e:
            print(f"Error processing exhibition game {row}: {e}")

    # Clients like Outlook need a VTIMEZONE for every TZID referenced; limit the
    # generated transitions to the season so the file stays small and deterministic.
    calendar.add_missing_timezones(
        first_date=date(SEASON_START_YEAR, 1, 1), last_date=date(SEASON_START_YEAR + 1, 12, 31))

    with open(BASE_DIR / "soccer_schedule.ics", "wb") as ics_file:
        ics_file.write(calendar.to_ical())

    print(f"Calendar successfully generated: soccer_schedule.ics ({len(calendar.walk('VEVENT'))} events)")


if __name__ == "__main__":
    try:
        generate_ics()
    except ScheduleError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
