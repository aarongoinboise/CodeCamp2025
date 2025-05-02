# DONE
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import sys
sys.path.append('../utils')
from team_mapping import team_encoding, coach_team_encoding
from getter import getter

def scrape(year, i):
    # URL of the page to scrape
    year = year - i
    url = f"https://www.pro-football-reference.com/years/{year}/coaches.htm"

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
        coach_name = row.find('th', {'data-stat': 'coach'}).get_text(strip=True)
        cells = [cell.text.strip() for cell in row.find_all('td')]
        cells.insert(0, coach_name)
        rows.append(cells)
    
    headers = headers[8:]
    df = pd.DataFrame(rows, columns=headers)
    df.columns = [f"{col}_{i}" for i, col in enumerate(df.columns)]
    df.columns = [col.rsplit('_', 1)[0] for col in df.columns]
    new_cols = []
    for i, col in enumerate(df.columns):
        if i > 1 and i < 6:
            new_cols.append(f"{col}-season")
        elif (i > 5 and i < 10) or (i > 16 and i < 20):
            new_cols.append(f"{col}-w/team")
        elif (i > 9 and i < 14) or (i > 19 and i < 23): 
            new_cols.append(f"{col}-career") 
        elif i > 13 and i < 17:
            new_cols.append(f"{col}-playoffs") 
        else:
            new_cols.append(col)
    df.columns = new_cols
    
    # go through remark and make week column
    present_week = 23
    week_range = []
    for _, r in df.iterrows():
        first_week = 1
        last_week = present_week - 1
        if 'interim' in r['Remark'].lower():
            first_week = int(re.search(r'\d+', r['Remark']).group()) + 1
        elif 'fired' in r['Remark'].lower():
            last_week = int(re.search(r'\d+', r['Remark']).group())
        week_range.append(f"{first_week}-{last_week}")
    df = df.assign(week_range = week_range)
    
    # Apply expansion to each row
    expanded_df = pd.concat(df.apply(expand_weeks, axis=1).tolist(), ignore_index=True)
    
    expanded_df = expanded_df[['Coach', 'Tm', 'week'] + [col for col in expanded_df.columns if col not in ['Coach', 'Tm', 'week']]]
    df = expanded_df.apply(lambda col: col.map(lambda x: '0' if pd.isna(x) or x == '' else x))
    
    df['Tm'] = df['Tm'].map(coach_team_encoding)
    df['Tm'] = df['Tm'].map(team_encoding)
    
    first_words = df.loc[df['Remark'] != '0', 'Remark'].str.split().str[0]
    unique_first_words = first_words.unique()
    word_to_number = {word: idx + 1 for idx, word in enumerate(unique_first_words)}
    df['Remark'] = df['Remark'].apply(lambda x: word_to_number[x.split()[0]] if x.split() and x.split()[0] in word_to_number else 0)
    df['year'] = year
    df = df[['year', 'week', 'Tm'] + [col for col in df.columns if col not in ['year', 'week', 'Tm']]]
    return df.sort_values(by=['week', 'Tm']).reset_index(drop=True)
    

def get_coaches(year):
    """
    Fetches and processes NFL coach data for a given year from Pro Football Reference. Returns a dataframe.
    """
    exclude_columns = ['year', 'week', 'Tm', 'Coach']
    return getter(exclude_columns, scrape, year, ['Coach', 'week', 'Tm'], True)

def expand_weeks(row):
    """
    Expands the week range for a given coach's week range into individual rows,
    with validation ensuring only relevant weeks are considered.
    """
    start, end = map(int, row['week_range'].split('-'))
    weeks = range(start, end + 1)
    expanded_rows = []
    for week in weeks:
        expanded_rows.append({**row.drop(['week_range']).to_dict(), 'week': week})
    return pd.DataFrame(expanded_rows)

# get_coaches(2023)
# get_coaches(2023).to_csv('out.csv', index=False)