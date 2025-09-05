# Soccer Schedule ICS Generator

A Python script that automatically fetches soccer schedules from the LSA GameSchedule API and generates an ICS calendar file for easy import into calendar applications.

## Features

- 🗓️ Fetches game schedules from the LSA (Lower Island Soccer Association) GameSchedule API
- 📅 Generates standard ICS format compatible with all major calendar apps (Google Calendar, Outlook, Apple Calendar, etc.)
- 🔄 Automated updates via GitHub Actions (runs every 20 minutes)
- 📍 Includes game locations (field names) and team information
- ⏰ Handles TBD game times appropriately
- 🎯 Filters for specific team schedules (currently configured for Lakehill U16 Division 2 Tier 3)

## Current Configuration

The script is currently configured for:
- **Team**: Lakehill SA (Team ID: 841)
- **Division**: U16 Boys Division 2 (Tier 3) (Division ID: 161)
- **Competition**: 12
- **Season**: 2025-2026 (Sept 2025 - Aug 2026)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/soccer-schedule-ics.git
cd soccer-schedule-ics
```

2. Create a virtual environment (required for WSL):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Manual Generation

Run the script to generate the ICS file:
```bash
source venv/bin/activate
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
1. Push the repository to GitHub
2. Enable GitHub Actions in your repository settings
3. Enable GitHub Pages from the `gh-pages` branch
4. The ICS file will be available at: `https://yourusername.github.io/soccer-schedule-ics/soccer_schedule.ics`

### Live Calendar Subscription

Once hosted on GitHub Pages, you can subscribe to the live schedule that auto-updates:

**Google Calendar:**
1. Open Google Calendar
2. Click the + next to "Other calendars"
3. Select "From URL"
4. Enter: `https://yourusername.github.io/soccer-schedule-ics/soccer_schedule.ics`
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

To update for a different team or season, modify these values in `main.py`:

### API Parameters (lines 32-63)
- `strCompetition`: Competition ID (currently "12")
- `DIVISION VALUE`: Division ID (line 45, currently 161)
- `TEAM VALUE`: Team ID (line 49, currently 841)

### Calendar Metadata (lines 86-87)
- Calendar name and description

### Season Year Logic (line 101)
- Update the month threshold for determining the year
- Current: Sept-Dec = 2025, Jan-Aug = 2026

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
└── venv/                 # Virtual environment (not tracked)
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

To find IDs for a different team:
1. Visit the LSA GameSchedule website
2. Navigate to your team's schedule
3. Use browser developer tools (F12) to monitor network requests
4. Look for `LOAD_SchedulePublic` API calls
5. Check the request payload for division and team values

## License

This project is for personal use. The LSA GameSchedule API is property of the Lower Island Soccer Association.

## Contributing

Feel free to fork and modify for your own team's schedule. Pull requests for improvements are welcome!