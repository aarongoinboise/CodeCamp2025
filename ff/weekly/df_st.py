# DEFENSE
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
sys.path.append('../utils')
from team_mapping import team_encoding

def get_dfs(year):
    """
    Scrapes and compiles defensive statistics data across weeks from FantasyPros. Returns a dataframe.
    """
    
    week = 1
    original_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
    df = None
    # figure out present_week
    if year < 2024:
        present_week = 23
    else:# 2024
        present_week = 21
        
    while week < present_week:
        headers = original_headers
        url = f"https://www.fantasypros.com/nfl/stats/dst.php?year={year}&week={week}&scoring=PPR&range=week"

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
    df = df.drop(columns=['Rank', 'ROST', 'FPTS/G'])
    df['Player']= df['Player'].str.extract(r'\((.*?)\)', expand=False)
    df = df[['Week', 'Player'] + [col for col in df.columns if col not in ['Week', 'Player']]]
    # replace JAX
    df.replace('JAC', 'JAX', inplace=True)
    df['Player'] = df['Player'].map(team_encoding)
    return df

# get_dfs(2023).to_csv('out.csv', index=False)
# get_dfs(2023)