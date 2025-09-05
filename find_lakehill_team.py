import requests
import json
from bs4 import BeautifulSoup
import re

def find_lakehill_team_id():
    """Find the Lakehill SA team ID in U16 Boys Division 2"""
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    
    # Use the correct competition and division
    payload = {
        "strCompetition": "12",
        "strFiltersXML": """
            <FILTERS>
                <DATERANGE>
                    <NAME>DATERANGE</NAME>
                    <VALUE>2025|9|1:2025|9|7</VALUE>
                </DATERANGE>
                <CLUB>
                    <NAME>CLUB</NAME>
                    <VALUE>-1</VALUE>
                </CLUB>
                <DIVISION>
                    <NAME>DIVISION</NAME>
                    <VALUE>161</VALUE>
                </DIVISION>
                <TEAM>
                    <NAME>TEAM</NAME>
                    <VALUE>-1</VALUE>
                </TEAM>
                <FIELD>
                    <NAME>FIELD</NAME>
                    <VALUE>-1</VALUE>
                </FIELD>
                <GAMES>
                    <NAME>GAMES</NAME>
                    <VALUE>-1</VALUE>
                </GAMES>
            </FILTERS>
        """,
        "strWeekMin": "2025|8|18:2025|8|24",
        "strWeekMax": "2026|3|16:2026|3|22"
    }
    
    print("Fetching U16 Boys Division 2 (Tier 3) data...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    json_response = response.json()
    p_content = json_response.get('d', {}).get('p_Content', None)
    
    if not p_content:
        print("No content found")
        return
    
    soup = BeautifulSoup(p_content, 'html.parser')
    games = soup.find_all("div", class_="Schedule_Row")
    
    print(f"Found {len(games)} games in division 161")
    
    # Extract team IDs and names
    teams = {}
    
    for game in games:
        # Check home team
        home_outer = game.find("div", class_="Schedule_HomeOuter")
        if home_outer and home_outer.get('onclick'):
            onclick = home_outer.get('onclick')
            team_id_match = re.search(r'PAGE_LoadTeam\((\d+)\)', onclick)
            if team_id_match:
                team_id = team_id_match.group(1)
                home_text_elem = game.find("div", class_="Schedule_Home_Text")
                if home_text_elem:
                    team_name = home_text_elem.text.strip()
                    if team_name and team_name != "--":
                        teams[team_name] = team_id
        
        # Check away team
        away_outer = game.find("div", class_="Schedule_AwayOuter")
        if away_outer and away_outer.get('onclick'):
            onclick = away_outer.get('onclick')
            team_id_match = re.search(r'PAGE_LoadTeam\((\d+)\)', onclick)
            if team_id_match:
                team_id = team_id_match.group(1)
                away_text_elem = game.find("div", class_="Schedule_Away_Text")
                if away_text_elem:
                    team_name = away_text_elem.text.strip()
                    if team_name and team_name != "--":
                        teams[team_name] = team_id
    
    print("\n=== TEAMS IN U16 BOYS DIVISION 2 (TIER 3) ===")
    for team_name in sorted(teams.keys()):
        team_id = teams[team_name]
        if "Lakehill" in team_name:
            print(f"*** FOUND: {team_name} - Team ID: {team_id} ***")
        else:
            print(f"  {team_name} - Team ID: {team_id}")
    
    # Show first few games to verify
    print("\n=== SAMPLE GAMES ===")
    for i, game in enumerate(games[:5]):
        date_elem = game.find("div", class_="Schedule_Date")
        home_elem = game.find("div", class_="Schedule_Home_Text")
        away_elem = game.find("div", class_="Schedule_Away_Text")
        
        if date_elem and home_elem and away_elem:
            date = date_elem.find("b").text.strip() if date_elem.find("b") else "Unknown"
            home = home_elem.text.strip()
            away = away_elem.text.strip()
            
            print(f"{date}: {home} vs {away}")
    
    return teams

if __name__ == "__main__":
    find_lakehill_team_id()