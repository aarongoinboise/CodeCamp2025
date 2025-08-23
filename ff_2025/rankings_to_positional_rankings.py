import pandas as pd

# Load CSV
df = pd.read_csv('fantasy_draft_rankings_2025.csv')

# Create Excel writer
with pd.ExcelWriter('fantasy_draft_rankings_2025_by_position.xlsx', engine='xlsxwriter') as writer:
    # Iterate over unique positions
    for pos in df['position'].unique():
        # Filter by position and sort by position_rank
        df_pos = df[df['position'] == pos].sort_values('position_rank')
        # Write to sheet named after position
        df_pos.to_excel(writer, sheet_name=pos, index=False)