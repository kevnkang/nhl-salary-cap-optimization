"""
Clean the data, making sure all the names and columns are uniform

Author: Kevin Kang
"""

import pandas as pd
from name_map import name_corrections, normalize_name, print_fuzzy_candidates

# --- Player Stats with Plus/Minus ---
# Load the player stats CSV file
player_stats_file_path = '../data/raw/player_stats_23_24.csv'  
df_player_stats = pd.read_csv(player_stats_file_path)

# Load the plus/minus values from the second CSV file
plus_minus_file_path = '../data/raw/players_plus_minus.csv'  
df_plus_minus = pd.read_csv(plus_minus_file_path)

# Rename specific player names in the plus-minus file using the shared name map
df_plus_minus['Player'] = df_plus_minus['Player'].replace(name_corrections)

# Ensure the column names are consistent. Rename the +/- column to 'plus_minus' to avoid issues with special characters.
df_plus_minus = df_plus_minus.rename(columns={'+/-': 'plus_minus'})

# Map nhl.com team codes to the naturalstattrick.com codes used in the player stats file
nhl_to_nst_teams = {'TBL': 'T.B', 'NJD': 'N.J', 'LAK': 'L.A', 'SJS': 'S.J'}

# Turn a team string (e.g. 'BOS, CBJ' or 'CBJ,BOS') into a set of naturalstattrick.com team codes
def team_set(teams):
    return {nhl_to_nst_teams.get(team.strip(), team.strip()) for team in str(teams).split(',')}

# Match on a normalized name key (no accents, lowercase, common first-name variants) but keep the original display names
df_player_stats['name_key'] = df_player_stats['Player'].map(normalize_name)
df_plus_minus['name_key'] = df_plus_minus['Player'].map(normalize_name)

# Step 1: match on player + team (at least one team in common), so two players with the same name each get their own +/-
candidates = pd.merge(df_player_stats.reset_index(), df_plus_minus[['name_key', 'Team', 'plus_minus']].reset_index(),
                      on='name_key', suffixes=('', '_pm'))
same_team = candidates.apply(lambda row: bool(team_set(row['Team']) & team_set(row['Team_pm'])), axis=1)
team_matches = candidates[same_team]

# Step 2: match the remaining rows on name, but only when the name is unique on both sides
remaining_stats = df_player_stats.drop(team_matches['index'])
remaining_plus_minus = df_plus_minus.drop(team_matches['index_pm'])
remaining_stats = remaining_stats[~remaining_stats['name_key'].duplicated(keep=False)]
remaining_plus_minus = remaining_plus_minus[~remaining_plus_minus['name_key'].duplicated(keep=False)]
name_matches = pd.merge(remaining_stats.reset_index(), remaining_plus_minus[['name_key', 'plus_minus']].reset_index(),
                        on='name_key', suffixes=('', '_pm'))

# Add the matched plus-minus values to the player stats (unmatched players keep a missing value)
matches = pd.concat([team_matches, name_matches]).drop_duplicates(subset='index')
merged_player_df = df_player_stats.drop(columns='name_key')
merged_player_df['plus_minus'] = matches.set_index('index')['plus_minus']

# Print match counts
print(f"Plus/minus matched on player + team: {len(team_matches)}")
print(f"Plus/minus matched on unique name: {len(name_matches)}")
print(f"Unmatched player stats rows (no plus/minus): {len(df_player_stats) - len(matches)}")
print(f"Unmatched plus/minus rows: {len(df_plus_minus) - len(matches)}")

# Suggest possible matches for unmatched players (review these and add approved ones to name_map.py)
unmatched_stats = df_player_stats.drop(matches['index'])
unmatched_plus_minus = df_plus_minus.drop(team_matches['index_pm']).drop(name_matches['index_pm'])
if len(unmatched_stats) > 0:
    print("Fuzzy match candidates for unmatched player stats (NOT applied):")
    print_fuzzy_candidates(list(zip(unmatched_stats['Player'], unmatched_stats['Team'])),
                           list(zip(unmatched_plus_minus['Player'], unmatched_plus_minus['Team'])))

# Display the first few rows of the merged dataframe to verify
print("Player Stats with Plus/Minus:")
print(merged_player_df.head())

merged_player_file_path = '../data/cleaned/merged_player_stats_with_plus_minus.csv'
merged_player_df.to_csv(merged_player_file_path, index=False)

# --- Goalie Stats with Wins ---
# Load the goalie stats CSV file
goalie_stats_file_path = '../data/raw/goalie_stats_23_24.csv'  
df_goalie_stats = pd.read_csv(goalie_stats_file_path)

# Load the wins data from a separate CSV file (assuming it contains player names and wins)
wins_file_path = '../data/raw/goalie_wins_losses.csv'  
df_wins = pd.read_csv(wins_file_path)

# Ensure the column names are consistent. Rename the 'Wins' column to 'wins'
df_wins = df_wins.rename(columns={'W': 'wins'})

# Merge the two datasets based on the 'Player' column to include the wins values
merged_goalie_df = pd.merge(df_goalie_stats, df_wins[['Player', 'wins']], on='Player', how='left')

# Calculate win percentage and handle division by zero if a goalie has no games played
merged_goalie_df['win_percentage'] = (merged_goalie_df['wins'] / merged_goalie_df['GP'].replace(0, pd.NA)) * 100

# Display the first few rows of the merged dataframe to verify
print("\nGoalie Stats with Wins:")
print(merged_goalie_df.head())

merged_goalie_file_path = '../data/cleaned/merged_goalie_stats_with_wins.csv'
merged_goalie_df.to_csv(merged_goalie_file_path, index=False)

