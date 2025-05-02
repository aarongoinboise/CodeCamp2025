import pandas as pd
from collections import Counter

ids = pd.read_csv('MTeams.csv', index_col=False)[['TeamID', 'TeamName']]

df = pd.read_csv('MRegularSeasonDetailedResults.csv')
df = df[df['Season'] == 2025]
name_to_id = dict(zip(ids['TeamName'], ids['TeamID']))

# Initialize an empty dictionary to store the summed statistics for each team
team_stats = {}
team_appearances = {}

# Iterate over each game in the dataframe
for _, row in df.iterrows():
    # Update stats for the winning team
    if row['WTeamID'] not in team_stats:
        team_stats[row['WTeamID']] = {'Score': 0, 'Score Diff': 0, 'FGM': 0, 'FGM Diff': 0,
            'FGM3': 0, 'FGM3 Diff': 0, 'TO': 0, 'TO Diff': 0}
    team_stats[row['WTeamID']]['Score'] += row['WScore']
    team_stats[row['WTeamID']]['Score Diff'] += (row['WScore'] - row['LScore'])
    team_stats[row['WTeamID']]['FGM'] += row['WFGM']
    team_stats[row['WTeamID']]['FGM Diff'] += (row['WFGM'] - row['LFGM'])
    team_stats[row['WTeamID']]['FGM3'] += row['WFGM3']
    team_stats[row['WTeamID']]['FGM3 Diff'] += (row['WFGM3'] - row['LFGM3'])
    team_stats[row['WTeamID']]['TO'] += row['WTO']
    team_stats[row['WTeamID']]['TO Diff'] += (row['WTO'] - row['LTO'])
    team_appearances[row['WTeamID']] = team_appearances.get(row['WTeamID'], 0) + 1
    
    # Update stats for the losing team
    if row['LTeamID'] not in team_stats:
        team_stats[row['LTeamID']] = {'Score': 0, 'Score Diff': 0, 'FGM': 0, 'FGM Diff': 0,
            'FGM3': 0, 'FGM3 Diff': 0, 'TO': 0, 'TO Diff': 0}
    team_stats[row['LTeamID']]['Score'] += row['LScore']
    team_stats[row['LTeamID']]['Score Diff'] += (row['LScore'] - row['WScore'])
    team_stats[row['LTeamID']]['FGM'] += row['LFGM']
    team_stats[row['LTeamID']]['FGM Diff'] += (row['LFGM'] - row['WFGM'])
    team_stats[row['LTeamID']]['FGM3'] += row['LFGM3']
    team_stats[row['LTeamID']]['FGM3 Diff'] += (row['LFGM3'] - row['WFGM3'])
    team_stats[row['LTeamID']]['TO'] += row['LTO']
    team_stats[row['LTeamID']]['TO Diff'] += (row['LTO'] - row['WTO'])
    team_appearances[row['LTeamID']] = team_appearances.get(row['LTeamID'], 0) + 1

# Convert the dictionary into a DataFrame
team_stats_df = pd.DataFrame.from_dict(team_stats, orient='index').reset_index()
team_stats_df.columns = ['TeamID', 'TotalScore', 'TotalScoreDiff', 'TotalFGM', 'TotalFGMDiff',
                         'TotalFGM3', 'TotalFGM3Diff', 'TotalTO', 'TotalTODiff']
team_stats_df['TotalAppearances'] = team_stats_df['TeamID'].map(team_appearances)
team_stats_df['AvgScore'] = team_stats_df['TotalScore'] / team_stats_df['TotalAppearances']
team_stats_df['AvgScoreDiff'] = team_stats_df['TotalScoreDiff'] / team_stats_df['TotalAppearances']
team_stats_df['AvgFGM'] = team_stats_df['TotalFGM'] / team_stats_df['TotalAppearances']
team_stats_df['AvgFGMDiff'] = team_stats_df['TotalFGMDiff'] / team_stats_df['TotalAppearances']
team_stats_df['AvgFGM3'] = team_stats_df['TotalFGM3'] / team_stats_df['TotalAppearances']
team_stats_df['AvgFGM3Diff'] = team_stats_df['TotalFGM3Diff'] / team_stats_df['TotalAppearances']
team_stats_df['AvgTO'] = team_stats_df['TotalTO'] / team_stats_df['TotalAppearances']
team_stats_df['AvgTODiff'] = team_stats_df['TotalTODiff'] / team_stats_df['TotalAppearances']
team_stats_df.to_csv('testts.csv', index=False)

id_counts = Counter(team_stats.keys())
duplicates = [team_id for team_id, count in id_counts.items() if count > 1]

if duplicates:
    print(f"Duplicate TeamIDs found: {duplicates}")
else:
    print("All TeamIDs are unique.")

# Get the games that will be played
slots = pd.read_csv('MNCAATourneySeedRoundSlots.csv')
seeds = pd.read_csv('MNCAATourneySeeds.csv')
seeds_specific = seeds[seeds['Season'] == 2025][['Seed', 'TeamID']]
team_id_to_seed = dict(zip(seeds_specific['TeamID'], seeds_specific['Seed'].str.replace(r'[A-Za-z]', '', regex=True)))

# only include seeds that map to players
slots = slots[slots['Seed'].isin(seeds_specific['Seed'])]
slots = slots.merge(seeds_specific, on='Seed', how='left')
slots['Seed'] = slots['TeamID']
slots = slots.drop(columns='TeamID')

grouped_slots = slots.groupby(['GameRound', 'GameSlot'], as_index=False).agg({'Seed': lambda x: list(x)})
grouped_slots = grouped_slots.rename(columns={'Seed': 'SeedPossibilities'})
grouped_slots.to_csv('testg.csv', index=False)

# Maryland vs Colorado St
m_id = name_to_id['Maryland']
cs_id = name_to_id['Colorado St'] 
check_r = grouped_slots[grouped_slots['SeedPossibilities'].apply(lambda x: m_id in x and cs_id in x)]
check_r = check_r.loc[check_r['GameRound'].idxmin()]
print(check_r)

m_r = team_stats_df[team_stats_df['TeamID'] == m_id]
cs_r = team_stats_df[team_stats_df['TeamID'] == cs_id]
print(m_r.columns)

vals = [
    team_id_to_seed[m_id] - team_id_to_seed[cs_id],
    m_r['AvgScoreDiff'],
    m_r['AvgFGMDiff'],
    m_r['AvgFGM3Diff'],
    m_r['AvgTODiff'],
    cs_r['AvgScoreDiff'],
    cs_r['AvgFGMDiff'],
    cs_r['AvgFGM3Diff'],
    cs_r['AvgTODiff']
]