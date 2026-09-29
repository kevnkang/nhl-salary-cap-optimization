"""
Integrating data to form a CPS (custom performance score)

note: CPS is calculated using different weights assigned to specific metrics that are relevant for each position (can be further customized)

Author: Kevin Kang
"""

import pandas as pd
from sklearn.preprocessing import MinMaxScaler

# --- Skater CPS Calculation ---

# Load the skater (player) stats dataset
df_player_stats = pd.read_csv('../data/cleaned/merged_player_stats_with_plus_minus.csv')

# Function to handle dual positions, selecting the second one if it exists
def select_second_position(position):
    if ',' in position:
        return position.split(',')[1].strip()  # Select the second position
    return position  # If no comma, return the original position

# Apply the function to the 'Position' column
df_player_stats['Position'] = df_player_stats['Position'].apply(select_second_position)

# Replace any '-' with 0
df_player_stats.replace('-', 0, inplace=True)

# Normalize positive-only columns for skaters
scaler = MinMaxScaler()
df_player_stats[['Goals', 'TOI', 'Shots', 'Total Assists', 'Shots Blocked', 'Hits', 'Takeaways', 'Faceoffs %', 'iCF', 'ixG']] = scaler.fit_transform(
    df_player_stats[['Goals', 'TOI', 'Shots', 'Total Assists', 'Shots Blocked', 'Hits', 'Takeaways', 'Faceoffs %', 'iCF', 'ixG']]
)

# Shift plus_minus column to positive before scaling, add abs(min value) + 1
plus_minus_shifted = df_player_stats['plus_minus'] + abs(df_player_stats['plus_minus'].min()) + 1
df_player_stats['plus_minus_normalized'] = scaler.fit_transform(plus_minus_shifted.values.reshape(-1, 1))

# Custom Performance Score (CPS) Calculation based on position
# note: the weights for every position (C, L/R, D, G) sum to 1
def calculate_cps(row):
    # Centers (C)
    if row['Position'] == 'C':
        return (0.25 * row['Goals'] + 0.2 * row['TOI'] + 0.15 * row['Total Assists'] + 
                0.1 * row['ixG'] + 0.1 * row['plus_minus_normalized'] + 
                0.1 * row['Takeaways'] + 0.1 * row['Faceoffs %'])
    
    # Wingers (L & R)
    elif row['Position'] in ['L', 'R']:
        return (0.3 * row['Goals'] + 0.25 * row['TOI'] + 0.2 * row['Total Assists'] + 
                0.1 * row['iCF'] + 0.1 * row['ixG'] + 0.05 * row['plus_minus_normalized'])
    
    # Defensemen (D)
    elif row['Position'] == 'D':
        return (0.25 * row['TOI'] + 0.2 * row['Shots Blocked'] + 0.15 * row['Hits'] + 
                0.1 * row['iCF'] + 0.2 * row['plus_minus_normalized'] + 0.1 * row['Takeaways'])
    
    # If no match, return None
    return None

# Apply CPS calculation for skaters
df_player_stats['cps'] = df_player_stats.apply(calculate_cps, axis=1)

# Save skater CPS to CSV
df_player_stats[['Player', 'Team', 'Position', 'GP', 'cps']].to_csv('../data/processed/cps/player_cps.csv', index=False)

# --- Goalie CPS Calculation ---

# Load the goalie stats dataset
df_goalie_stats = pd.read_csv('../data/cleaned/merged_goalie_stats_with_wins.csv')

# Replace any missing or non-numeric values (like '-') with 0
df_goalie_stats.replace('-', 0, inplace=True)

# Set threshold for games played to scale win percentage
games_played_threshold = 10

# Scale win percentage using RAW games played (before any normalization) if the goalie has played fewer than the threshold number of games
gp_raw = df_goalie_stats['GP'].copy()
df_goalie_stats['scaled_win_percentage'] = df_goalie_stats['win_percentage'].where(
    gp_raw >= games_played_threshold, df_goalie_stats['win_percentage'] * (gp_raw / games_played_threshold)
)

# Metrics relevant for goalie CPS
metrics = ['SV%', 'GAA', 'GSAA', 'HDSV%', 'xG Against', 'Rebound Attempts Against', 'win_percentage', 'GP', 'scaled_win_percentage']

# Normalize the relevant goalie stats columns (including the scaled win percentage)
df_goalie_stats[metrics] = scaler.fit_transform(df_goalie_stats[metrics])

# Invert 'GAA', 'xG Against', and 'Rebound Attempts Against' since lower values are better
df_goalie_stats['GAA'] = 1 - df_goalie_stats['GAA']
df_goalie_stats['xG Against'] = 1 - df_goalie_stats['xG Against']
df_goalie_stats['Rebound Attempts Against'] = 1 - df_goalie_stats['Rebound Attempts Against']

# Calculate CPS for goalies using weighted formula
df_goalie_stats['cps_goalie'] = (0.3 * df_goalie_stats['SV%'] +
                                 0.2 * df_goalie_stats['GAA'] +
                                 0.15 * df_goalie_stats['GSAA'] +
                                 0.15 * df_goalie_stats['HDSV%'] +
                                 0.1 * df_goalie_stats['xG Against'] +
                                 0.05 * df_goalie_stats['Rebound Attempts Against'] +
                                 0.05 * df_goalie_stats['scaled_win_percentage'])

# Add Position for goalies and restore the raw games played for the output
df_goalie_stats['Position'] = 'G'
df_goalie_stats['GP'] = gp_raw

# Save goalie CPS to CSV
df_goalie_stats[['Player', 'Team', 'Position', 'GP', 'cps_goalie']].to_csv('../data/processed/cps/goalie_cps.csv', index=False)

# --- Combine Skater and Goalie CPS Results ---

# Load the skater CPS and goalie CPS datasets
df_skaters_cps = pd.read_csv('../data/processed/cps/player_cps.csv')
df_goalies_cps = pd.read_csv('../data/processed/cps/goalie_cps.csv')

# Rename goalie CPS column for consistency
df_goalies_cps.rename(columns={'cps_goalie': 'cps'}, inplace=True)

# Combine skaters and goalies into one dataset
df_combined_cps = pd.concat([df_skaters_cps, df_goalies_cps], ignore_index=True)

# Save the combined CPS dataset to a CSV file
df_combined_cps.to_csv('../data/processed/cps/combined_player_goalie_cps.csv', index=False)

# Print the first few rows of the combined dataset
print(df_combined_cps.head())
