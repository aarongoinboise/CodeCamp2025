from contextlib import contextmanager
import random
import cbbpy.mens_scraper as s
from datetime import datetime, timedelta
import pandas as pd
import os
import sys
import warnings
import logging

# 3/20
# 1   Texas A&M Aggies
# 0   Missouri Tigers
# 1   UCLA Bruins
# 0   St. John's Red Storm
# 0   Michigan Wolverines
# 0   Texas Tech Red Raiders
# 1   Mississippi State Bulldogs
# 0   Alabama Crimson Tide
# 0   Iowa State Cyclones
# 0   Memphis Tigers
# 0   Duke Blue Devils
# 1   Saint Mary's Gaels
# 0   Ole Miss Rebels
# 0   Florida Gators
# 0   Kentucky Wildcats
# 1   Marquette Golden Eagles
# 0   Arizona Wildcats
# 1   UConn Huskies
# 0   Illinois Fighting Illini
# 0   Michigan State Spartans
# 0   Oregon Ducks



start_date = (datetime.today() - timedelta(days=13)).strftime("%Y-%m-%d")
end_date = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

final_games = []
non_final_games = []

# Loop through each date in the range from start_date to end_date
current_date = datetime.strptime(start_date, "%Y-%m-%d")
end_date = datetime.strptime(end_date, "%Y-%m-%d")
while current_date <= end_date:
    game_ids = s.get_game_ids(current_date)
    for id in game_ids:
        a = s.get_game_info(id)
        game_data = a.to_dict(orient="records")[0]
        if game_data["game_status"] == "Final":
            final_games.append(game_data)
        else:
            non_final_games.append(game_data)
    
    current_date += timedelta(days=1)

train_test_df = pd.DataFrame(final_games)
predict_df = pd.DataFrame(non_final_games)

# Clean up data
print('done with data retrieval')
print(f"final game len: {len(final_games)} other games: {len(non_final_games)}")
train_test_df = train_test_df.dropna(subset=["home_team", "away_team", "home_rank", "away_rank"], how="any")
predict_df = predict_df.dropna(subset=["home_team", "away_team", "home_rank", "away_rank"], how="any")

home_away_teams = zip(predict_df["home_team"], predict_df["away_team"])
team_num_map = {}
team_num = 1

print('before for')
# Process categorical data
for col in train_test_df.select_dtypes(include=["object", "category"]).columns:
    if col in ["home_team", "away_team"]:
        for team in pd.concat([train_test_df[col], predict_df[col]]).dropna().unique():
            if team not in team_num_map:
                team_num_map[team_num] = team
                team_num += 1
        reverse_team_num_map = {v: k for k, v in team_num_map.items()}
        train_test_df[col] = train_test_df[col].map(reverse_team_num_map)
        predict_df[col] = predict_df[col].map(reverse_team_num_map)
    else:
        train_test_df[col] = pd.Categorical(train_test_df[col])
        predict_df[col] = pd.Categorical(predict_df[col])
        train_test_df[col] = train_test_df[col].cat.codes
        predict_df[col] = predict_df[col].cat.codes
# Convert boolean columns to int
train_test_df = train_test_df.astype({col: int for col in train_test_df.select_dtypes(include=["bool"]).columns})
predict_df = predict_df.astype({col: int for col in predict_df.select_dtypes(include=["bool"]).columns})

# Filter train data for valid scores (home_score and away_score)
train_test_df = train_test_df[(train_test_df["home_score"] > 0) & (train_test_df["away_score"] > 0)]

# Set target columns
y_train_home = train_test_df["home_score"]
y_train_away = train_test_df["away_score"]
X_train = train_test_df.drop(columns=["home_score", "away_score"])

# Prepare test data
predict_df = predict_df.drop(columns=["home_score", "away_score"], errors="ignore")
X_test = predict_df.copy()

param_distributions = {
    'generations': [5, 10, 15],
    'population_size': [20, 50, 100],
    'cv': [3, 5],
    'random_state': [12, 42, 100],
}

print('before fit')
# Suppress all stdout and stderr
sys.stdout = open(os.devnull, 'w')
sys.stderr = open(os.devnull, 'w')
import warnings
warnings.filterwarnings("ignore")
import logging
logging.disable(logging.CRITICAL)
from tpot import TPOTClassifier
from sklearn.model_selection import RandomizedSearchCV
tpot = TPOTClassifier()
search = RandomizedSearchCV(
    tpot,
    param_distributions,
    n_iter=10,
    scoring='r2',
    cv=3,
    n_jobs=-1,
    random_state=42,
    verbose = 0
)
search.fit(X_train, y_train_home)
home_model = search.best_estimator_
away_model = TPOTClassifier(**search.best_params_, verbosity=0)
away_model.fit(X_train, y_train_away)
sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__
print('after fit')

# Predict future game scores
missing_cols = X_test.columns[X_test.isnull().any()]
known_cols = [col for col in missing_cols if col in X_train.columns]
print(f"missing cols: {missing_cols} known cols: {known_cols}")
print("Rows with missing values in known columns:")
print(X_test[X_test[known_cols].isnull().any(axis=1)])
# X_test[known_cols] = X_test[known_cols].fillna(X_train[known_cols].median())
predict_df["predicted_home_score"] = home_model.predict(X_test)
predict_df["predicted_away_score"] = away_model.predict(X_test)

# Convert team numbers back to names
for i, row in predict_df.iterrows():
    predict_df.at[i, "home_team"] = team_num_map[int(row["home_team"])]
    predict_df.at[i, "away_team"] = team_num_map[int(row["away_team"])]
predict_df["score_diff"] = abs(predict_df["predicted_home_score"] - predict_df["predicted_away_score"])
cols = [col for col in predict_df.columns if col not in ['predicted_home_score', 'home_team', 'predicted_away_score', 'away_team', 'score_diff']] + ['predicted_home_score', 'home_team', 'predicted_away_score', 'away_team', 'score_diff']
predict_df = predict_df[cols]

predict_df.to_csv("predicted_scores.csv", index=False)
