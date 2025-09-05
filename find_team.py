import requests
import json
from bs4 import BeautifulSoup
import re

def find_u16_teams():
    """Search for U16 teams and divisions"""
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    
    # Search with a wider date range
    payload = {
        "strCompetition": "6|7|10|9",
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
                    <VALUE>-1</VALUE>
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
                    <VALUE>ALL</VALUE>
                </GAMES>
            </FILTERS>
        """,
        "strWeekMax": "2025|12|31:2026|1|6",
        "strWeekMin": "2025|9|1:2025|9|7"
    }
    
    print("Searching for U16 teams and divisions...")
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return
    
    json_response = response.json()
    p_content = json_response.get('d', {}).get('p_Content', None)
    
    if not p_content:
        print("No content found")
        return
    
    soup = BeautifulSoup(p_content, 'html.parser')
    
    # Look for team IDs and division info
    team_divisions = {}
    
    # Find all games
    games = soup.find_all("div", class_="Schedule_Row")
    print(f"\nFound {len(games)} games total")
    
    for game in games:
        # Home team
        home_outer = game.find("div", class_="Schedule_HomeOuter")
        if home_outer and home_outer.get('onclick'):
            onclick = home_outer.get('onclick')
            team_id_match = re.search(r'PAGE_LoadTeam\((\d+)\)', onclick)
            if team_id_match:
                team_id = team_id_match.group(1)
                
                home_text = game.find("div", class_="Schedule_Home_Text")
                home_div = game.find("div", class_="Schedule_Home_Division")
                
                if home_text and home_div:
                    team_name = home_text.text.strip()
                    division = home_div.text.strip()
                    
                    if team_name and team_name != "--":
                        if team_name not in team_divisions:
                            team_divisions[team_name] = {}
                        team_divisions[team_name][division] = team_id
        
        # Away team
        away_outer = game.find("div", class_="Schedule_AwayOuter")
        if away_outer and away_outer.get('onclick'):
            onclick = away_outer.get('onclick')
            team_id_match = re.search(r'PAGE_LoadTeam\((\d+)\)', onclick)
            if team_id_match:
                team_id = team_id_match.group(1)
                
                away_text = game.find("div", class_="Schedule_Away_Text")
                away_div = game.find("div", class_="Schedule_Away_Division")
                
                if away_text and away_div:
                    team_name = away_text.text.strip()
                    division = away_div.text.strip()
                    
                    if team_name and team_name != "--":
                        if team_name not in team_divisions:
                            team_divisions[team_name] = {}
                        team_divisions[team_name][division] = team_id
    
    # Filter for U16 and Lakehill
    print("\n=== U16 TEAMS AND DIVISIONS ===")
    u16_found = False
    for team_name, divisions in sorted(team_divisions.items()):
        for division, team_id in divisions.items():
            if "U16" in division or "16B" in division:
                u16_found = True
                if "Lakehill" in team_name:
                    print(f"*** MATCH: {team_name} - Division: {division} - Team ID: {team_id} ***")
                else:
                    print(f"  {team_name} - Division: {division} - Team ID: {team_id}")
    
    if not u16_found:
        print("No U16 teams found in current data")
    
    print("\n=== ALL LAKEHILL TEAMS ===")
    for team_name, divisions in sorted(team_divisions.items()):
        if "Lakehill" in team_name:
            for division, team_id in divisions.items():
                print(f"  {team_name} - Division: {division} - Team ID: {team_id}")
    
    print("\n=== ALL UNIQUE DIVISIONS ===")
    all_divisions = set()
    for team_name, divisions in team_divisions.items():
        for division in divisions.keys():
            all_divisions.add(division)
    
    for div in sorted(all_divisions):
        if "16" in div or "Div2" in div or "T3" in div or "Tier 3" in div.lower():
            print(f"  {div} *** POTENTIAL MATCH")
        else:
            print(f"  {div}")

if __name__ == "__main__":
    find_u16_teams()