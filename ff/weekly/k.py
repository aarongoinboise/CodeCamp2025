# Kickers
import requests
from bs4 import BeautifulSoup
import pandas as pd
import nfl_data_py as nfl
import sys
sys.path.append('../utils')
from team_mapping import team_encoding

def get_ks(year):
    """
    Scrapes and processes kicker statistics data for a given NFL season. Returns a dataframe.
    """
    
    week = 1
    original_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
    df = None
    if year < 2024:
        present_week = 23
    else:# 2024
        present_week = 21
        
    while week < present_week:
        headers = original_headers
        url = f"https://www.fantasypros.com/nfl/stats/k.php?year={year}&week={week}&scoring=PPR&range=week"

        # Fetch the page content
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch the page: {response.status_code}")

        # Parse the page content with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        # Locate the table containing the data
        table = soup.find('table')

        # Extract headers
        headers = [header.text.strip() for header in table.find('thead').find_all('th')]
        if df is None:
            headers.append('Week')
            df = pd.DataFrame(columns=headers)

        # Extract rows
        rows = []
        for row in table.find('tbody').find_all('tr'):
            cells = [cell.text.strip() for cell in row.find_all('td')]
            cells.append(week)
            rows.append(cells)

        # append rows
        for row in rows:
            df.loc[len(df)] = row
        week += 1
    df[['Name', 'Team']] = df['Player'].str.extract(r'([A-Za-z\s\']+)\s\((\w+)\)')
    df = df.drop(columns=['Player', 'Team', 'Rank', 'ROST', 'FPTS/G'])
    df = df[['Name', 'Week'] + [col for col in df.columns if col not in ['Name', 'Week']]]
    
    r = nfl.import_weekly_rosters(years=[year])
    r = r[['player_name', 'team', 'week']]
    
    merged_df = pd.merge(
        df,
        r,
        left_on=['Name', 'Week'],
        right_on=['player_name', 'week'],
        how='left'
    )
    df['Team'] = merged_df['team']
    df['Team'] = df['Team'].replace('LA', 'LAR')
    df['Team'] = df['Team'].map(team_encoding)
    
    return df

# get_ks(2023).to_csv('out.csv', index=False)
# get_ks(2023)