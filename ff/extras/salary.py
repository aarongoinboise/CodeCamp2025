# DONE
import requests
from bs4 import BeautifulSoup
import pandas as pd
import sys
sys.path.append('../utils')
from team_mapping import team_name_mapping, team_encoding

def get_salaries(pos):
    """
    Scrapes and processes salary data for a given position from OverTheCap. Returns a dataframe.
    """
    
    # URL of the page to scrape
    url = "https://overthecap.com/contracts"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

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

    # Extract rows
    rows = []
    for row in table.find('tbody').find_all('tr'):
        cells = [cell.text.strip() for cell in row.find_all('td')]
        rows.append(cells)

    df = pd.DataFrame(rows, columns=headers)
    df = df[df['Pos.'] == pos]
    df.drop(columns='Pos.', inplace=True)
    df['Team'] = df['Team'].map(team_name_mapping)
    df['Team'] = df['Team'].map(team_encoding)
    
    money_columns = ['Total Value', 'APY', 'Total Guaranteed', 'Avg. Guarantee/Year']
    for col in money_columns:
        df[col] = df[col].replace({r'\$': '', r',': ''}, regex=True).astype(float)

    # Convert percentage strings to decimals
    df['% Guaranteed'] = df['% Guaranteed'].str.replace('%', '').astype(float) / 100
    df.rename(columns={'Player': 'player_name', 'Team': 'team'}, inplace=True)
    return df

# pos_salaries = get_salaries('K')
# pos_salaries.to_pickle('../pickles/k_salaries.pickle')