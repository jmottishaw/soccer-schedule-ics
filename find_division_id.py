import requests
import json
from bs4 import BeautifulSoup
import re

def try_division_range():
    """Try different division IDs to find U16"""
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    
    # Try division IDs around 69 (current U14 division)
    # U16 might be a higher number
    found_divisions = {}
    
    print("Testing division IDs from 65 to 85...")
    for div_id in range(65, 86):
        payload = {
            "strCompetition": "6|7|10|9",
            "strFiltersXML": f"""
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
                        <VALUE>{div_id}</VALUE>
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
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                json_response = response.json()
                p_content = json_response.get('d', {}).get('p_Content', None)
                
                if p_content and len(p_content) > 100:  # Has content
                    soup = BeautifulSoup(p_content, 'html.parser')
                    games = soup.find_all("div", class_="Schedule_Row")
                    
                    if games:
                        # Get division name from first game
                        div_elem = games[0].find("div", class_="Schedule_Home_Division")
                        if not div_elem:
                            div_elem = games[0].find("div", class_="Schedule_Away_Division")
                        
                        if div_elem:
                            division_name = div_elem.text.strip()
                            if division_name:
                                found_divisions[div_id] = division_name
                                
                                # Check for teams in this division
                                teams = set()
                                for game in games[:5]:
                                    home = game.find("div", class_="Schedule_Home_Text")
                                    away = game.find("div", class_="Schedule_Away_Text")
                                    if home and home.text.strip() != "--":
                                        teams.add(home.text.strip())
                                    if away and away.text.strip() != "--":
                                        teams.add(away.text.strip())
                                
                                if "16" in division_name or "Lakehill" in str(teams):
                                    print(f"*** Division {div_id}: {division_name} - Teams: {', '.join(sorted(teams)[:3])}...")
                                else:
                                    print(f"Division {div_id}: {division_name}")
        except Exception as e:
            continue
    
    print("\n=== SUMMARY ===")
    for div_id, div_name in sorted(found_divisions.items()):
        if "16" in div_name or "Div2" in div_name or "T3" in div_name:
            print(f"Division ID {div_id}: {div_name} *** POTENTIAL MATCH")
        else:
            print(f"Division ID {div_id}: {div_name}")

if __name__ == "__main__":
    try_division_range()