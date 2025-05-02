# DONE
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import sys
sys.path.append('../utils')
from team_mapping import team_mapping, team_encoding
from getter import getter

def scrape(year, i):
    """
    Fetches and processes NFL team down statistics for a given year from FootballDB. Returns a dataframe.
    """
    year = year - i
    
    url = f"https://www.footballdb.com/stats/teamstat.html?group=O&cat=W&yr={year}&lg=NFL"

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
    headers = headers[5:]

    df = pd.DataFrame(rows, columns=headers)
    # df.drop([32], inplace=True)
    df['Team'] = df['Team'].apply(lambda x: re.sub(r'(?<=([a-z]))([A-Z].*)', '', x))
    new_cols = []
    for i, col in enumerate(df.columns):
        if i > 0 and i < 6:
            new_cols.append(f"{col}-fds")
        elif i > 5 and i < 9:
            new_cols.append(f"{col}-tde")
        elif i > 8 and i < 12:
            new_cols.append(f"{col}-fde")
        else:
            new_cols.append(col)
    df.columns = new_cols
    df.drop(columns=['Tot-fds', 'Att-tde', 'Made-tde', 'Att-fde', 'Made-fde'], inplace=True)
    df['Team'] = df['Team'].map(team_mapping)
    df['Team'] = df['Team'].map(team_encoding)
    df['year'] = year
    return df

def get_down_stats(year):
    exclude_columns = ['Team', 'year']
    return getter(exclude_columns, scrape, year, ['Team'])

# get_down_stats(2024).to_csv('out.csv', index=False)