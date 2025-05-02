# Injuries - just start by searching for each individual player who may play
import os
import pickle
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import re
import sys

sys.path.append('../utils')
from team_mapping import team_encoding
from team_mapping import team_name_mapping
fetched_url_cache = {}

def encode_game_status(status):
    mapping = {
        'Playing': 1,
        'Questionable': 2,
        'Doubtful': 3,
        'Out': 4
    }
    return mapping.get(status, 5)

def encode_practice_status(status):
    """
    Encodes practice status into numerical values for analysis. Returns mapping.
    """
    mapping = {
        'Full': 1,
        'Limited': 2,
        'DNP': 3,
        'Unknown': 4
    }
    return mapping.get(status, 5)

def encode_injuries(injuries, description=False):
    """
    Encodes injury and practice data into numerical values for machine learning. Returns mapping.
    """
        
    
    injuries = injuries.replace("Ribs", "Rib")
    injuries = injuries.replace('Hamstring, Knee', 'Knee, Hamstring')
    injuries = injuries.replace('Right Elbow, Right Shoulder', 'Right Shoulder, Right Elbow')
        
    injury_list = [
        'Knee', 'Right Wrist', 'Hip', 'Hamstring', 'Achilles', 'Thigh', 'Quadricep', 'Foot', 'Toe', 'Ankle', 'Abdomen', 'Rib', 'Back', 
        'Calf', 'Pectoral', 'Groin', 'Oblique', 'Left Hand', 'Right Hand', 'Right Thumb', 'Right Finger', 'Left Finger',
        'Right Shoulder', 'Left Shoulder', 'Right Forearm', 'Right Arm (laceration', 'Right Elbow', 'Right Biceps', 'Collarbone', 'Calf, Quadricep', 'Chest, Pectoral', 'Ankle, Left Hand', 
        'Right Wrist, Shin', 'Right Shoulder,chest', 'Left Wrist, Left Shoulder', 'Right Wrist, Left Biceps', 'Left Shoulder, Right Elbow', 'Right Shoulder, Right Elbow', 'Right Shoulder,left Finger', 'Left Thumb,quadricep', 'Left Shoulder,knee', 'Left Shoulder,quadricep', 'Knee, Hamstring', 'Achilles, Knee', 'Right Wrist, Knee', 'Back, Knee', 'Back, Foot', 'Ankle,ribs', 'Ankle, Hip', 'Ankle, Thigh', 'Ankle,foot', 'Calf, Achilles', 'Heel, Left Elbow', 'Ankle, Coaching Decision', 'Neck,right Finger', 'Left Hand, Concussion', 'Concussion, Left Finger', 'Ankle,concussion', 'Concussion,right Shoulder, Rib', 'Concussion', 'Neck', 'Tooth', 
        'Illness', 'Coach\'s Decision', 'Gameday Concussion Protocol Evaluation'
    ]
    
    if description:
        for injury in injury_list:
            if injury.lower() in injuries.lower():
                injuries = injury
    
    mapping = {injury: i + 1 for i, injury in enumerate(injury_list)}
    player_was_ill_index = len(injury_list) + 1

    if injuries.startswith("Player Was Ill"):
        return player_was_ill_index
    
    if 'Rest' in injuries:
        return player_was_ill_index + 1
    
    if 'Personal' in injuries:
        return player_was_ill_index + 2
    
    if 'Returning From Suspension' in injuries:
        return player_was_ill_index + 3
    
    return mapping.get(injuries, player_was_ill_index + 4) 

def get_injury(team, year, pos, type, week):
    """
    Fetches, processes, and encodes injury data for a given year and position. Returns a DataFrame.
    """
    url = f"https://www.footballdb.com/transactions/injuries.html?yr={year}&wk={week}&type={type}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    if url in fetched_url_cache:
        response = fetched_url_cache[url]
    else:
        response = requests.get(url, headers=headers)
        fetched_url_cache[url] = response
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the page: {response.status_code} url: {url}")

    soup = BeautifulSoup(response.text, 'html.parser')
    injury_data = []
    rows = soup.select("div.divtable-mobile .tr")

    for row in rows:
        cols = row.find_all("div", class_="td")
        if len(cols) < 6:
            continue

        player_info = cols[0].get_text(strip=True)
        if f"({pos})" not in player_info:
            continue

        player_name = player_info.split("(")[0].strip()
        position = pos
        injury = cols[1].get_text(strip=True)
        injury = encode_injuries(injury)
        wed_status = encode_practice_status(cols[2].get_text(strip=True).replace("--", "Unknown"))
        thu_status = encode_practice_status(cols[3].get_text(strip=True).replace("--", "Unknown"))
        fri_status = encode_practice_status(cols[4].get_text(strip=True).replace("--", "Unknown"))
        game_status = re.sub(r"\(\d{2}/\d{2}\)|@ [A-Za-z]+|vs [A-Za-z]+", "", cols[5].get_text(strip=True)).strip()
        game_status = "Playing" if game_status == "--" else game_status
        game_status = encode_game_status(game_status)

        injury_data.append({
            "Year": year,
            "week": week,
            "Team": team_encoding.get(team, -1),
            "Player": player_name,
            "Position": position,
            "Injury": injury,
            "Wed": wed_status,
            "Thu": thu_status,
            "Fri": fri_status,
            "Game Status": game_status
        })
    return pd.DataFrame(injury_data)


def get_curr_injury(year, week, pos, team):
    if team == 'WAS':
        url = f"https://www.espn.com/nfl/team/injuries/_/name/wsh"
    else:
        url = f"https://www.espn.com/nfl/team/injuries/_/name/{team}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
     # Fetch the page content
    if url in fetched_url_cache:
        response = fetched_url_cache[url]
    else:
        response = requests.get(url, headers=headers)
        fetched_url_cache[url] = response
    if response.status_code != 200:
        raise Exception(f"Failed to fetch the page: {response.status_code} url: {url}")

    # Parse the page content with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    pattern = r'"logo":\{"href":"([^"]+)".*?"alt":"([^"]+)".*?"position":"([^"]+)".*?"status":"([^"]+)".*?"description":"([^"]+)"'
    injury_data = []
    for s in soup:
        if s:
            matches = re.findall(pattern, str(s))
            for match in matches:
                _, player_name, position, status, description = match
                injury_data.append({"Player": player_name, "Position": position, "Status": status, "Description": description})
    df = pd.DataFrame([data for data in injury_data if data["Position"] == pos])
    if df.empty:
        return df
    df['Year'] = year
    df['week'] = week
    df["Team"] = team_encoding.get(team, -1)
    df = df.rename(columns={'Status': 'Game Status'})
    df['Injury'] = ''
    df[['Wed', 'Thu', 'Fri']] = ''
    status_map = {'injury-4': 'Out', 'injury-5': 'Out', 'injury-2': 'Questionable'}
    practice_map = {'Out': 'DNP', 'Questionable': 'Limited'}

    for i, row in df.iterrows():
        game_status = row['Game Status']
        smgs = status_map[game_status]
        df.at[i, 'Game Status'] = encode_game_status(smgs)
        prac_status = practice_map[smgs]
        df.at[i, 'Wed'] = encode_practice_status(prac_status)
        df.at[i, 'Thu'] = encode_practice_status(prac_status)
        df.at[i, 'Fri'] = encode_practice_status(prac_status)
        df.at[i, 'Injury'] = encode_injuries(df.at[i, 'Description'], True)
    return df[['Year', 'week', 'Team', 'Player', 'Position', 'Injury', 'Wed', 'Thu', 'Fri', 'Game Status']]

def get_injuries_for_all_teams(year, pos):
    print(f'starting new injury getting for {year} for {pos}')
    all_injuries = []
    
    total = len(team_name_mapping)
    for i, (_, team_code) in enumerate(team_name_mapping.items()):
        if i == total // 4:
            print("25% complete")
        elif i == total // 2:
            print("50% complete")
        elif i == 3 * total // 4:
            print("75% complete")
        if (i == 22) and year == 2024:
            df = get_curr_injury(year, 22, pos, team_code)
            all_injuries.append(df)
        else:
            t = 'reg' if i < 19 else 'post'
            if t == 'reg':
                df = get_injury(team_code, year, pos, t, i)
                # print(df)
                all_injuries.append(df)
            else:
                df = get_injury(team_code, year, pos, t, i-18)
                # print(df)
                all_injuries.append(df)
    
    # Combine all the data frames into one
    combined_df = pd.concat(all_injuries, ignore_index=True)
    combined_df.rename(columns={'Year': 'year', 'Team': 'team', 'Player': 'player_name'}, inplace=True)
    combined_df.drop(columns='Position', inplace=True)
    return combined_df

# inj_before_2024 = pd.concat([get_injuries_for_all_teams(year, 'RB') for year in range(2022, 2024)], ignore_index=True)
# inj_before_2024.to_pickle('../pickles/rb_inj_before_2024.pickle')
# inj_2024 = get_injuries_for_all_teams(2024, 'RB')
# inj_2024.to_pickle('../pickles/rb_inj_2024.pickle')