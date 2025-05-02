import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import VarianceThreshold
from sklearn.pipeline import make_pipeline
from tpot.export_utils import set_param_recursive
import matplotlib.pyplot as plt

# NOTE: Make sure that the outcome column is labeled 'target' in the data file
def wrmod(df_list):
    train_df = df_list[2][0]
    test_df = df_list[2][1]
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

    # Average CV score on the training set was: -4.7511662699323045
    exported_pipeline = make_pipeline(
        VarianceThreshold(threshold=0.2),
        RandomForestRegressor(bootstrap=True, max_features=0.15000000000000002, min_samples_leaf=9, min_samples_split=6, n_estimators=100)
    )
    # Fix random state for all the steps in exported pipeline
    set_param_recursive(exported_pipeline.steps, 'random_state', 1)
    
    exported_pipeline.fit(X_train, y_train)
    # Make predictions
    results = exported_pipeline.predict(X_test)
    
    feature_importances = exported_pipeline.named_steps['randomforestregressor'].feature_importances_
    # Plot feature importance
    # Set a threshold to filter out small feature importances
    threshold = 0.01
    selected_features = exported_pipeline.named_steps['variancethreshold'].get_support()
    filtered_feature_names = feature_names[selected_features][feature_importances > threshold]
    filtered_feature_importances = feature_importances[feature_importances > threshold]

    # Plot filtered feature importance
    plt.figure(figsize=(25, 6))
    plt.bar(filtered_feature_names, filtered_feature_importances, color='red')
    plt.xticks(rotation=45, ha="right")
    plt.xlabel('Features')
    plt.ylabel('Relative Importance')
    plt.title('Filtered Feature Importance')
    plt.tight_layout()
    plt.show()
    
    print("Average difference:", np.mean(np.abs(results - y_test)))
    return pd.DataFrame({'player_name': player_ids, 'week': weeks, 'predicted_points': results, 'actual_points': y_test})