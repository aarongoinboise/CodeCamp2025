import pandas as pd
from xgboost import XGBRegressor, plot_importance
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer

def dstmod(df_list):
    """
    Chosen model for rbs. From TPOT.
    """
    train_df = df_list[5][0]
    test_df = df_list[5][1]
    
    weeks = test_df['week']
    
    feature_names = train_df.drop(columns=['player', 'points']).columns
    X_train = train_df.drop(columns=['player', 'points']).values.astype('float32')
    y_train = train_df['points'].values.astype('float32')
    
    # Process the testing data
    test_columns = test_df.drop(columns=['player', 'points']).columns
    available_columns = test_columns.intersection(train_df.columns)    
    imputer = SimpleImputer(strategy='mean')  # Can change to 'median' if preferred
    X_train = imputer.fit_transform(train_df[available_columns].values.astype('float32'))
    X_test = imputer.transform(test_df[available_columns].values.astype('float32'))
    y_test = test_df['points'].values.astype('float32')
    player_ids = test_df['player'].values 

    # Average CV score on the training set was: -2.5009371519088743
    exported_pipeline = XGBRegressor(learning_rate=0.1, max_depth=5, min_child_weight=4, n_estimators=100, n_jobs=1, objective="reg:squarederror", subsample=0.8, verbosity=0)
    # Fix random state in exported estimator
    if hasattr(exported_pipeline, 'random_state'):
        setattr(exported_pipeline, 'random_state', 1)

    exported_pipeline.fit(X_train, y_train)
    results = exported_pipeline.predict(X_test)
    
    feature_importances = exported_pipeline.feature_importances_
    
    plt.figure(figsize=(25, 6))
    plt.bar(feature_names, feature_importances, color='purple')
    plt.xticks(rotation=45, ha="right")
    plt.xlabel('Features')
    plt.ylabel('Relative Importance')
    plt.title('XGBRegressor Feature Importance')
    plt.tight_layout()
    plt.show()
    
    return pd.DataFrame({'player': player_ids, 'week': weeks, 'predicted_points': results, 'actual_points': y_test})
