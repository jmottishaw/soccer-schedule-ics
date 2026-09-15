# Soccer Schedule ICS Generator

A Python script that automatically fetches soccer schedules from the Lower Island Soccer Association (LISA) GameSchedule API and generates an ICS calendar file for easy import into calendar applications.

## Disclaimer

**This is an unofficial, community-created tool** that scrapes data from the LISA GameSchedule website. It is:
- NOT affiliated with or endorsed by the Lower Island Soccer Association
- NOT officially supported - it's a personal hack that may break if the API changes
- Provided as-is with no guarantees - YMMV (Your Mileage May Vary)
- For personal use only

If the schedule stops updating or shows incorrect data, check the official LISA GameSchedule website.

## Features

- 🗓️ Fetches game schedules from the LISA GameSchedule API
- 📅 Generates standard ICS format compatible with all major calendar apps (Google Calendar, Outlook, Apple Calendar, etc.)
- 🔄 Automated updates via GitHub Actions (runs every 20 minutes)
- 📍 Includes game locations (field names) and team information
- ⏰ Handles TBD game times appropriately
- 🎯 Filters for specific team schedules (currently configured for Lakehill FC U17)

## Current Configuration

The script is currently configured for:
- **Team**: Lakehill FC U17 (Team ID: 1242)
- **Division**: U17/18 Boys Div 2 (division filter left at -1; team filter is sufficient)
- **Competition**: 19
- **Season**: 2026-2027 Fall/Winter (Sept 2026 - Aug 2027)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/jmottishaw/soccer-schedule-ics.git
cd soccer-schedule-ics
```

2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Manual Generation

Run the script to generate the ICS file:
```bash
source .venv/bin/activate
python main.py
```

This will create `soccer_schedule.ics` in the current directory.

### Automated Generation (GitHub Actions)

The repository includes a GitHub Actions workflow that:
- Runs every 20 minutes
- Generates an updated ICS file
- Commits it to the `gh-pages` branch
- Makes it available via GitHub Pages

To enable this:
1. Fork this repository to your GitHub account
2. Enable GitHub Actions in your repository settings
3. Enable GitHub Pages from the `gh-pages` branch
4. The ICS file will be available at: `https://YOUR-USERNAME.github.io/soccer-schedule-ics/soccer_schedule.ics`

### Live Calendar Subscription

Once hosted on GitHub Pages, you can subscribe to the live schedule that auto-updates:

**Google Calendar:**
1. Open Google Calendar
2. Click the + next to "Other calendars"
3. Select "From URL"
4. Enter: `https://YOUR-USERNAME.github.io/soccer-schedule-ics/soccer_schedule.ics`
5. Click "Add calendar"

**Apple Calendar:**
1. Open Calendar app
2. File → New Calendar Subscription
3. Enter the URL above
4. Set auto-refresh frequency (recommended: every hour)

**Outlook/Other:**
- Most calendar apps support subscribing to ICS URLs
- Look for "Subscribe to calendar" or "Add from URL" option
- The calendar will automatically sync with updates every 20 minutes via GitHub Actions

## Configuration

To update for a different team or season, edit the constants at the top of `main.py`:

- `COMPETITION`: Competition ID (currently "19")
- `DIVISION_ID`: Division ID (currently -1 = all; team filter does the work)
- `TEAM_ID`: Team ID (currently 1242, Lakehill FC U17)
- `WEEK_MIN` / `WEEK_MAX`: season week window (currently Aug 2026 - Apr 2027)
- `SEASON_START_YEAR`: drives the year logic (Aug-Dec = start year, Jan-Jul = next)
- `CAL_NAME` / `CAL_DESC`: calendar name and description

## Exhibition Games

You can add exhibition/friendly games not in the regular schedule by updating `exhibition.csv`:
```csv
Date,Time,Home Team,Guest Team,Field
2024-11-02,2:30 PM,Peninsula U15T3,Lakehill U14 Tier 3,Blue Heron Turf
```

## Dependencies

- `requests`: HTTP API calls
- `beautifulsoup4`: HTML parsing
- `icalendar`: ICS file generation
- `pytz`: Timezone handling

## File Structure

```
soccer-schedule-ics/
├── main.py                 # Main script
├── requirements.txt        # Python dependencies
├── exhibition.csv         # Optional exhibition games
├── CLAUDE.md             # Development documentation
├── README.md             # This file
├── .gitignore            # Git ignore rules
├── .github/
│   └── workflows/
│       └── generate_ics.yml  # GitHub Actions workflow
└── .venv/                # Virtual environment (not tracked)
```

## Troubleshooting

### No games showing up
- Verify the division and team IDs are correct
- Check that the date range in `strWeekMin` and `strWeekMax` covers the current season
- Ensure the competition ID is correct

### Times showing as TBD
- This is normal for games without scheduled times yet
- The script will only create calendar events for TBD games within the next 6 days

### GitHub Actions failing
- Check that all required secrets are set (if any)
- Ensure the gh-pages branch exists
- Verify GitHub Actions and Pages are enabled

## Finding Team/Division IDs

To find the correct Competition, Division, and Team IDs for your team:

### Method 1: Browser Developer Tools
1. Visit https://lisa.gameschedule.ca
2. Navigate to your team's schedule page
3. Open browser developer tools (F12)
4. Go to the Network tab
5. Look for requests to `LOAD_SchedulePublic` or `LOAD_UpdateFilters`
6. Check the request payload for:
   - `strCompetition`: The competition ID (e.g., "19" for U17/18 in 2026/27)
   - `DIVISION` value in `strFiltersXML`: The division ID (-1 works if you filter by team)
   - `TEAM` value / `ixTeam`: Your specific team ID (e.g., 1242 for Lakehill FC U17)
   - `strWeekMin` / `strWeekMax`: The season week window (copy verbatim)

An exported HAR of the schedule page also works — the same fields are in the
captured `GSServicePublic.asmx` request payloads.

### Method 2: Using the API Explorer (included)
1. Look at the `find_lakehill_team.py` script as an example
2. Modify it to search for your team name
3. Run it to discover the IDs:
```bash
source .venv/bin/activate
python find_lakehill_team.py
```

### Common Competition IDs
- Different age groups typically have different competition IDs
- You may need to try multiple competition IDs to find your team
- The competition ID changes based on the league/age group

## License

This project is for personal/community use only. 

The LISA GameSchedule API and data are property of the Lower Island Soccer Association. This tool merely reformats publicly available schedule data for personal convenience.

Use at your own risk - if this tool causes you to miss a game, that's on you!

## Contributing

Feel free to fork and modify for your own team's schedule. Pull requests for improvements are welcome!