from datetime import datetime
import nfl_data_py as nfl
import sys
import pandas as pd
sys.path.append('../utils')
from team_mapping import team_encoding

def get_indiv(year, pos):
    """
    Fetches and processes individual player data for a given year and position group. Returns dataframe.
    """
    
    imp = nfl.import_weekly_data([year])
    ps = imp[imp['position_group'].isin([pos])]
    ps = ps.drop(columns=['season', 'player_id', 'player_name', 'position', 'position_group', 'headshot_url', 'season_type', 'special_teams_tds', 'fantasy_points'])
    ps = ps[['week', 'player_display_name', 'recent_team'] + [col for col in ps.columns if col not in ['week', 'player_display_name', 'recent_team']]]
    ps['recent_team'] = ps['recent_team'].replace('LA', 'LAR')
    ps['recent_team'] = ps['recent_team'].map(team_encoding)
    ps['opponent_team'] = ps['opponent_team'].replace('LA', 'LAR')
    ps['opponent_team'] = ps['opponent_team'].map(team_encoding)
    ps.rename(columns={'recent_team': 'team', 'fantasy_points_ppr': 'points', 'player_display_name': 'player'}, inplace=True)
    if year == 2024:
        new_rows = pd.DataFrame({
            'week': [1, 1],
            'player': ['Christian McCaffrey', 'Isaac Guerendo'],
            'team': [1, 1],  
            'opponent_team': [31, 31],
            'points': [0, 0]
        })
        ps = pd.concat([ps, new_rows], ignore_index=True)
    ps['year'] = year
    ps = ps.fillna(0)
    d = nfl.import_depth_charts([year])[['club_code', 'week', 'full_name', 'depth_team']]
    d['club_code'] = d['club_code'].replace('LA', 'LAR')
    d['club_code'] = d['club_code'].map(team_encoding)
    d.rename(columns={'club_code': 'team', 'full_name': 'player'}, inplace=True)
    d = d.drop_duplicates(subset=['team', 'week', 'player'])
    merged = ps.merge(d, on=['team', 'week', 'player'], how='left')
    
    def fill_depth(group):
        max_depth = group['depth_team'].dropna().astype(int).max() if not group['depth_team'].dropna().empty else 0
        group['depth_team'] = group['depth_team'].fillna(str(max_depth + 1))
        return group
    merged = merged.groupby(['team', 'week'], group_keys=False).apply(fill_depth)
    return merged.sort_values(by=['year', 'week', 'player'], ascending=[False, False, True])

def cum_adjust(current_df, prev_dfs):
    prev_df = pd.concat(prev_dfs)
    prev_totals = prev_df.groupby('player').sum(numeric_only=True)
    adjusted = current_df.copy()
    adjusted = adjusted.sort_values(by=['player', 'week'])

    id_cols = ['week', 'player', 'opponent_team', 'team', 'year', 'points', 'depth_team']
    stat_cols = [col for col in adjusted.columns if col not in id_cols]

    for col in stat_cols:
        adjusted[f'prev_{col}'] = adjusted['player'].map(lambda p: prev_totals.at[p, col] if p in prev_totals.index else 0)
        adjusted[f'cum_{col}'] = 0

    cum_sums = {}

    for i, row in adjusted.iterrows():
        player = row['player']
        if player not in cum_sums:
            cum_sums[player] = {col: 0 for col in stat_cols}
            cum_sums[player]['points'] = 0 
        for col in stat_cols + ['points']:
            adjusted.at[i, f'cum_{col}'] = cum_sums[player][col]
            cum_sums[player][col] += row[col]
            
    adjusted = adjusted[id_cols + [f'prev_{col}' for col in stat_cols] + [f'cum_{col}' for col in stat_cols] + ['cum_points']]
    adjusted.rename(columns={'player': 'player_name'}, inplace=True)
    return adjusted

# d1 = get_indiv(2024, 'RB')
# d2 = get_indiv(2023, 'RB')
# d3 = get_indiv(2022, 'RB')
# d4 = get_indiv(2021, 'RB')
# d1 = cum_adjust(d1, [d4, d3, d2])
# d1.to_pickle('../pickles/rb_2024.pickle')
# d2 = d2 = cum_adjust(d2, [d4, d3])
# d2.to_pickle('../pickles/rb_before_2024.pickle')