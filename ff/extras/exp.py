# DONE
import math
import nfl_data_py as nfl
import numpy as np
import pandas as pd
import sys
sys.path.append('../utils')
from team_mapping import team_encoding

class Exp:
    def __init__(self):
        self.past_exps = {}
        
    def load_past_exps(self, y, e):
        self.past_exps[y] = e

    def get_len(self, year, name, team, pos):
        """
        Calculates the number of consecutive years a player has spent with the same team based on historical data. Returns this number.
        """
        len_val = 1
        while True:
            year -= 1
            if year in self.past_exps:
                p = self.past_exps[year]
            else:
                p = get_exp(year, pos)
                self.load_past_exps(year, p)
            p = p[p['player_name'] == name]
            if p.empty:
                break
            if p['team'].iloc[0] == team:
                len_val += 1
        return len_val
                
    def get_all(self, year, pos):
        df = get_exp(year, pos)
        print('GOT CURR DF')
        p1, p2 = get_exp(year - 1, pos), get_exp(year - 2, pos)
        self.load_past_exps(year - 1, p1)
        self.load_past_exps(year - 2, p2)
        past_df = pd.concat([p1, p2], ignore_index=True)
        print('GOT PAST DFS')
        
        df_len = len(df)
        print(f'START FINDING TEAM LENGTHS with df len {df_len}')
        # process df (current year)
        for j, (i, row) in enumerate(df.iterrows()):
            if j in {round(df_len * 0.25), round(df_len * 0.5), round(df_len * 0.75)}:
                print(f'Progress (current df): {round(j / df_len * 100)}%')
            n, team, pos_name = row['player_name'], row['team'], row['position']
            df.loc[i, 'len_with_team'] = self.get_len(row['year'], n, team, pos_name)
        
        past_len = len(past_df)
        print(f'DONE WITH FIRST DF, second DF len: {past_len}')
        # process past_df (past years)
        for j, (i, row) in enumerate(past_df.iterrows()):
            if j in {round(past_len * 0.25), round(past_len * 0.5), round(past_len * 0.75)}:
                print(f'Progress (past df): {round(j / past_len * 100)}%')
            n, team, pos_name = row['player_name'], row['team'], row['position']
            past_df.loc[i, 'len_with_team'] = self.get_len(row['year'], n, team, pos_name)
        
        print('DONE WITH SECOND DF')
        df['team'] = df['team'].replace('LA', 'LAR')
        df['team'] = df['team'].map(team_encoding)
        df.drop(columns='position', inplace=True)

        past_df['team'] = past_df['team'].replace('LA', 'LAR')
        past_df['team'] = past_df['team'].map(team_encoding)
        past_df.drop(columns='position', inplace=True)
        
        df['age'].fillna(math.floor(df['age'].mean()), inplace=True)
        past_df['age'].fillna(math.floor(df['age'].mean()), inplace=True)

        return df, past_df

def get_exp(year, pos):
    """
    Fetches player experience data for a given position and year using the nfl library. Return a dataframe with relevant columns.
    """
    p = nfl.import_seasonal_rosters([year])
    p = p[p['position'].isin([pos])]
    p['year'] = year
    return p[['year', 'player_name', 'team', 'position', 'age']]

# exp_obj = Exp()
# df, past_df = exp_obj.get_all(2024, 'K')
# past_df.to_pickle('k_before_2024.pickle')
# df.to_pickle('k_2024.pickle')