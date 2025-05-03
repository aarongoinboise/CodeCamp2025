import pandas as pd
import numpy as np
import re
from sklearn.preprocessing import LabelEncoder
from sklearn.impute import SimpleImputer
import xgboost as xgb
from sklearn.metrics import mean_squared_error

# Load data
train_df = pd.read_excel("train.xlsx")
test_df = pd.read_excel("test.xlsx")
original_horses = test_df['Horse'].copy()

# Combine for consistent preprocessing
test_df['KD Place'] = np.nan
df = pd.concat([train_df, test_df], ignore_index=True)

# Replace NA and blanks
df.replace({'NA': np.nan, '': np.nan}, inplace=True)

# Convert numeric columns
numeric_cols = ['Last Beyer', 'Second Beyer', 'Third back Beyer', 'BRIS DIST',
                'Tomlinson (DST)', 'Tomlinson (Wet)', 'AWD Sire', "AWD Dam's Sire", 'Dosage Index']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

# Parse odds (Morning Line)
def parse_odds(val):
    if isinstance(val, str) and '-' in val:
        a, b = val.split('-')
        return float(a) / float(b)
    return np.nan

df['Morning Line'] = df['Morning Line'].apply(parse_odds).fillna(0)

# Invert the odds to make lower odds (better chances) higher weight
df['Morning Line Weighted'] = 1 / df['Morning Line']
df['Morning Line Weighted'] = df['Morning Line Weighted'].replace([np.inf, -np.inf], np.nan).fillna(0)

# Apply stronger scaling for odds
df['Morning Line Weighted'] = np.log(df['Morning Line Weighted'] + 1) * 10  # Higher weight on odds

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

# Add weighted odds to features
features = train_processed.drop(columns=['Last Prep/Finish', 'KD Place']).copy()
features['Morning Line Weighted'] = df.loc[features.index, 'Morning Line Weighted']
target = train_processed['KD Place']

X_test = test_processed.drop(columns=['Last Prep/Finish', 'KD Place']).copy()
X_test['Morning Line Weighted'] = df.iloc[len(train_df):].reset_index(drop=True)['Morning Line Weighted']

# Impute missing values for numerical features
imputer = SimpleImputer(strategy='mean')  # You can also use 'median' or 'most_frequent' as strategy
features[numeric_cols] = imputer.fit_transform(features[numeric_cols])

# For the string columns, we can use a similar imputer but for categorical values
imputer_cat = SimpleImputer(strategy='most_frequent')
features[string_cols] = imputer_cat.fit_transform(features[string_cols])

# Impute missing values in test set
X_test[numeric_cols] = imputer.transform(X_test[numeric_cols])
X_test[string_cols] = imputer_cat.transform(X_test[string_cols])

# Train XGBoost model
model = xgb.XGBClassifier(random_state=42, use_label_encoder=False, eval_metric='mlogloss')
model.fit(features, target)

# Predict
preds = model.predict(X_test)
preds[:] = -1

# Get probabilities and pick top 5 most confident predictions
probs = model.predict_proba(X_test)
top5_indices = np.argsort(np.max(probs, axis=1))[-5:][::-1]

# Assign labels 1–5 based on confidence
for label, idx in enumerate(top5_indices, start=1):
    preds[idx] = label

test_processed['KD Place Predicted'] = preds
test_processed['Horse'] = original_horses.values
test_processed[['Horse', 'Morning Line', 'KD Place Predicted']].to_excel("test_with_predictions.xlsx", index=False)
