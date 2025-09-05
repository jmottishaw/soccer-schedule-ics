import requests
import json
from bs4 import BeautifulSoup
import re

def find_competitions_and_divisions():
    """Try different competition and division combinations"""
    url = "https://lisa.gameschedule.ca/GSServicePublic.asmx/LOAD_SchedulePublic"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }
    
    # Try different competition IDs
    competition_sets = [
        "6|7|10|9",  # Current
        "1|2|3|4|5|6|7|8|9|10|11|12",  # Try more
        "11|12|13|14|15",  # Higher numbers
        "-1"  # All
    ]
    
    found_data = {}
    
    for comp in competition_sets:
        print(f"\nTrying competition: {comp}")
        
        # Try with broader division search
        for div_start in [1, 50, 100, 150, 200]:
            for div_id in range(div_start, div_start + 10):
                payload = {
                    "strCompetition": comp,
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
                    "strWeekMax": "2026|1|31:2026|2|7",
                    "strWeekMin": "2025|9|1:2025|9|7"
                }
                
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=5)
                    
                    if response.status_code == 200:
                        json_response = response.json()
                        p_content = json_response.get('d', {}).get('p_Content', None)
                        
                        if p_content and len(p_content) > 500:  # Has substantial content
                            soup = BeautifulSoup(p_content, 'html.parser')
                            games = soup.find_all("div", class_="Schedule_Row")
                            
                            if games:
                                # Get division info
                                for game in games[:3]:
                                    div_elem = game.find("div", class_="Schedule_Home_Division")
                                    if not div_elem:
                                        div_elem = game.find("div", class_="Schedule_Away_Division")
                                    
                                    if div_elem:
                                        division_name = div_elem.text.strip()
                                        if division_name:
                                            # Look for teams
                                            teams = set()
                                            home = game.find("div", class_="Schedule_Home_Text")
                                            away = game.find("div", class_="Schedule_Away_Text")
                                            
                                            home_team = home.text.strip() if home else ""
                                            away_team = away.text.strip() if away else ""
                                            
                                            if home_team and home_team != "--":
                                                teams.add(home_team)
                                            if away_team and away_team != "--":
                                                teams.add(away_team)
                                            
                                            key = f"{comp}|{div_id}"
                                            found_data[key] = {
                                                'division_name': division_name,
                                                'division_id': div_id,
                                                'competition': comp,
                                                'teams': teams
                                            }
                                            
                                            # Print if it might be U16
                                            if "16" in division_name or "Lakehill" in home_team or "Lakehill" in away_team:
                                                print(f"  *** Found: Division {div_id} = {division_name}")
                                                print(f"      Teams: {home_team} vs {away_team}")
                                            
                                            break  # Found division name, move to next
                except Exception as e:
                    continue
    
    print("\n\n=== ALL DIVISIONS FOUND ===")
    for key, data in sorted(found_data.items(), key=lambda x: x[1]['division_name']):
        div_name = data['division_name']
        div_id = data['division_id']
        comp = data['competition']
        teams_sample = list(data['teams'])[:2]
        
        if "16" in div_name or "Div2" in div_name or any("Lakehill" in t for t in data['teams']):
            print(f"*** Competition: {comp}, Division ID: {div_id}, Name: {div_name}")
            print(f"    Sample teams: {', '.join(teams_sample)}")
        else:
            print(f"Competition: {comp}, Division ID: {div_id}, Name: {div_name}")

if __name__ == "__main__":
    find_competitions_and_divisions()