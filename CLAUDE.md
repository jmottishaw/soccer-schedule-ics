# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working Environment

**IMPORTANT**: Always use a Python virtual environment when working in WSL:
```bash
# Create virtual environment if not exists
python3 -m venv venv

# Activate virtual environment for all Python operations
source venv/bin/activate
```

## Common Development Commands

### Install Dependencies
```bash
source venv/bin/activate && pip install -r requirements.txt
```

### Run the Main Script
```bash
source venv/bin/activate && python main.py
```
This generates `soccer_schedule.ics` from the LSA GameSchedule API.

### GitHub Actions Workflow
The project includes automated ICS generation via `.github/workflows/generate_ics.yml` that:
- Runs every 20 minutes via cron schedule
- Can be manually triggered via workflow_dispatch
- Automatically commits generated ICS file to gh-pages branch

## Project Architecture

### Core Functionality
The soccer-schedule-ics project is a web scraper that:

1. **Data Sources**:
   - Primary: LSA GameSchedule API (`https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic`)
   - Secondary: Exhibition games from `exhibition.csv`

2. **Main Components** (`main.py`):
   - `generate_ics()`: Main function that orchestrates the entire process
   - API payload configuration for filtering specific team/division
   - HTML parsing using BeautifulSoup to extract game data
   - ICS calendar generation using icalendar library with Pacific timezone support

3. **Data Processing Flow**:
   - Fetches schedule data using configured competition, division, and team IDs
   - Parses HTML response to extract game dates, times, teams, and field information
   - Filters out BYE games (games with missing teams)
   - Handles TBD times for games within the next week
   - Creates 2-hour calendar events for each game
   - Exports to ICS format for calendar applications

4. **Date Handling Logic** (lines 101-102):
   - **Critical**: Year determination based on month
   - September-December games → current year (2025)
   - January-August games → next year (2026)
   - All times are localized to America/Los_Angeles timezone

### Key Configuration Parameters
When updating for a new season or age group, modify these in `main.py`:

1. **API Payload** (lines 31-63):
   - `strCompetition`: Competition IDs (currently "6|7|10|9")
   - `DIVISION VALUE`: Division ID (line 45, currently 69)
   - `TEAM VALUE`: Team ID (line 49, currently 410)

2. **Calendar Metadata** (lines 86-87):
   - `x-wr-calname`: Calendar display name
   - `x-wr-caldesc`: Calendar description

3. **Year Logic** (line 101):
   - Update the month threshold and year assignments when seasons change

### Dependencies
- `requests`: HTTP API calls
- `beautifulsoup4`: HTML parsing
- `icalendar`: ICS file generation
- `pytz`: Timezone handling