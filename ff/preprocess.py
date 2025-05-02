from sklearn.preprocessing import StandardScaler, OneHotEncoder
import pandas as pd

def preprocess_dataframe(df):
    # Columns to manually exclude from scaling (categorical or non-relevant columns)
    exclude = ['player_name', 'week', 'stadium', 'referee', 'gameday', 'weekday', 'gametime']

    # Categorical columns (currently numeric but should be treated as categorical)
    categorical_cols = ['team', 'home_team', 'opponent_team', 'away_team', 'bye_week',
                        'Injury', 'Wed', 'Thu', 'Fri', 'Game Status', 'div_game', 'Remark', 
                        'depth_team']
    
    # Separate exclude columns
    exclude_cols = df[exclude]
    # Drop exclude columns before encoding
    df = df.drop(columns=exclude)

    # Apply one-hot encoding to categorical columns
    df_encoded = pd.get_dummies(df, columns=categorical_cols)

    # Separate numeric columns and scale them (excluding the 'points' column)
    numeric_cols = df_encoded.select_dtypes(include=['float64', 'int64']).columns
    numeric_cols = [col for col in numeric_cols if col != 'points']

    # Scale numeric columns
    scaler = StandardScaler()
    df_encoded[numeric_cols] = scaler.fit_transform(df_encoded[numeric_cols])
    df_final = pd.concat([df_encoded, exclude_cols], axis=1)

    return df_final