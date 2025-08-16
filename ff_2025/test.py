import pandas as pd
import numpy as np
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')

def get_player_data():
    """Get the core player data we need"""
    print("Fetching player data...")
    
    # Get seasonal stats (this has the fantasy points)
    years = [2021, 2022, 2023, 2024]
    seasonal_stats = nfl.import_seasonal_data(years=years)
    
    # Get weekly data (this has player names and positions)
    weekly_data = nfl.import_weekly_data(years=years)
    
    # Get player info (names, positions, teams) from weekly data
    player_info = weekly_data.groupby('player_id').agg({
        'player_name': 'first',
        'player_display_name': 'first', 
        'position': 'first',
        'recent_team': 'last'  # Most recent team
    }).reset_index()
    
    # Try to get current rosters for 2025 team assignments
    try:
        print("Getting current roster/team data...")
        depth_charts = nfl.import_depth_charts([2024])  
        current_teams = depth_charts.groupby('gsis_id').agg({
            'team': 'first',
            'position': 'first',
            'depth_team': 'first'
        }).reset_index()
        current_teams = current_teams.rename(columns={'gsis_id': 'player_id', 'team': 'current_team_2025'})
    except:
        print("Could not get current team data")
        current_teams = pd.DataFrame()
    
    return seasonal_stats, weekly_data, player_info, current_teams

def get_all_draft_data():
    """Get draft data for all years including 2025"""
    print("Getting draft data for all years...")
    
    draft_data_list = []
    
    # Get historical draft data (2021-2024)
    for year in [2021, 2022, 2023, 2024]:
        try:
            draft_year = nfl.import_draft_picks([year])
            if not draft_year.empty:
                draft_year_clean = draft_year[['gsis_id', 'pick', 'round', 'team', 'pfr_player_name', 'position', 'college']].copy()
                draft_year_clean = draft_year_clean.rename(columns={'gsis_id': 'player_id', 'pfr_player_name': 'player_display_name'})
                draft_year_clean['draft_year'] = year
                draft_data_list.append(draft_year_clean)
        except Exception as e:
            print(f"Could not get {year} draft data: {e}")
    
    # Get 2025 draft data (you'll need to update this with actual picks)
    draft_2025 = get_2025_draft_data()
    if not draft_2025.empty:
        draft_data_list.append(draft_2025)
    
    # Combine all draft data
    if draft_data_list:
        all_draft_data = pd.concat(draft_data_list, ignore_index=True)
        return all_draft_data
    else:
        return pd.DataFrame()

def get_2025_draft_data():
    """Get actual 2025 NFL Draft results - UPDATE THIS WITH REAL DATA"""
    print("Getting 2025 draft results...")
    
    # This needs to be updated with actual 2025 draft results
    # For now, using projected/example data
    draft_2025 = [
        # Round 1 QBs (3)
        {'player_display_name': 'Cam Ward', 'position': 'QB', 'team': 'TEN', 'round': 1, 'pick': 1, 'college': 'Miami'},

        # Round 1 RBs (1)
        {'player_display_name': 'Ashton Jeanty', 'position': 'RB', 'team': 'LV', 'round': 1, 'pick': 6, 'college': 'Boise State'},

        # Round 1 WRs (4)
        {'player_display_name': 'Travis Hunter', 'position': 'WR', 'team': 'JAX', 'round': 1, 'pick': 2, 'college': 'Colorado'},
        {'player_display_name': 'Tetairoa McMillan', 'position': 'WR', 'team': 'CAR', 'round': 1, 'pick': 8, 'college': 'Arizona'},
        {'player_display_name': 'Luther Burden III', 'position': 'WR', 'team': 'NO', 'round': 1, 'pick': 9, 'college': 'Missouri'},
        {'player_display_name': 'Emeka Egbuka', 'position': 'WR', 'team': 'GB', 'round': 1, 'pick': 18, 'college': 'Ohio State'},


        # Round 1 TEs (2)
        {'player_display_name': 'Colston Loveland', 'position': 'TE', 'team': 'SEA', 'round': 1, 'pick': 16, 'college': 'Michigan'},
        {'player_display_name': 'Tyler Warren', 'position': 'TE', 'team': 'IND', 'round': 1, 'pick': 14, 'college': 'Penn State'},

        # Round 2 QBs (2)
        {'player_display_name': 'Jaxson Dart', 'position': 'QB', 'team': 'PHI', 'round': 2, 'pick': 37, 'college': 'Ole Miss'},
        {'player_display_name': 'Drew Allar', 'position': 'QB', 'team': 'CHI', 'round': 2, 'pick': 44, 'college': 'Penn State'},

        # Round 2 RBs
        {'player_display_name': 'Jordan James', 'position': 'RB', 'team': 'SF', 'round': 2, 'pick': 49, 'college': 'Oregon'},
        {'player_display_name': 'Ollie Gordon II', 'position': 'RB', 'team': 'BUF', 'round': 2, 'pick': 54, 'college': 'Oklahoma State'},
        {'player_display_name': 'Donovan Edwards', 'position': 'RB', 'team': 'KC', 'round': 2, 'pick': 58, 'college': 'Michigan'},

        # Round 2 WRs
        {'player_display_name': 'Tre Harris', 'position': 'WR', 'team': 'DEN', 'round': 2, 'pick': 41, 'college': 'Ole Miss'},
        {'player_display_name': 'Xavier Worthy', 'position': 'WR', 'team': 'CIN', 'round': 2, 'pick': 48, 'college': 'Texas'},
        {'player_display_name': 'Troy Franklin', 'position': 'WR', 'team': 'LAC', 'round': 2, 'pick': 56, 'college': 'Oregon'},
        {'player_display_name': 'Antwane Wells Jr.', 'position': 'WR', 'team': 'BAL', 'round': 2, 'pick': 62, 'college': 'South Carolina'},
        {'player_display_name': 'Elic Ayomanor', 'position': 'WR', 'team': 'HOU', 'round': 2, 'pick': 52, 'college': 'Stanford'},

        # Round 2 TEs
        {'player_display_name': "Ja'Tavion Sanders", 'position': 'TE', 'team': 'DET', 'round': 2, 'pick': 50, 'college': 'Texas'},
        {'player_display_name': 'Brant Kuithe', 'position': 'TE', 'team': 'BAL', 'round': 2, 'pick': 60, 'college': 'Utah'},

        # Round 3 QBs
        {'player_display_name': 'Michael Penix Jr.', 'position': 'QB', 'team': 'ATL', 'round': 3, 'pick': 79, 'college': 'Washington'},

        # Round 3 RBs
        {'player_display_name': 'Braelon Allen', 'position': 'RB', 'team': 'TEN', 'round': 3, 'pick': 71, 'college': 'Wisconsin'},
        {'player_display_name': 'Will Shipley', 'position': 'RB', 'team': 'MIN', 'round': 3, 'pick': 75, 'college': 'Clemson'},
        {'player_display_name': 'Carson Steele', 'position': 'RB', 'team': 'LAR', 'round': 3, 'pick': 83, 'college': 'UCLA'},

        # Round 3 WRs
        {'player_display_name': 'Jacob Cowing', 'position': 'WR', 'team': 'WAS', 'round': 3, 'pick': 67, 'college': 'Arizona'},
        {'player_display_name': 'Johnny Wilson', 'position': 'WR', 'team': 'NYJ', 'round': 3, 'pick': 72, 'college': 'Florida State'},
        {'player_display_name': 'Malachi Corley', 'position': 'WR', 'team': 'CAR', 'round': 3, 'pick': 81, 'college': 'Western Kentucky'},

        # Round 3 TE
        {'player_display_name': 'Cade Stover', 'position': 'TE', 'team': 'JAX', 'round': 3, 'pick': 88, 'college': 'Ohio State'}
    ]
    
    rookies_df = pd.DataFrame(draft_2025)
    rookies_df['draft_year'] = 2025
    rookies_df['player_id'] = 'DRAFT_2025_' + rookies_df['player_display_name'].str.replace(' ', '_').str.replace('.', '')
    
    return rookies_df

def calculate_consistency_metrics(weekly_data):
    """Calculate consistency metrics from weekly data"""
    print("Calculating consistency metrics...")
    
    # Filter to regular season games only
    weekly_reg = weekly_data[weekly_data['season_type'] == 'REG'].copy()
    
    consistency_stats = []
    
    # Calculate for each player-season combination
    for (player_id, season) in weekly_reg[['player_id', 'season']].drop_duplicates().values:
        player_season_weeks = weekly_reg[(weekly_reg['player_id'] == player_id) & 
                                        (weekly_reg['season'] == season)]
        
        # Need at least 4 games to calculate meaningful consistency
        if len(player_season_weeks) < 4:
            continue
            
        points = player_season_weeks['fantasy_points_ppr'].dropna()
        
        if len(points) < 4:
            continue
            
        # Calculate consistency metrics
        stats = {
            'player_id': player_id,
            'season': season,
            'total_games': len(points),
            'mean_ppg': points.mean(),
            'std_ppg': points.std(),
            'cv': points.std() / points.mean() if points.mean() > 0 else np.inf,
            'median_ppg': points.median(),
            'min_ppg': points.min(),
            'max_ppg': points.max(),
            'games_over_10': (points >= 10).sum(),
            'games_over_15': (points >= 15).sum(),
            'games_under_5': (points < 5).sum(),
            'boom_games': (points > points.mean() + points.std()).sum() if points.std() > 0 else 0,
            'bust_games': (points < 5).sum()
        }
        
        consistency_stats.append(stats)
    
    return pd.DataFrame(consistency_stats)

def get_college_stats_proxy(draft_data):
    """Create proxy college stats for rookies based on draft position and position"""
    print("Creating college stats proxy for rookies...")
    
    # Position-based fantasy point projections based on historical rookie performance
    position_projections = {
        'QB': {
            'round_1': {'mean_ppg': 12.5, 'std_ppg': 8.2, 'games': 12, 'targets': 0, 'carries': 25, 'receptions': 0},
            'round_2': {'mean_ppg': 8.5, 'std_ppg': 6.8, 'games': 8, 'targets': 0, 'carries': 15, 'receptions': 0},
            'round_3+': {'mean_ppg': 4.2, 'std_ppg': 4.5, 'games': 4, 'targets': 0, 'carries': 8, 'receptions': 0}
        },
        'RB': {
            'round_1': {'mean_ppg': 11.8, 'std_ppg': 6.5, 'games': 14, 'targets': 35, 'carries': 180, 'receptions': 28},
            'round_2': {'mean_ppg': 8.2, 'std_ppg': 5.8, 'games': 12, 'targets': 25, 'carries': 120, 'receptions': 20},
            'round_3+': {'mean_ppg': 5.5, 'std_ppg': 4.2, 'games': 10, 'targets': 15, 'carries': 80, 'receptions': 12}
        },
        'WR': {
            'round_1': {'mean_ppg': 9.5, 'std_ppg': 5.8, 'games': 15, 'targets': 85, 'carries': 2, 'receptions': 52},
            'round_2': {'mean_ppg': 6.8, 'std_ppg': 4.5, 'games': 13, 'targets': 65, 'carries': 1, 'receptions': 38},
            'round_3+': {'mean_ppg': 4.2, 'std_ppg': 3.8, 'games': 11, 'targets': 45, 'carries': 1, 'receptions': 26}
        },
        'TE': {
            'round_1': {'mean_ppg': 7.2, 'std_ppg': 4.8, 'games': 14, 'targets': 65, 'carries': 1, 'receptions': 42},
            'round_2': {'mean_ppg': 4.8, 'std_ppg': 3.5, 'games': 12, 'targets': 45, 'carries': 0, 'receptions': 28},
            'round_3+': {'mean_ppg': 2.8, 'std_ppg': 2.5, 'games': 10, 'targets': 25, 'carries': 0, 'receptions': 16}
        }
    }
    
    # Apply projections to rookies
    for idx, row in draft_data.iterrows():
        pos = row['position']
        round_num = row['round']
        
        if pos not in position_projections:
            continue
            
        # Determine round category
        if round_num == 1:
            round_cat = 'round_1'
        elif round_num == 2:
            round_cat = 'round_2'
        else:
            round_cat = 'round_3+'
            
        if round_cat in position_projections[pos]:
            proj = position_projections[pos][round_cat]
            
            # Apply projections with some randomness
            for key, value in proj.items():
                if key in ['mean_ppg', 'std_ppg']:
                    # Add some variation based on draft position within round
                    pick_modifier = 1 - (row['pick'] % 32) * 0.01  # Slight adjustment based on pick
                    draft_data.loc[idx, key] = value * pick_modifier
                else:
                    draft_data.loc[idx, key] = value
    
    return draft_data

def create_comprehensive_dataframe():
    """Create the complete player data dataframe with all years"""
    print("Creating comprehensive dataframe...")
    
    # Get all the data
    seasonal_stats, weekly_data, player_info, current_teams = get_player_data()
    consistency_df = calculate_consistency_metrics(weekly_data)
    
    # Get draft data for all years
    all_draft_data = get_all_draft_data()
    
    # Get team context data
    team_context = get_team_context_data()
    
    # Create rows for ALL years, not just 2024
    all_seasons_data = []
    
    for year in [2021, 2022, 2023, 2024]:
        print(f"Processing {year} season data...")
        
        # Get season stats for this year
        season_stats = seasonal_stats[seasonal_stats['season'] == year].copy()
        
        if season_stats.empty:
            continue
            
        # Merge with player info
        season_df = season_stats.merge(player_info, on='player_id', how='left')
        
        # Merge consistency metrics for this season
        season_consistency = consistency_df[consistency_df['season'] == year]
        season_df = season_df.merge(season_consistency, on='player_id', how='left')
        
        # Add draft information
        if not all_draft_data.empty:
            season_df = season_df.merge(all_draft_data, on='player_id', how='left', suffixes=('', '_draft'))
        
        # Calculate years of experience
        season_df['years_experience'] = year - season_df['draft_year'].fillna(year - 3)  # Assume 3 years if no draft data
        season_df['years_experience'] = season_df['years_experience'].clip(lower=0)
        
        # Determine player type for this season
        season_df['is_rookie'] = (season_df['draft_year'] == year)
        season_df['player_type'] = 'veteran'
        season_df.loc[season_df['draft_year'] == year, 'player_type'] = 'rookie'
        season_df.loc[season_df['draft_year'] == year - 1, 'player_type'] = '2nd_year'
        
        # Calculate per-game stats
        season_df['ppg'] = season_df['fantasy_points_ppr'] / season_df['games'].clip(lower=1)
        season_df['targets_per_game'] = season_df['targets'] / season_df['games'].clip(lower=1)
        season_df['carries_per_game'] = season_df['carries'] / season_df['games'].clip(lower=1)
        
        # Add team context
        team_col = 'recent_team'
        if not team_context.empty and team_col in season_df.columns:
            merge_col = 'team_abbr' if 'team_abbr' in team_context.columns else 'team'
            season_df = season_df.merge(team_context, left_on=team_col, right_on=merge_col, 
                                      how='left', suffixes=('', '_team_context'))
        
        all_seasons_data.append(season_df)
    
    # Combine all seasons
    if all_seasons_data:
        df = pd.concat(all_seasons_data, ignore_index=True, sort=False)
    else:
        df = pd.DataFrame()
    
    # Add 2025 rookies with projected stats
    rookies_2025 = all_draft_data[all_draft_data['draft_year'] == 2025].copy()
    if not rookies_2025.empty:
        # Apply college stats proxy
        rookies_2025 = get_college_stats_proxy(rookies_2025)
        
        # Set 2025 season values
        rookies_2025['season'] = 2025
        rookies_2025['years_experience'] = 0
        rookies_2025['is_rookie'] = True
        rookies_2025['player_type'] = 'rookie'
        rookies_2025['player_name'] = rookies_2025['player_display_name']
        
        # Fill missing columns with appropriate defaults
        for col in df.columns:
            if col not in rookies_2025.columns:
                if col in ['fantasy_points_ppr', 'targets', 'carries', 'receptions', 'receiving_yards', 'rushing_yards']:
                    rookies_2025[col] = 0  # Will be filled by projections
                else:
                    rookies_2025[col] = np.nan
        
        # Calculate projected fantasy points based on the proxy stats
        for idx, row in rookies_2025.iterrows():
            if pd.notna(row.get('mean_ppg')) and pd.notna(row.get('games')):
                rookies_2025.loc[idx, 'fantasy_points_ppr'] = row['mean_ppg'] * row['games']
                rookies_2025.loc[idx, 'ppg'] = row['mean_ppg']
                
                # Set other stats
                if pd.notna(row.get('targets')):
                    rookies_2025.loc[idx, 'targets'] = row['targets']
                    rookies_2025.loc[idx, 'targets_per_game'] = row['targets'] / row['games']
                if pd.notna(row.get('carries')):
                    rookies_2025.loc[idx, 'carries'] = row['carries']
                    rookies_2025.loc[idx, 'carries_per_game'] = row['carries'] / row['games']
                if pd.notna(row.get('receptions')):
                    rookies_2025.loc[idx, 'receptions'] = row['receptions']
        
        # Add rookies to main dataframe
        df = pd.concat([df, rookies_2025], ignore_index=True, sort=False)
    
    return df

def get_team_context_data():
    """Get team-level context data for fantasy analysis"""
    print("Getting team context data...")
    
    try:
        # Get team stats and info
        team_desc = nfl.import_team_desc()
        
        # Get team stats for offensive context from most recent year
        team_stats = nfl.import_weekly_data([2024]).groupby('recent_team').agg({
            'passing_yards': 'mean',
            'rushing_yards': 'mean', 
            'passing_tds': 'mean',
            'rushing_tds': 'mean',
            'targets': 'sum',
            'carries': 'sum'
        }).reset_index()
        team_stats.columns = ['team'] + [f'team_{col}' for col in team_stats.columns[1:]]
        
        # Merge team info with stats
        if not team_desc.empty:
            team_context = team_desc.merge(team_stats, left_on='team_abbr', right_on='team', how='left')
        else:
            team_context = team_stats
            
        return team_context
        
    except Exception as e:
        print(f"Could not get team context: {e}")
        return pd.DataFrame()

def filter_fantasy_relevant(df):
    """Filter to fantasy relevant players"""
    print("Filtering to fantasy relevant players...")
    
    # Fantasy relevant positions
    fantasy_positions = ['QB', 'RB', 'WR', 'TE']
    
    # More inclusive filter criteria for ML training
    relevant = df[
        (df['position'].isin(fantasy_positions)) &
        (
            # Veterans with any production
            ((df['player_type'] == 'veteran') & (df['fantasy_points_ppr'] >= 10)) |
            # OR any rookies/2nd year players
            (df['player_type'].isin(['rookie', '2nd_year'])) |
            # OR players with significant opportunity (targets/carries)
            (df['targets'] >= 20) |
            (df['carries'] >= 30) |
            # OR players who played in multiple games
            (df['games'] >= 4)
        )
    ].copy()
    
    return relevant

def add_advanced_features(df):
    """Add advanced features for ML modeling"""
    print("Adding advanced features for ML modeling...")
    
    # Market share features
    df['target_share'] = df.groupby(['recent_team', 'season'])['targets'].transform(
        lambda x: x / x.sum() if x.sum() > 0 else 0
    )
    
    df['carry_share'] = df.groupby(['recent_team', 'season'])['carries'].transform(
        lambda x: x / x.sum() if x.sum() > 0 else 0
    )
    
    # Efficiency metrics
    df['yards_per_target'] = df['receiving_yards'] / df['targets'].clip(lower=1)
    df['yards_per_carry'] = df['rushing_yards'] / df['carries'].clip(lower=1)
    df['td_rate'] = (df['receiving_tds'] + df['rushing_tds']) / (df['targets'] + df['carries']).clip(lower=1)
    
    # Age proxy (years since draft)
    df['draft_age_proxy'] = df['season'] - df['draft_year'].fillna(df['season'] - 4)
    
    # Positional rankings within team
    df['team_pos_rank'] = df.groupby(['recent_team', 'season', 'position'])['fantasy_points_ppr'].rank(
        method='dense', ascending=False
    )
    
    # Fill NaNs with reasonable defaults
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col not in ['player_id', 'season', 'draft_year']:
            df[col] = df[col].fillna(0)
    
    return df

def main():
    """Main function to generate and save the data"""
    print("Starting Enhanced Fantasy Football Data Collection...")
    print("="*60)
    
    # Create the comprehensive dataframe
    df = create_comprehensive_dataframe()
    
    # Filter to relevant players
    df_filtered = filter_fantasy_relevant(df)
    
    # Add advanced features for ML
    df_final = add_advanced_features(df_filtered)
    
    print(f"\nComprehensive data created!")
    print(f"Total player-seasons: {len(df_final)}")
    print(f"Unique players: {df_final['player_id'].nunique()}")
    print(f"By season: {df_final['season'].value_counts().sort_index().to_dict()}")
    print(f"By player type: {df_final['player_type'].value_counts().to_dict()}")
    print(f"By position: {df_final['position'].value_counts().to_dict()}")
    
    df_final.drop(columns=[
        'team_color', 'team_color2', 'team_color3', 'team_color4',
        'team_logo_wikipedia', 'team_logo_espn', 'team_wordmark',
        'team_conference_logo', 'team_league_logo', 'team_logo_squared',
        'team_team_context', 'player_display_name'
    ], inplace=True)
    cols = df_final.columns.tolist()
    cols.remove('player_name')
    cols.remove('fantasy_points_ppr')
    df_final = df_final[['player_name'] + cols + ['fantasy_points_ppr']]
    return df_final

if __name__ == "__main__":
    fantasy_df = main()
    # Save to CSV
    fantasy_df.to_csv('fantasy_football_2025_complete_data.csv', index=False)
    print(f"\n✅ Saved complete data to: fantasy_football_2025_complete_data.csv")
    
    # Show sample rookie data
    print("\nSample rookie data (2025):")
    rookie_sample = fantasy_df[fantasy_df['season'] == 2025].head()
    if not rookie_sample.empty:
        print(rookie_sample[['player_name', 'position', 'team', 'draft_year', 'fantasy_points_ppr', 'ppg', 'targets', 'carries']].to_string())
    
    print(f"\nColumns in final dataset: {len(fantasy_df.columns)}")
    print("Key columns:", [col for col in fantasy_df.columns if any(x in col.lower() for x in ['fantasy', 'ppg', 'target', 'carry', 'experience', 'draft'])][:10])