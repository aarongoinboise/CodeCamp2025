import pandas as pd

def getter(exclude_columns, scrape, year, keyz, coach=False):
    l = []
    for i in range(2):
        l.append(scrape(year, i))
    prev_year_df = l[1]
    curr_year_df = l[0]
    columns_to_update = [col for col in prev_year_df.columns if col not in exclude_columns]
    for idx, row in curr_year_df.iterrows():
        # Try matching based on 
        if len(keyz) == 3:
            match = prev_year_df[(prev_year_df[keyz[0]] == row[keyz[0]]) & 
                                (prev_year_df[keyz[1]] == row[keyz[1]]) & 
                                (prev_year_df[keyz[2]] == row[keyz[2]])]
            if match.empty:
                match = prev_year_df[(prev_year_df[keyz[0]] == row[keyz[0]]) & 
                                    (prev_year_df[keyz[1]] == row[keyz[1]])]
        elif len(keyz) == 2:
            match = prev_year_df[(prev_year_df[keyz[0]] == row[keyz[0]]) & 
                                  (prev_year_df[keyz[1]] == row[keyz[1]])]
        else:
            match = prev_year_df[(prev_year_df[keyz[0]] == row[keyz[0]])]
            
        if match.empty:
            # If no match found, use zeros
            curr_year_df.loc[idx, columns_to_update] = 0
            if coach:
                curr_year_df.loc[idx, 'w/same_team'] = 0 
        else:
            # Otherwise, assign the previous year values to the current year
            curr_year_df.loc[idx, columns_to_update] = match.iloc[0, :][columns_to_update].values
            if coach:
                if match.iloc[0]['Tm'] == row['Tm']:
                    curr_year_df.loc[idx, 'w/same_team'] = 1
                else:
                    curr_year_df.loc[idx, 'w/same_team'] = 0

    return curr_year_df