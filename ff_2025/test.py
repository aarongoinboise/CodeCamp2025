import pandas as pd
import numpy as np
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')
import traceback

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
        depth_charts = nfl.import_depth_charts([2025])

        # Keep only skill positions
        skill_positions = ['QB', 'RB', 'WR', 'TE']
        skill_players = depth_charts[depth_charts['pos_abb'].isin(skill_positions)].copy()
        
        # Team-relative ranking using existing pos_rank
        skill_players['pos_rank'] = skill_players.groupby(['team', 'pos_abb'])['pos_rank'].rank()

        # Prepare the final output
        current_teams = skill_players.groupby('gsis_id').agg({
            'team': 'first',
            'player_name': 'first',
            'espn_id': 'first',
            'pos_abb': 'first',
            'pos_rank': 'first',
            'pos_slot': 'first'
        }).reset_index()

        current_teams = current_teams.rename(columns={'gsis_id': 'player_id', 'team': 'current_team_2025'})

        # Select and order columns as needed
        final_columns = [
            'player_id', 'current_team_2025', 'player_name', 'espn_id', 
            'pos_abb', 'pos_rank', 'pos_slot'
        ]
        current_teams = current_teams[final_columns]
        current_teams.to_csv('test.csv', index=False)
    except Exception as e:
        print("Could not get current team data:", e)
        traceback.print_exc()
        current_teams = pd.DataFrame()
        exit(1)
    
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

def get_enhanced_rookie_projections(draft_data, historical_rookie_data=None):
    """
    Create comprehensive rookie projections based on draft position, position, and historical data
    """
    print("Creating enhanced rookie projections...")
    
    # Enhanced position-based projections with full stat lines
    position_projections = {
        'QB': {
            'round_1': {
                'games': 12, 'fantasy_points_ppr': 150, 'ppg': 12.5,
                'passing_yards': 2800, 'passing_tds': 18, 'interceptions': 12,
                'passing_attempts': 450, 'completions': 285, 'sacks': 32,
                'rushing_yards': 180, 'rushing_tds': 3, 'carries': 45,
                'targets': 0, 'receptions': 0, 'receiving_yards': 0, 'receiving_tds': 0,
                'fumbles_lost': 3, 'passing_2pt_conversions': 0
            },
            'round_2': {
                'games': 8, 'fantasy_points_ppr': 68, 'ppg': 8.5,
                'passing_yards': 1200, 'passing_tds': 8, 'interceptions': 6,
                'passing_attempts': 200, 'completions': 120, 'sacks': 18,
                'rushing_yards': 85, 'rushing_tds': 1, 'carries': 22,
                'targets': 0, 'receptions': 0, 'receiving_yards': 0, 'receiving_tds': 0,
                'fumbles_lost': 2, 'passing_2pt_conversions': 0
            },
            'round_3+': {
                'games': 4, 'fantasy_points_ppr': 17, 'ppg': 4.2,
                'passing_yards': 500, 'passing_tds': 3, 'interceptions': 3,
                'passing_attempts': 85, 'completions': 48, 'sacks': 8,
                'rushing_yards': 35, 'rushing_tds': 1, 'carries': 12,
                'targets': 0, 'receptions': 0, 'receiving_yards': 0, 'receiving_tds': 0,
                'fumbles_lost': 1, 'passing_2pt_conversions': 0
            }
        },
        'RB': {
            'round_1': {
                'games': 14, 'fantasy_points_ppr': 165, 'ppg': 11.8,
                'rushing_yards': 850, 'rushing_tds': 6, 'carries': 200,
                'targets': 45, 'receptions': 32, 'receiving_yards': 280, 'receiving_tds': 2,
                'fumbles_lost': 2, 'rushing_2pt_conversions': 0, 'receiving_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            },
            'round_2': {
                'games': 12, 'fantasy_points_ppr': 98, 'ppg': 8.2,
                'rushing_yards': 520, 'rushing_tds': 4, 'carries': 135,
                'targets': 28, 'receptions': 21, 'receiving_yards': 175, 'receiving_tds': 1,
                'fumbles_lost': 1, 'rushing_2pt_conversions': 0, 'receiving_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            },
            'round_3+': {
                'games': 10, 'fantasy_points_ppr': 55, 'ppg': 5.5,
                'rushing_yards': 320, 'rushing_tds': 2, 'carries': 85,
                'targets': 18, 'receptions': 13, 'receiving_yards': 110, 'receiving_tds': 1,
                'fumbles_lost': 1, 'rushing_2pt_conversions': 0, 'receiving_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            }
        },
        'WR': {
            'round_1': {
                'games': 15, 'fantasy_points_ppr': 143, 'ppg': 9.5,
                'targets': 90, 'receptions': 55, 'receiving_yards': 750, 'receiving_tds': 5,
                'carries': 3, 'rushing_yards': 25, 'rushing_tds': 0,
                'fumbles_lost': 1, 'receiving_2pt_conversions': 0, 'rushing_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            },
            'round_2': {
                'games': 13, 'fantasy_points_ppr': 88, 'ppg': 6.8,
                'targets': 70, 'receptions': 40, 'receiving_yards': 520, 'receiving_tds': 3,
                'carries': 2, 'rushing_yards': 15, 'rushing_tds': 0,
                'fumbles_lost': 0, 'receiving_2pt_conversions': 0, 'rushing_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            },
            'round_3+': {
                'games': 11, 'fantasy_points_ppr': 46, 'ppg': 4.2,
                'targets': 50, 'receptions': 28, 'receiving_yards': 350, 'receiving_tds': 2,
                'carries': 1, 'rushing_yards': 8, 'rushing_tds': 0,
                'fumbles_lost': 0, 'receiving_2pt_conversions': 0, 'rushing_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            }
        },
        'TE': {
            'round_1': {
                'games': 14, 'fantasy_points_ppr': 101, 'ppg': 7.2,
                'targets': 70, 'receptions': 45, 'receiving_yards': 520, 'receiving_tds': 4,
                'carries': 1, 'rushing_yards': 5, 'rushing_tds': 0,
                'fumbles_lost': 0, 'receiving_2pt_conversions': 0, 'rushing_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            },
            'round_2': {
                'games': 12, 'fantasy_points_ppr': 58, 'ppg': 4.8,
                'targets': 50, 'receptions': 30, 'receiving_yards': 350, 'receiving_tds': 2,
                'carries': 0, 'rushing_yards': 0, 'rushing_tds': 0,
                'fumbles_lost': 0, 'receiving_2pt_conversions': 0, 'rushing_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            },
            'round_3+': {
                'games': 10, 'fantasy_points_ppr': 28, 'ppg': 2.8,
                'targets': 30, 'receptions': 18, 'receiving_yards': 200, 'receiving_tds': 1,
                'carries': 0, 'rushing_yards': 0, 'rushing_tds': 0,
                'fumbles_lost': 0, 'receiving_2pt_conversions': 0, 'rushing_2pt_conversions': 0,
                'passing_yards': 0, 'passing_tds': 0, 'interceptions': 0,
                'passing_attempts': 0, 'completions': 0, 'sacks': 0
            }
        }
    }
    
    # Apply projections to each rookie
    for idx, row in draft_data.iterrows():
        pos = row['position']
        round_num = row['round']
        pick = row['pick']
        
        if pos not in position_projections:
            continue
            
        # Determine round category
        if round_num == 1:
            round_cat = 'round_1'
        elif round_num == 2:
            round_cat = 'round_2'
        else:
            round_cat = 'round_3+'
            
        if round_cat not in position_projections[pos]:
            continue
            
        base_projections = position_projections[pos][round_cat].copy()
        
        # Apply draft position modifiers
        # Earlier picks within each round get slight boost
        if round_num <= 2:
            pick_in_round = pick - ((round_num - 1) * 32)
            pick_modifier = 1 + (32 - pick_in_round) * 0.003  # Small boost for earlier picks
        else:
            pick_modifier = 0.95 + np.random.uniform(-0.05, 0.1)  # More variation for later picks
        
        # Apply team context modifiers (simplified)
        team_modifiers = get_team_context_modifiers(row.get('team', ''), pos)
        
        # Apply all projections
        for stat, base_value in base_projections.items():
            if stat in ['games']:
                # Games don't get modified much
                final_value = max(1, int(base_value * pick_modifier))
            elif stat in ['fantasy_points_ppr', 'ppg']:
                # Fantasy points get full modifiers
                final_value = base_value * pick_modifier * team_modifiers.get('fantasy_modifier', 1.0)
            elif 'yards' in stat or 'tds' in stat:
                # Volume stats get team context
                final_value = base_value * pick_modifier * team_modifiers.get('volume_modifier', 1.0)
            elif stat in ['targets', 'carries', 'attempts']:
                # Opportunity stats
                final_value = int(base_value * pick_modifier * team_modifiers.get('opportunity_modifier', 1.0))
            else:
                # Other stats get basic modifier
                final_value = base_value * pick_modifier
            
            # Set the value
            if stat in ['games', 'targets', 'carries', 'attempts', 'completions', 'receptions', 'sacks']:
                draft_data.loc[idx, stat] = max(0, int(final_value))
            else:
                draft_data.loc[idx, stat] = max(0, final_value)
        
        # Calculate derived stats
        games = draft_data.loc[idx, 'games']
        if games > 0:
            # Per-game stats
            draft_data.loc[idx, 'targets_per_game'] = draft_data.loc[idx, 'targets'] / games
            draft_data.loc[idx, 'carries_per_game'] = draft_data.loc[idx, 'carries'] / games
            
            # Completion percentage for QBs
            if pos == 'QB' and draft_data.loc[idx, 'passing_attempts'] > 0:
                completion_pct = draft_data.loc[idx, 'completions'] / draft_data.loc[idx, 'passing_attempts']
                draft_data.loc[idx, 'completion_percentage'] = completion_pct
        
    return draft_data

def get_team_context_modifiers(team, position):
    """
    Get team-specific modifiers based on offensive system and needs
    This is a simplified version - you could make this much more sophisticated
    """
    # High-volume passing offenses
    pass_heavy_teams = ['BUF', 'KC', 'MIA', 'CIN', 'LAC', 'DET', 'GB', 'DAL', 'PHI']
    
    # Run-heavy offenses  
    run_heavy_teams = ['BAL', 'SF', 'NYJ', 'PIT', 'TEN', 'CLE']
    
    # Rookie-friendly situations (good OL, good coaching, etc.)
    rookie_friendly = ['KC', 'BUF', 'SF', 'DET', 'GB', 'PHI', 'BAL', 'LAC']
    
    modifiers = {
        'fantasy_modifier': 1.0,
        'volume_modifier': 1.0, 
        'opportunity_modifier': 1.0
    }
    
    # Position-specific team adjustments
    if position in ['QB', 'WR']:
        if team in pass_heavy_teams:
            modifiers['volume_modifier'] = 1.15
            modifiers['opportunity_modifier'] = 1.1
        elif team in run_heavy_teams:
            modifiers['volume_modifier'] = 0.9
            modifiers['opportunity_modifier'] = 0.95
            
    elif position == 'RB':
        if team in run_heavy_teams:
            modifiers['volume_modifier'] = 1.2
            modifiers['opportunity_modifier'] = 1.15
        elif team in pass_heavy_teams:
            modifiers['volume_modifier'] = 0.95
            modifiers['opportunity_modifier'] = 1.05  # More receiving work
            
    elif position == 'TE':
        if team in pass_heavy_teams:
            modifiers['volume_modifier'] = 1.1
            modifiers['opportunity_modifier'] = 1.1
    
    # Rookie-friendly boost
    if team in rookie_friendly:
        modifiers['fantasy_modifier'] = modifiers.get('fantasy_modifier', 1.0) * 1.05
    
    return modifiers

def add_rookie_consistency_estimates(rookies_df):
    """
    Add consistency metrics for rookies based on position and draft capital
    """
    for idx, row in rookies_df.iterrows():
        pos = row['position']
        round_num = row['round']
        ppg = row.get('ppg', 0)
        
        # Consistency varies by position and draft capital
        if pos == 'QB':
            if round_num == 1:
                std_ppg = ppg * 0.65  # QBs are volatile
                cv = 0.65
            else:
                std_ppg = ppg * 0.8
                cv = 0.8
        elif pos == 'RB':
            if round_num == 1:
                std_ppg = ppg * 0.55  # Top RBs more consistent
                cv = 0.55
            else:
                std_ppg = ppg * 0.7
                cv = 0.7
        elif pos == 'WR':
            std_ppg = ppg * 0.6  # WRs moderately consistent
            cv = 0.6
        elif pos == 'TE':
            std_ppg = ppg * 0.67  # TEs somewhat volatile
            cv = 0.67
        else:
            std_ppg = ppg * 0.7
            cv = 0.7
        
        # Set consistency metrics
        rookies_df.loc[idx, 'std_ppg'] = std_ppg
        rookies_df.loc[idx, 'cv'] = cv
        rookies_df.loc[idx, 'median_ppg'] = ppg * 0.9  # Slightly below mean
        
        # Estimate boom/bust games
        games = row.get('games', 0)
        if games > 0:
            rookies_df.loc[idx, 'boom_games'] = max(0, int(games * 0.15))  # 15% boom rate
            rookies_df.loc[idx, 'bust_games'] = max(0, int(games * 0.25))  # 25% bust rate
            rookies_df.loc[idx, 'games_over_10'] = max(0, int(games * (ppg/10 * 0.6)))
            rookies_df.loc[idx, 'games_over_15'] = max(0, int(games * (ppg/15 * 0.4)))
            rookies_df.loc[idx, 'games_under_5'] = max(0, int(games * 0.3))
        
    return rookies_df

def get_college_stats_proxy(draft_data):
    """Enhanced version that creates comprehensive rookie projections"""
    print("Creating enhanced college stats proxy for rookies...")
    
    # Apply the enhanced projections
    draft_data = get_enhanced_rookie_projections(draft_data)
    
    # Add consistency estimates
    draft_data = add_rookie_consistency_estimates(draft_data)
    
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
    
    print(df.columns)
    if not current_teams.empty:
        # Merge current team info with main dataframe
        df = df.merge(
            current_teams[['player_id', 'current_team_2025', 'pos_abb', 'pos_rank', 'depth_team']],
            on='player_id',
            how='left',
            suffixes=('', '_current')
        )
        
        # For 2025 data, update recent_team with current_team_2025 if available
        df.loc[df['season'] == 2025, 'recent_team'] = df.loc[df['season'] == 2025, 'recent_team'].fillna(
            df.loc[df['season'] == 2025, 'current_team_2025']
        )

        # Fill missing stats with player's historical averages (across all teams)
        stat_columns = ['fantasy_points_ppr', 'targets', 'carries', 'ppg', 
                       'targets_per_game', 'carries_per_game']  # Add more as needed
        
        # Calculate each player's historical averages
        historical_avgs = df[df['season'] < 2025].groupby('player_id')[stat_columns].mean().reset_index()
        
        # Merge historical averages for 2025 data
        df_2025 = df[df['season'] == 2025].copy()
        if not df_2025.empty:
            df_2025 = df_2025.merge(historical_avgs, on='player_id', how='left', suffixes=('', '_hist'))
            
            # Fill missing 2025 stats with historical averages
            for stat in stat_columns:
                df_2025[stat] = df_2025[stat].fillna(df_2025[f'{stat}_hist'])
                df_2025.drop(columns=[f'{stat}_hist'], inplace=True)
            
            # Update the dataframe
            df = pd.concat([df[df['season'] != 2025], df_2025], ignore_index=True)
    
    # Add 2025 rookies with projected stats
    rookies_2025 = all_draft_data[all_draft_data['draft_year'] == 2025].copy()
    if not rookies_2025.empty:
        # Apply enhanced college stats proxy - this sets ALL the realistic projections
        rookies_2025 = get_college_stats_proxy(rookies_2025)
        
        # Set 2025 season values
        rookies_2025['season'] = 2025
        rookies_2025['years_experience'] = 0
        rookies_2025['is_rookie'] = True
        rookies_2025['player_type'] = 'rookie'
        rookies_2025['player_name'] = rookies_2025['player_display_name']
        rookies_2025['recent_team'] = rookies_2025['team']
        
        # Fill missing columns with appropriate defaults (but DON'T override existing projections!)
        for col in df.columns:
            if col not in rookies_2025.columns:
                rookies_2025[col] = np.nan
        
        # The enhanced projections have already set all the stats we need!
        print(f"Enhanced projections complete. Sample fantasy points: {rookies_2025['fantasy_points_ppr'].head().tolist()}")
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
    
    # Clean up columns
    columns_to_drop = []
    for col in ['team_color', 'team_color2', 'team_color3', 'team_color4',
                'team_logo_wikipedia', 'team_logo_espn', 'team_wordmark',
                'team_conference_logo', 'team_league_logo', 'team_logo_squared',
                'team_team_context', 'player_display_name']:
        if col in df_final.columns:
            columns_to_drop.append(col)
    
    if columns_to_drop:
        df_final = df_final.drop(columns=columns_to_drop)
    
    # Reorder columns
    cols = df_final.columns.tolist()
    if 'player_name' in cols:
        cols.remove('player_name')
    if 'fantasy_points_ppr' in cols:
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
        key_cols = ['player_name', 'position', 'team', 'draft_year', 'fantasy_points_ppr', 'ppg', 'targets', 'carries', 'passing_yards', 'rushing_yards', 'receiving_yards']
        available_cols = [col for col in key_cols if col in rookie_sample.columns]
        print(rookie_sample[available_cols].to_string())
    
    print(f"\nColumns in final dataset: {len(fantasy_df.columns)}")
    print("Key columns:", [col for col in fantasy_df.columns if any(x in col.lower() for x in ['fantasy', 'ppg', 'target', 'carry', 'experience', 'draft'])][:10])