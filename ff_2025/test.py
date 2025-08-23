import pandas as pd
import numpy as np
import nfl_data_py as nfl
import warnings
warnings.filterwarnings('ignore')
import traceback

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def calculate_injury_risk_score(df):
    """
    Calculate injury risk based on games played patterns and other indicators
    Lower score = lower injury risk (better)
    """
    print("Calculating injury risk scores...")
    
    injury_scores = []
    
    for player_id in df['player_id'].unique():
        player_data = df[df['player_id'] == player_id].copy()
        
        if len(player_data) == 0:
            continue
            
        # Skip rookies for injury analysis (no history)
        non_rookie_data = player_data[player_data['player_type'] != 'rookie']
        
        if len(non_rookie_data) == 0:
            # Rookie - assign neutral injury risk
            injury_score = 0.5
        else:
            # Calculate injury indicators
            games_played = non_rookie_data['games'].fillna(0)
            seasons_played = len(non_rookie_data)
            
            # Games per season average (17 games = perfect availability)
            avg_games_per_season = games_played.mean() if len(games_played) > 0 else 8
            availability_rate = avg_games_per_season / 17.0
            
            # Consistency of availability (low std = more consistent)
            games_std = games_played.std() if len(games_played) > 1 else 0
            consistency_penalty = (games_std / 17.0) * 0.3
            
            # Recent injury history (weight recent seasons more)
            if len(games_played) >= 2:
                recent_games = games_played.iloc[-2:].mean()  # Last 2 seasons
                recent_availability = recent_games / 17.0
            else:
                recent_availability = availability_rate
            
            # Fumbles lost can indicate hits/injury risk
            fumbles_avg = non_rookie_data['fumbles_lost'].fillna(0).mean()
            fumble_penalty = min(fumbles_avg * 0.1, 0.2)  # Cap at 0.2
            
            # Calculate final injury risk score (0 = no risk, 1 = high risk)
            injury_score = 1.0 - availability_rate
            injury_score += consistency_penalty
            injury_score = (injury_score * 0.7) + (1.0 - recent_availability) * 0.3  # Weight recent more
            injury_score += fumble_penalty
            
            # Cap between 0 and 1
            injury_score = np.clip(injury_score, 0, 1)
        
        injury_scores.append({
            'player_id': player_id,
            'injury_risk_score': injury_score,
            'avg_games_per_season': avg_games_per_season if 'avg_games_per_season' in locals() else 17,
            'seasons_analyzed': len(non_rookie_data)
        })
    
    return pd.DataFrame(injury_scores)

def calculate_consistency_score(df):
    """
    Calculate consistency score - higher is better
    Focuses on week-to-week consistency rather than boom/bust
    """
    print("Calculating consistency scores...")
    
    consistency_scores = []
    
    for player_id in df['player_id'].unique():
        player_data = df[df['player_id'] == player_id].copy()
        
        if len(player_data) == 0:
            continue
            
        # For rookies, use projected consistency metrics
        if player_data['player_type'].iloc[0] == 'rookie':
            # Use rookie projections if available
            if 'cv' in player_data.columns and not pd.isna(player_data['cv'].iloc[0]):
                cv = player_data['cv'].iloc[0]
                consistency_score = 1.0 / (1.0 + cv)  # Lower CV = higher consistency
            else:
                # Default rookie consistency by position
                pos = player_data['position'].iloc[0]
                pos_consistency = {'QB': 0.6, 'RB': 0.65, 'WR': 0.55, 'TE': 0.5}
                consistency_score = pos_consistency.get(pos, 0.5)
        else:
            # Use historical data for veterans
            non_rookie_data = player_data[player_data['player_type'] != 'rookie']
            
            if len(non_rookie_data) == 0:
                consistency_score = 0.5
            else:
                # Multiple consistency indicators
                cv_scores = non_rookie_data['cv'].fillna(1.0)  # Lower CV = more consistent
                std_scores = non_rookie_data['std_ppg'].fillna(10.0)
                ppg_scores = non_rookie_data['ppg'].fillna(0)
                
                # Coefficient of variation (lower = more consistent)
                avg_cv = cv_scores.mean()
                cv_consistency = 1.0 / (1.0 + avg_cv)
                
                # Boom/bust ratio
                boom_games = non_rookie_data['boom_games'].fillna(0).mean()
                bust_games = non_rookie_data['bust_games'].fillna(0).mean()
                total_games = non_rookie_data['games'].fillna(1).mean()
                
                if total_games > 0:
                    boom_rate = boom_games / total_games
                    bust_rate = bust_games / total_games
                    # Prefer low bust rate over high boom rate
                    boom_bust_score = 1.0 - (bust_rate * 0.7) + (boom_rate * 0.2)
                else:
                    boom_bust_score = 0.5
                
                # Games with decent production
                if 'games_over_10' in non_rookie_data.columns:
                    solid_games = non_rookie_data['games_over_10'].fillna(0).mean()
                    solid_rate = solid_games / total_games if total_games > 0 else 0
                else:
                    solid_rate = 0.5
                
                # Combine consistency metrics
                consistency_score = (cv_consistency * 0.4 + 
                                   boom_bust_score * 0.4 + 
                                   solid_rate * 0.2)
                
                # Cap between 0 and 1
                consistency_score = np.clip(consistency_score, 0, 1)
        
        consistency_scores.append({
            'player_id': player_id,
            'consistency_score': consistency_score
        })
    
    return pd.DataFrame(consistency_scores)

def get_positional_scarcity_adjustments():
    """
    Define positional scarcity multipliers based on typical fantasy league needs
    """
    return {
        'QB': 0.85,  # Less valuable, most teams only start 1
        'RB': 1.4,   # Most scarce, teams start 2+ and injuries common
        'WR': 1.2,   # High volume, teams start 2-3+
        'TE': 0.9    # Only elite TEs are worth early picks, big dropoff
    }

def calculate_team_context_score(df, current_teams):
    """
    Score players based on their team context for fantasy production
    """
    print("Calculating team context scores...")
    
    # Define team tiers based on offensive quality and opportunity
    # This should be updated based on 2025 expectations
    team_tiers = {
        # Tier 1: Elite offenses, great for fantasy
        'KC': 1.0, 'BUF': 1.0, 'SF': 0.95, 'DAL': 0.95, 'MIA': 0.95,
        
        # Tier 2: Good offenses
        'PHI': 0.9, 'CIN': 0.9, 'DET': 0.9, 'LAC': 0.85, 'GB': 0.85,
        'BAL': 0.85, 'HOU': 0.8, 'JAX': 0.8,
        
        # Tier 3: Average offenses  
        'ATL': 0.75, 'TB': 0.75, 'MIN': 0.75, 'SEA': 0.75, 'LAR': 0.75,
        'IND': 0.7, 'PIT': 0.7, 'DEN': 0.7,
        
        # Tier 4: Below average
        'LV': 0.6, 'NYJ': 0.65, 'TEN': 0.65, 'ARI': 0.6, 'CHI': 0.6,
        'WAS': 0.65, 'CLE': 0.6, 'NO': 0.6,
        
        # Tier 5: Concerning offenses
        'CAR': 0.5, 'NYG': 0.5, 'NE': 0.55
    }
    
    # Position-specific team adjustments
    position_team_bonuses = {
        'TE': {
            'KC': 0.2,   # Kelce history
            'SF': 0.15,  # Kittle usage
            'BAL': 0.1,  # Andrews usage
            'LV': -0.1,  # Weaker offense for TEs
            'ARI': -0.05, 'CAR': -0.1, 'NYG': -0.1
        }
    }
    
    team_scores = []
    
    for player_id in df['player_id'].unique():
        player_data = df[df['player_id'] == player_id].copy()
        
        # Get current team from current_teams df or recent_team
        current_team_info = current_teams[current_teams['player_id'] == player_id]
        
        if not current_team_info.empty:
            team = current_team_info['current_team_2025'].iloc[0]
            depth_rank = current_team_info['pos_rank'].iloc[0]
            # Better depth chart penalty
            if depth_rank <= 1:
                depth_score = 1.0
            elif depth_rank <= 2:
                depth_score = 0.8
            elif depth_rank <= 3:
                depth_score = 0.6
            else:
                depth_score = 0.4
        else:
            team = player_data['recent_team'].iloc[0] if 'recent_team' in player_data.columns else 'UNK'
            depth_score = 0.7  # Neutral if no depth chart info
        
        # Get team tier score
        base_team_score = team_tiers.get(team, 0.6)  # Default to below average if unknown
        
        # Apply position-specific bonuses/penalties
        position = player_data['position'].iloc[0]
        position_bonus = position_team_bonuses.get(position, {}).get(team, 0)
        team_tier_score = base_team_score + position_bonus
        
        # Combine team quality and depth chart position
        team_context_score = (team_tier_score * 0.7) + (depth_score * 0.3)
        
        team_scores.append({
            'player_id': player_id,
            'team_context_score': team_context_score,
            'current_team': team,
            'depth_chart_rank': current_team_info['pos_rank'].iloc[0] if not current_team_info.empty else None
        })
    
    return pd.DataFrame(team_scores)

def create_fantasy_rankings(df, current_teams):
    """
    Create comprehensive fantasy draft rankings
    """
    print("Creating fantasy draft rankings...")
    
    # Get latest season data for each player (2025 for rookies, most recent for veterans)
    latest_data = []
    
    for player_id in df['player_id'].unique():
        player_data = df[df['player_id'] == player_id].copy()
        
        # For rookies, use 2025 data; for others, use most recent season
        if (player_data['player_type'] == 'rookie').any():
            latest = player_data[player_data['season'] == 2025].iloc[0] if len(player_data[player_data['season'] == 2025]) > 0 else player_data.iloc[-1]
        else:
            latest = player_data.loc[player_data['season'].idxmax()]
        
        latest_data.append(latest)
    
    rankings_df = pd.DataFrame(latest_data)
    
    # Calculate component scores
    injury_scores = calculate_injury_risk_score(df)
    consistency_scores = calculate_consistency_score(df)
    team_context_scores = calculate_team_context_score(df, current_teams)
    
    # Merge all scores
    rankings_df = rankings_df.merge(injury_scores, on='player_id', how='left')
    rankings_df = rankings_df.merge(consistency_scores, on='player_id', how='left')
    rankings_df = rankings_df.merge(team_context_scores, on='player_id', how='left')
    
    # Fill missing scores with neutral values
    rankings_df['injury_risk_score'] = rankings_df['injury_risk_score'].fillna(0.5)
    rankings_df['consistency_score'] = rankings_df['consistency_score'].fillna(0.5)
    rankings_df['team_context_score'] = rankings_df['team_context_score'].fillna(0.6)
    
    # Handle missing fantasy points (especially for rookies)
    rankings_df['fantasy_points_ppr'] = rankings_df['fantasy_points_ppr'].fillna(0)
    rankings_df['ppg'] = rankings_df['ppg'].fillna(0)
    
    # For players with 0 fantasy points, use projected values if available
    zero_points_mask = rankings_df['fantasy_points_ppr'] == 0
    if 'projected_fantasy_points' in rankings_df.columns:
        rankings_df.loc[zero_points_mask, 'fantasy_points_ppr'] = rankings_df.loc[zero_points_mask, 'projected_fantasy_points'].fillna(0)
    
    # Calculate base fantasy value (normalize by position)
    position_medians = rankings_df.groupby('position')['fantasy_points_ppr'].median()
    rankings_df['position_adjusted_points'] = rankings_df.apply(
        lambda x: x['fantasy_points_ppr'] / position_medians.get(x['position'], 1) if position_medians.get(x['position'], 1) > 0 else 0, 
        axis=1
    )
    
    # Apply TE penalty - only top TEs should rank highly
    te_penalty_threshold = rankings_df[rankings_df['position'] == 'TE']['fantasy_points_ppr'].quantile(0.8)
    rankings_df.loc[
        (rankings_df['position'] == 'TE') & 
        (rankings_df['fantasy_points_ppr'] < te_penalty_threshold), 
        'position_adjusted_points'
    ] *= 0.6  # Heavy penalty for mid-tier TEs
    
    # Apply positional scarcity
    scarcity_adj = get_positional_scarcity_adjustments()
    rankings_df['scarcity_multiplier'] = rankings_df['position'].map(scarcity_adj)
    
    # Calculate final composite score
    # Weights: Production (45%), Consistency (25%), Health (20%), Team Context (10%)
    rankings_df['base_score'] = rankings_df['position_adjusted_points'] * rankings_df['scarcity_multiplier']
    
    rankings_df['composite_score'] = (
        rankings_df['base_score'] * 0.45 +
        rankings_df['consistency_score'] * 0.25 +
        (1 - rankings_df['injury_risk_score']) * 0.20 +  # Flip injury risk (lower risk = higher score)
        rankings_df['team_context_score'] * 0.10
    )
    
    # Create positional rankings
    rankings_df['overall_rank'] = rankings_df['composite_score'].rank(method='dense', ascending=False)
    rankings_df['position_rank'] = rankings_df.groupby('position')['composite_score'].rank(method='dense', ascending=False)
    
    # Select and order columns for output
    output_columns = [
        'overall_rank', 'position_rank', 'player_name', 'position', 'current_team',
        'player_type', 'fantasy_points_ppr', 'ppg', 'composite_score',
        'consistency_score', 'injury_risk_score', 'team_context_score',
        'avg_games_per_season', 'depth_chart_rank'
    ]
    
    # Add available columns
    final_columns = [col for col in output_columns if col in rankings_df.columns]
    rankings_df = rankings_df[final_columns].copy()
    
    # Sort by overall rank
    rankings_df = rankings_df.sort_values('overall_rank').reset_index(drop=True)
    
    return rankings_df

def generate_tier_analysis(rankings_df):
    """
    Generate tier analysis for each position
    """
    print("Generating tier analysis...")
    
    tiers = {}
    
    for position in ['QB', 'RB', 'WR', 'TE']:
        pos_players = rankings_df[rankings_df['position'] == position].copy()
        
        if len(pos_players) == 0:
            continue
        
        # Create tiers based on composite score gaps
        scores = pos_players['composite_score'].values
        score_diffs = np.diff(scores)
        
        # Find natural breakpoints (large drops in score)
        if len(score_diffs) > 0:
            percentile_80 = np.percentile(np.abs(score_diffs), 80)
            tier_breaks = np.where(np.abs(score_diffs) > percentile_80)[0] + 1
        else:
            tier_breaks = []
        
        # Add tier 1 start and end
        tier_breaks = np.concatenate(([0], tier_breaks, [len(pos_players)]))
        tier_breaks = np.unique(tier_breaks)
        
        pos_tiers = {}
        for i in range(len(tier_breaks) - 1):
            start_idx = tier_breaks[i]
            end_idx = tier_breaks[i + 1]
            tier_players = pos_players.iloc[start_idx:end_idx]
            
            pos_tiers[f'Tier {i + 1}'] = {
                'players': tier_players['player_name'].tolist(),
                'rank_range': f"{int(tier_players['position_rank'].min())}-{int(tier_players['position_rank'].max())}",
                'avg_score': tier_players['composite_score'].mean(),
                'count': len(tier_players)
            }
            
            # Limit to top 5 tiers
            if i >= 4:
                break
        
        tiers[position] = pos_tiers
    
    return tiers

def print_rankings_summary(rankings_df, tiers, top_n=200):
    """
    Print a nice summary of the rankings
    """
    print(f"\n🏈 FANTASY FOOTBALL DRAFT RANKINGS (Top {top_n})")
    print("=" * 80)
    print("Methodology: Prioritizes consistency and health over boom/bust players")
    print("Weights: Production (40%), Consistency (30%), Health (20%), Team Context (10%)")
    print("=" * 80)
    
    # Overall top players
    print(f"\n📊 OVERALL TOP {min(top_n, len(rankings_df))}:")
    top_players = rankings_df.head(top_n)
    
    print(f"{'Rank':<4} {'Name':<25} {'Pos':<3} {'Team':<4} {'Type':<8} {'PPG':<6} {'Score':<6} {'Health':<7} {'Consistency':<11}")
    print("-" * 80)
    
    for _, player in top_players.iterrows():
        health_grade = 'A' if player['injury_risk_score'] < 0.3 else 'B' if player['injury_risk_score'] < 0.6 else 'C'
        consistency_grade = 'A' if player['consistency_score'] > 0.7 else 'B' if player['consistency_score'] > 0.5 else 'C'
        
        print(f"{int(player['overall_rank']):<4} {str(player['player_name'])[:24]:<25} "
              f"{player['position']:<3} {str(player.get('current_team', 'UNK')):<4} "
              f"{str(player['player_type'])[:8]:<8} {player['ppg']:<6.1f} "
              f"{player['composite_score']:<6.2f} {health_grade:<7} {consistency_grade:<11}")
    
    # Position breakdowns
    for position in ['QB', 'RB', 'WR', 'TE']:
        print(f"\n📈 {position} TIERS:")
        if position in tiers:
            for tier_name, tier_data in tiers[position].items():
                player_list = ", ".join(tier_data['players'][:8])  # Show first 8 players
                if len(tier_data['players']) > 8:
                    player_list += f"... (+{len(tier_data['players']) - 8} more)"
                
                print(f"  {tier_name} (Ranks {tier_data['rank_range']}): {player_list}")
        
        # Top 12 for this position
        pos_top = rankings_df[rankings_df['position'] == position].head(12)
        print(f"\n  Top 12 {position}s:")
        for _, player in pos_top.iterrows():
            consistency_indicator = "🟢" if player['consistency_score'] > 0.7 else "🟡" if player['consistency_score'] > 0.5 else "🔴"
            health_indicator = "💪" if player['injury_risk_score'] < 0.3 else "⚠️" if player['injury_risk_score'] > 0.6 else "✅"
            
            print(f"    {int(player['position_rank']):2}. {player['player_name']:<20} ({player.get('current_team', 'UNK')}) "
                  f"{player['ppg']:5.1f} PPG {consistency_indicator}{health_indicator}")

def main_rankings(df, current_teams):
    """
    Main function to generate and display rankings
    """
    print("🚀 Starting Fantasy Football Draft Rankings Generation...")
    print("=" * 60)
    
    # Filter to fantasy relevant players only
    fantasy_relevant = df[
        (df['position'].isin(['QB', 'RB', 'WR', 'TE'])) &
        (
            (df['fantasy_points_ppr'] > 0) |  # Has production
            (df['player_type'] == 'rookie') |  # Or is a rookie
            (df['targets'].fillna(0) >= 10) |  # Or has opportunity
            (df['carries'].fillna(0) >= 20)
        )
    ].copy()
    
    print(f"Analyzing {len(fantasy_relevant)} fantasy relevant players...")
    
    # Generate rankings
    rankings_df = create_fantasy_rankings(fantasy_relevant, current_teams)
    
    # Generate tier analysis
    tiers = generate_tier_analysis(rankings_df)
    
    # Print summary
    print_rankings_summary(rankings_df, tiers, top_n=150)
    
    # Save to CSV
    rankings_df.to_csv('fantasy_draft_rankings_2025.csv', index=False)
    print(f"\n✅ Rankings saved to: fantasy_draft_rankings_2025.csv")
    
    return rankings_df, tiers

# Usage example:
# rankings, tiers = main_rankings(df, current_teams)

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
        season_df = season_df.merge(season_consistency, on='player_id', how='left', suffixes=('', '_consistency'))
        
        # Add draft information - be explicit about suffixes to avoid conflicts
        if not all_draft_data.empty:
            # Drop any season column from draft data if it exists to avoid conflicts
            draft_cols_to_merge = [col for col in all_draft_data.columns if col != 'season']
            draft_data_clean = all_draft_data[draft_cols_to_merge].copy()
            season_df = season_df.merge(draft_data_clean, on='player_id', how='left', suffixes=('', '_draft'))
        
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
        
        # Add team context - avoid column conflicts
        team_col = 'recent_team'
        if not team_context.empty and team_col in season_df.columns:
            merge_col = 'team_abbr' if 'team_abbr' in team_context.columns else 'team'
            # Only select necessary columns from team_context to avoid conflicts
            team_context_cols = ['team_abbr'] if 'team_abbr' in team_context.columns else ['team']
            team_context_cols += [col for col in team_context.columns if col.startswith('team_') and col not in team_context_cols]
            
            season_df = season_df.merge(
                team_context[team_context_cols], 
                left_on=team_col, 
                right_on=merge_col, 
                how='left', 
                suffixes=('', '_team_context')
            )
        
        all_seasons_data.append(season_df)
    
    # Combine all seasons
    if all_seasons_data:
        df = pd.concat(all_seasons_data, ignore_index=True, sort=False)
    else:
        df = pd.DataFrame()
    
    # Fix any column naming issues from merges
    if 'season_x' in df.columns and 'season' not in df.columns:
        df = df.rename(columns={'season_x': 'season'})
    if 'season_y' in df.columns:
        df = df.drop(columns=['season_y'])
    
    print("Columns after initial merge:", df.columns.tolist()[:20])  # Debug print
    
    if not current_teams.empty:
        # Merge current team info with main dataframe
        df = df.merge(
            current_teams[['player_id', 'current_team_2025', 'pos_abb', 'pos_rank', 'pos_slot']],
            on='player_id',
            how='left',
            suffixes=('', '_current')
        )
        
        # For 2025 data, update recent_team with current_team_2025 if available
        if 'season' in df.columns:  # Make sure season column exists
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
                    if f'{stat}_hist' in df_2025.columns:
                        df_2025[stat] = df_2025[stat].fillna(df_2025[f'{stat}_hist'])
                        df_2025 = df_2025.drop(columns=[f'{stat}_hist'])
                
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
    
    # Final column cleanup - remove any remaining duplicate season columns
    duplicate_cols = [col for col in df.columns if col.endswith('_x') or col.endswith('_y')]
    if duplicate_cols:
        print(f"Dropping duplicate columns: {duplicate_cols}")
        df = df.drop(columns=duplicate_cols)
    
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
    
    # Get the raw data (we'll need current_teams for rankings)
    seasonal_stats, weekly_data, player_info, current_teams = get_player_data()
    
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
    
    return df_final, current_teams

if __name__ == "__main__":
    fantasy_df, current_teams = main()
    
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
    
    # Generate draft rankings using the current_teams data we already have
    print("\n" + "="*60)
    print("GENERATING FANTASY DRAFT RANKINGS...")
    print("="*60)
    
    try:
        # Generate draft rankings
        rankings, tiers = main_rankings(fantasy_df, current_teams)
        
        # Show some key insights
        print("\n🎯 KEY INSIGHTS:")
        print("-" * 40)
        
        # Top rookies
        top_rookies = rankings[rankings['player_type'] == 'rookie'].head(10)
        if not top_rookies.empty:
            print(f"\n📈 Top 10 Rookies:")
            for _, rookie in top_rookies.iterrows():
                consistency = "High" if rookie['consistency_score'] > 0.6 else "Medium" if rookie['consistency_score'] > 0.4 else "Low"
                health = "Excellent" if rookie['injury_risk_score'] < 0.4 else "Good" if rookie['injury_risk_score'] < 0.6 else "Concerning"
                print(f"  {int(rookie['overall_rank']):3}. {rookie['player_name']:<20} {rookie['position']:<2} ({rookie.get('current_team', 'UNK')}) - Consistency: {consistency}, Health: {health}")
        
        # Most consistent veterans
        consistent_vets = rankings[
            (rankings['player_type'] == 'veteran') & 
            (rankings['consistency_score'] > 0.7)
        ].head(15)
        
        if not consistent_vets.empty:
            print(f"\n🎯 Most Consistent Veterans (Consistency Score > 0.7):")
            for _, vet in consistent_vets.iterrows():
                games_avg = vet.get('avg_games_per_season', 'N/A')
                print(f"  {int(vet['overall_rank']):3}. {vet['player_name']:<20} {vet['position']:<2} ({vet.get('current_team', 'UNK')}) - {games_avg:.1f} games/yr avg")
        
        # Injury concerns
        injury_concerns = rankings[rankings['injury_risk_score'] > 0.7].head(10)
        if not injury_concerns.empty:
            print(f"\n⚠️  Injury Risk Concerns (Risk Score > 0.7):")
            for _, player in injury_concerns.iterrows():
                games_avg = player.get('avg_games_per_season', 'N/A')
                print(f"  {int(player['overall_rank']):3}. {player['player_name']:<20} {player['position']:<2} - {games_avg:.1f} games/yr avg")
        
        # Value picks (good players ranked lower due to injury/consistency concerns)
        potential_values = rankings[
            (rankings['fantasy_points_ppr'] > rankings['fantasy_points_ppr'].quantile(0.7)) &
            (rankings['overall_rank'] > 50)
        ].head(10)
        
        if not potential_values.empty:
            print(f"\n💎 Potential Value Picks (High Production, Lower Rank due to Risk):")
            for _, player in potential_values.iterrows():
                risk_reason = "Injury Risk" if player['injury_risk_score'] > 0.6 else "Inconsistency" if player['consistency_score'] < 0.5 else "Team Context"
                print(f"  {int(player['overall_rank']):3}. {player['player_name']:<20} {player['position']:<2} - {player['ppg']:.1f} PPG (Risk: {risk_reason})")
        
        print(f"\n✅ Complete rankings saved to: fantasy_draft_rankings_2025.csv")
        print(f"✅ Use this for your draft preparation!")
        
    except Exception as e:
        print(f"\n❌ Error generating rankings: {e}")
        print("Check that all required functions are defined and current_teams data is valid.")
        import traceback
        traceback.print_exc()