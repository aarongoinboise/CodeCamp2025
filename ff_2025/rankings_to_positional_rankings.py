import pandas as pd
import xlsxwriter

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
        
        # Get the workbook and worksheet objects
        workbook = writer.book
        worksheet = writer.sheets[pos]
        
        # Define formats
        consistent_format = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})  # Light green
        
        # Apply highlighting for Most Consistent Veterans (Consistency Score > 0.7)
        if 'consistency_score' in df_pos.columns:
            # Find the column index for consistency_score
            col_idx = df_pos.columns.get_loc('consistency_score') + 1  # +1 because Excel is 1-indexed
            
            # Apply conditional formatting to highlight rows with consistency_score > 0.7
            worksheet.conditional_format(1, 0, len(df_pos), len(df_pos.columns) - 1, {
                'type': 'formula',
                'criteria': f'=INDIRECT(ADDRESS(ROW(), {col_idx})) > 0.7',
                'format': consistent_format
            })
            print(f"Highlighted {len(df_pos[df_pos['consistency_score'] > 0.7])} consistent veterans in {pos} position")

print("Excel file created with highlighted consistent veterans!")