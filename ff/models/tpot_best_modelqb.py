import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt

# NOTE: Make sure that the outcome column is labeled 'target' in the data file
def qbmod(df_list):
    train_df = df_list[0][0]
    test_df = df_list[0][1]
    weeks = test_df['week']
    X_train = train_df.drop(columns=['player_name', 'points']).values.astype('float32')
    y_train = train_df['points'].values.astype('float32')
    # Process the testing data
    test_columns = test_df.drop(columns=['player_name', 'points']).columns
    available_columns = test_columns.intersection(train_df.columns)
    feature_names = train_df[available_columns].columns
    print(train_df.isnull().values.any())
    print(test_df.isnull().values.any())
    X_train = train_df[available_columns].values.astype('float32')
    X_test = test_df[available_columns].values.astype('float32')
    y_test = test_df['points'].values.astype('float32')
    player_ids = test_df['player_name']

    # Average CV score on the training set was: -5.550180632140729
    exported_pipeline = RandomForestRegressor(bootstrap=True, max_features=0.7500000000000001, min_samples_leaf=2, min_samples_split=4, n_estimators=100)
    # Fix random state in exported estimator
    if hasattr(exported_pipeline, 'random_state'):
        setattr(exported_pipeline, 'random_state', 1)
    exported_pipeline.fit(X_train, y_train)
    # Make predictions
    results = exported_pipeline.predict(X_test)
    
    feature_importances = exported_pipeline.feature_importances_
    # Plot feature importance
    # Set a threshold to filter out small feature importances
    threshold = 0.01
    filtered_feature_importances = feature_importances[feature_importances > threshold]
    filtered_feature_names = feature_names[feature_importances > threshold]

    # Plot filtered feature importance
    plt.figure(figsize=(25, 6))
    plt.bar(filtered_feature_names, filtered_feature_importances, color='red')
    plt.xticks(rotation=45, ha="right")
    plt.xlabel('Features')
    plt.ylabel('Relative Importance')
    plt.title('Filtered Feature Importance')
    plt.tight_layout()
    plt.show()
    
    # General way to determine average differences
    print("Average difference:", np.mean(np.abs(results - y_test)))
    return pd.DataFrame({'player_name': player_ids, 'week': weeks, 'predicted_points': results, 'actual_points': y_test})

    
