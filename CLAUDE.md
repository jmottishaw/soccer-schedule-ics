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
- Commits the generated ICS file to the gh-pages branch
- Output is deterministic for unchanged input, so no-op runs don't create commits

## Project Architecture

`main.py` fetches the LISA GameSchedule public API and writes a subscribable ICS:

1. **Data Sources**:
   - Primary: `https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic`
   - Secondary: Exhibition games from `exhibition.csv` (Date,Time,Home Team,Guest Team,Field)

2. **Structure** (`main.py`):
   - Configuration constants at the top of the file (see below)
   - `fetch_league_games()`: API call + BeautifulSoup parse, returns `Schedule_Row` divs
   - `add_league_game()`: parses one row — date/time, teams, field; skips BYE games
     ("--" opponents); TBD-time games become all-day placeholders only within the
     next 6 days
   - `add_exhibition_game()`: adds one `exhibition.csv` row as a 2-hour event
   - `add_event()`: shared event builder — stable deterministic UID per game and a
     DTSTAMP derived from the game date (never run time), so repeat runs produce
     byte-identical output and calendar clients don't churn on refresh
   - `generate_ics()`: orchestrates and writes `soccer_schedule.ics`

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
