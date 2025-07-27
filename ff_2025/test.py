import pandas as pd

url = 'https://www.pro-football-reference.com/years/2024/coaches.htm'
df = pd.read_html(url)[0]
new_cols = pd.MultiIndex.from_tuples([
    (lvl0.replace('2024', '2025'), lvl1)
    for lvl0, lvl1 in df.columns
])

new_df = pd.DataFrame(columns=new_cols)
teams = [
    "BAL", "BUF", "CIN", "CLE", "DEN", "HOU", "IND", "JAX",
    "KAN", "LVR", "LAC", "MIA", "NWE", "NYJ", "PIT", "TEN",
    "ARI", "ATL", "CAR", "CHI", "DAL", "DET", "GNB", "LAR",
    "MIN", "NOR", "NYG", "PHI", "SFO", "SEA", "TAM", "WAS"
]

coaches = [
    "John Harbaugh", "Sean McDermott", "Zac Taylor", "Kevin Stefanski",
    "Sean Payton", "DeMeco Ryans", "Shane Steichen", "Liam Coen",
    "Andy Reid", "Pete Carroll", "Jim Harbaugh", "Mike McDaniel",
    "Mike Vrabel", "Aaron Glenn", "Mike Tomlin", "Brian Callahan",
    "Jonathan Gannon", "Raheem Morris", "Dave Canales", "Ben Johnson",
    "Brian Schottenheimer", "Dan Campbell", "Matt LaFleur", "Sean McVay",
    "Kevin O'Connell", "Kellen Moore", "Brian Daboll", "Nick Sirianni",
    "Kyle Shanahan", "Mike Macdonald", "Todd Bowles", "Dan Quinn"
]

for coach, team in zip(coaches, teams):
    match_coach = df[df[('Unnamed: 0_level_0', 'Coach')] == coach]
    row = []
    for col in new_df.columns:
        if col[1] == 'Remark':
            continue
        if col[1] == 'Coach':
            row.append(coach)
        elif col[1] == 'Tm':
            row.append(team)
        elif col[0] == 'w/ Team':
            match_team = match_coach[match_coach[('Unnamed: 1_level_0', 'Tm')] == team]
            if not match_team.empty and col in df.columns:
                row.append(match_team.iloc[0][col])
            else:
                row.append(pd.NA)
        elif col in df.columns:
            if not match_coach.empty:
                row.append(match_coach.iloc[0][col])
            else:
                row.append(pd.NA)
        else:
            row.append(pd.NA)
    new_df.loc[len(new_df)] = row
    
print(new_df)