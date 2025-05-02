# DONE
import nfl_data_py as nfl
import pandas as pd
import sys
sys.path.append('../utils')
from team_mapping import team_encoding
from sklearn.preprocessing import LabelEncoder

def get_game_data(year):
    """
    Fetches and processes NFL game data for a given year from the nfl library. Returns a dataframe.
    """
    p = nfl.import_schedules([year])
    p = p.drop(columns=['game_id', 'season', 'game_type', 'away_score', 'home_score', 'location', 'result', 'total', 'overtime', 'old_game_id', 'gsis', 'nfl_detail_id', 'pfr', 'pff', 'espn', 'ftn', 'away_qb_id', 'home_qb_id', 'stadium_id', 'away_rest', 'home_rest'])
    # p['week'] = p['week'].astype(str)
    home_df = p.copy()
    home_df['team'] = home_df['home_team']
    
    away_df = p.copy()
    away_df['team'] = away_df['away_team']
    
    # Combine both DataFrames
    result = pd.concat([home_df, away_df], ignore_index=True)
    result.drop(['away_qb_name', 'home_qb_name', 'away_coach', 'home_coach'], axis=1, inplace=True)
    
    result = result.fillna(value='unknown')
    
    result['temp'] = result['temp'].replace('unknown', -1)
    result['wind'] = result['wind'].replace('unknown', -1)
    
    # encode all team vals
    result['away_team'] = result['away_team'].replace('LA', 'LAR')
    result['home_team'] = result['home_team'].replace('LA', 'LAR')
    result['team'] = result['team'].replace('LA', 'LAR')
    result['away_team'] = result['away_team'].map(team_encoding)
    result['home_team'] = result['home_team'].map(team_encoding)
    result['team'] = result['team'].map(team_encoding)
    
    # labels for rest
    columns_to_encode = ['roof', 'surface', 'referee', 'stadium', 'gameday', 'weekday', 'gametime']
    label_encoders = {col: LabelEncoder() for col in columns_to_encode}
    for col in columns_to_encode:
        try:
            result[col] = label_encoders[col].fit_transform(result[col])
        except Exception as e:
            print(f"Error encoding column: {col}")
            print(f"Column values: {result[col].unique()}")
            print(f"Error: {e}")
    
    # Add Bye Weeks (teams not playing on certain weeks)
    all_teams = result['team'].unique()
    weeks = range(1, 19)  # Adjust weeks depending on year

    bye_rows = []
    for team in all_teams:
        for week in weeks:
            if not result[(result['team'] == team) & (result['week'] == week)].any().any():
                # Insert a bye week row
                bye_rows.append({'bye_week': week, 'team': team})
    
    # Combine bye weeks
    bye_df = pd.DataFrame(bye_rows)

    # Merge bye weeks
    result['year'] = year
    result = pd.merge(result, bye_df, on=['team'], how='left')
    result = result[['year', 'week', 'team'] + [col for col in result.columns if col not in ['year', 'week', 'team']]]
    return result.sort_values(by=['week', 'team']).reset_index(drop=True)

# get_game_data(2023)