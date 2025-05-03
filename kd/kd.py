import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# Load data
train_df = pd.read_excel("train.xlsx")
test_df = pd.read_excel("test.xlsx")

# Combine for consistent preprocessing
test_df['KD Place'] = np.nan
df = pd.concat([train_df, test_df], ignore_index=True)

# Replace NA and blanks
df.replace({'NA': np.nan, '': np.nan}, inplace=True)

# Convert numeric columns
numeric_cols = ['Last Beyer', 'Second Beyer', 'Third back Beyer', 'BRIS DIST',
                'Tomlinson (DST)', 'Tomlinson (Wet)', 'AWD Sire', "AWD Dam's Sire", 'Dosage Index']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

# Parse odds
def parse_odds(val):
    if isinstance(val, str) and '-' in val:
        a, b = val.split('-')
        return float(a) / float(b)
    return np.nan

df['Morning Line'] = df['Morning Line'].apply(parse_odds).fillna(0)

# Extract place and race
def extract_place_and_race(x):
    m = re.match(r"(\d+)[a-z]{2},?\s*(.*)", str(x).strip(), flags=re.IGNORECASE)
    return pd.Series([int(m.group(1)) if m else 0,
                      m.group(2).strip().lower().replace(' ', '_') if m else str(x).strip().lower().replace(' ', '_')])

df[['Last Prep Place', 'Last Prep Race']] = df['Last Prep/Finish'].apply(extract_place_and_race)

# Replace KD Place -1 with 0, fill NaNs with 0
df['KD Place'] = df['KD Place'].replace(-1, 0).fillna(0)

# Encode string columns
string_cols = ['Horse', 'Trainer', 'Jockey', 'Sire', 'Dam', "Dam's Sire", 'Last Prep Race']
df[string_cols] = df[string_cols].apply(lambda x: x.str.lower().str.replace(r'\s+', '_', regex=True))
encoders = {}
for col in string_cols:
    le = LabelEncoder()
    df[col] = le.fit_transform(df[col].astype(str))
    encoders[col] = le

# Split back
train_processed = df[:len(train_df)].copy()
test_processed = df[len(train_df):].copy()

# Train model
features = train_processed.drop(columns=['Last Prep/Finish', 'KD Place'])
target = train_processed['KD Place']
model = RandomForestClassifier(random_state=42)
model.fit(features, target)

# Predict
test_processed['KD Place Predicted'] = model.predict(test_processed.drop(columns=['Last Prep/Finish', 'KD Place']))
test_processed[['Horse', 'KD Place Predicted']].to_excel("test_with_predictions.xlsx", index=False)