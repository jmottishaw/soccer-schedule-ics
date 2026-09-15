# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Environment

Always use a Python virtual environment:

```bash
# Windows
py -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt
.venv\Scripts\python.exe main.py

# Linux/WSL/macOS
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Running `main.py` generates `soccer_schedule.ics` next to the script
(paths are anchored to the repo directory, not the cwd).

### GitHub Actions Workflow
`.github/workflows/generate_ics.yml`:
- Runs every 20 minutes via cron schedule (also manually via workflow_dispatch)
- Checks out the existing gh-pages branch (shallow, via FETCH_HEAD — the main checkout
  is single-branch so no tracking ref exists), copies the ICS in, and commits/pushes
  only if `git diff --cached` shows a change; output is deterministic so no-op runs
  really are no-ops
- Scheduled workflows get auto-disabled after 60 days of repo inactivity and were
  disabled manually at the end of last season — re-enable in the Actions tab when
  starting a season

## Project Architecture

`main.py` fetches the LISA GameSchedule public API and writes a subscribable ICS:

1. **Data Sources**:
   - Primary: `https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic`
   - Secondary: Exhibition games from `exhibition.csv` (Date,Time,Home Team,Guest Team,Field)

2. **Structure** (`main.py`):
   - Configuration constants at the top of the file (see below)
   - `fetch_league_games()`: API call + BeautifulSoup parse, returns `Schedule_Row` divs
   - `add_league_game()`: parses one row — date/time, teams, field; skips BYE games
     ("--" opponents); time-TBD (or unparseable-time) games become all-day
     placeholders from today through 6 days out, then normal events once timed.
     Played games get the score in the title and the round in the description;
     postponed/cancelled games are kept (regardless of the TBD window) with the
     status prefixed and any league note included. The site reuses the field-name
     div to hold the status word itself when a game has no venue — that text is
     suppressed as a location rather than shown (e.g. `LOCATION:Postponed`)
   - `add_exhibition_game()`: adds one `exhibition.csv` row as a 2-hour event
   - `add_event()`: shared event builder — deterministic UID (date, or date+time for
     timed games, plus summary) and a DTSTAMP derived from the start (never run time),
     so repeat runs are byte-identical, clients don't churn, and a rescheduled game
     becomes a new event rather than a backwards-dated update
   - `generate_ics()`: orchestrates, adds a season-limited VTIMEZONE (Outlook needs
     one for every TZID), writes `soccer_schedule.ics`
   - Safety: `ScheduleError` (non-zero exit, nothing published) on HTTP failure,
     non-empty `p_Error`, zero `Schedule_Row`s, or every row failing to parse —
     an outage must never replace subscribers' calendars with an empty one

3. **Date Handling**:
   - Year determination: month >= 8 (Aug-Dec) → `SEASON_START_YEAR`, else next year
   - All times localized to America/Los_Angeles (Pacific)

## Configuration Constants (top of main.py)

- `COMPETITION` = "19" (U17/18, 2026/27 Fall/Winter)
- `DIVISION_ID` = "-1" (all; team filter is sufficient)
- `TEAM_ID` = "1242" (Lakehill FC U17)
- `SEASON_START_YEAR` = 2026
- `WEEK_MIN` / `WEEK_MAX`: season week window in the API's `year|month|day` format
- `CAL_NAME` / `CAL_DESC`: calendar metadata

To reconfigure for a new team/season, capture the schedule page's network
traffic (or a HAR export) and copy these values from the
`LOAD_SchedulePublic` request payload.

## Dependencies

Pinned in `requirements.txt`: requests, beautifulsoup4, icalendar, pytz.
