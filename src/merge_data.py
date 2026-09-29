"""
Merge cps data with salary data

Author: Kevin Kang
"""

import glob
import os
import sys
import pandas as pd
from name_map import name_corrections, normalize_name, print_fuzzy_candidates

# Load salary data: use the filename passed as an argument, otherwise the most recent contract file in data/raw
if len(sys.argv) > 1:
    salary_file_path = sys.argv[1]
else:
    salary_file_path = max(glob.glob('../data/raw/all_player_contract_data_*.csv'), key=os.path.basename)
print(f"Using salary file: {salary_file_path}")
salary_df = pd.read_csv(salary_file_path)

# Load combined CPS data for both skaters and goalies
combined_cps_df = pd.read_csv('../data/processed/cps/combined_player_goalie_cps.csv')

# Rename the columns to match (standardize to 'player' for both)
combined_cps_df.rename(columns={'Player': 'player'}, inplace=True)
salary_df.rename(columns={'name': 'player'}, inplace=True)

# Replace names in the 'player' column of both DataFrames
combined_cps_df['player'] = combined_cps_df['player'].replace(name_corrections)
salary_df['player'] = salary_df['player'].replace(name_corrections)

# Remove duplicate rows before merging (same name AND same team, so two different players with the same name are kept)
combined_cps_df = combined_cps_df.drop_duplicates(subset=['player', 'Team'])
salary_df = salary_df.drop_duplicates(subset=['player', 'team_name'])

# Map spotrac team names to the stats team abbreviations (Utah players were Arizona in 23-24)
team_abbreviations = {
    'Anaheim Ducks': 'ANA', 'Boston Bruins': 'BOS', 'Buffalo Sabres': 'BUF', 'Calgary Flames': 'CGY',
    'Carolina Hurricanes': 'CAR', 'Chicago Blackhawks': 'CHI', 'Colorado Avalanche': 'COL',
    'Columbus Blue Jackets': 'CBJ', 'Dallas Stars': 'DAL', 'Detroit Red Wings': 'DET', 'Edmonton Oilers': 'EDM',
    'Florida Panthers': 'FLA', 'Los Angeles Kings': 'L.A', 'Minnesota Wild': 'MIN', 'Montreal Canadiens': 'MTL',
    'Nashville Predators': 'NSH', 'New Jersey Devils': 'N.J', 'New York Islanders': 'NYI', 'New York Rangers': 'NYR',
    'Ottawa Senators': 'OTT', 'Philadelphia Flyers': 'PHI', 'Pittsburgh Penguins': 'PIT', 'San Jose Sharks': 'S.J',
    'Seattle Kraken': 'SEA', 'St. Louis Blues': 'STL', 'Tampa Bay Lightning': 'T.B', 'Toronto Maple Leafs': 'TOR',
    'Utah Hockey Club': 'ARI', 'Vancouver Canucks': 'VAN', 'Vegas Golden Knights': 'VGK', 'Washington Capitals': 'WSH',
    'Winnipeg Jets': 'WPG'
}
salary_df['team_abbr'] = salary_df['team_name'].map(team_abbreviations)

# Match on a normalized name key (no accents, lowercase, common first-name variants) but keep the original display names
combined_cps_df['name_key'] = combined_cps_df['player'].map(normalize_name)
salary_df['name_key'] = salary_df['player'].map(normalize_name)

# Step 1: match on player + team (the salary team appears in the player's 23-24 team list, e.g. 'ANA, COL')
candidates = pd.merge(combined_cps_df.reset_index(), salary_df.reset_index(), on='name_key', suffixes=('_cps', '_salary'))
same_team = candidates.apply(lambda row: row['team_abbr'] in row['Team'].split(', '), axis=1)
team_matches = candidates[same_team]

# Step 2: players who changed teams - match the remaining rows on name, but only when the name is unique on both sides
remaining_cps = combined_cps_df.drop(team_matches['index_cps'])
remaining_salary = salary_df.drop(team_matches['index_salary'])
remaining_cps = remaining_cps.drop_duplicates(subset='name_key', keep=False)
remaining_salary = remaining_salary.drop_duplicates(subset='name_key', keep=False)
name_matches = pd.merge(remaining_cps.reset_index(), remaining_salary.reset_index(), on='name_key', suffixes=('_cps', '_salary'))

# Combine both sets of matches
merged_df = pd.concat([team_matches, name_matches], ignore_index=True)

# Show matches where the two sources spell the name differently, so they can be checked
spelling_differences = merged_df[merged_df['player_cps'] != merged_df['player_salary']]
print(f"Matched with a different spelling: {len(spelling_differences)}")
for _, row in spelling_differences.iterrows():
    print(f"  {row['player_cps']} ({row['Team']}) = {row['player_salary']} ({row['team_name']})")

# Keep the stats spelling as the display name
merged_df = merged_df.rename(columns={'player_cps': 'player'})
merged_df = merged_df.drop(columns=['index_cps', 'index_salary', 'team_abbr', 'name_key', 'player_salary'])

# Print match counts
print(f"Matched on player + team: {len(team_matches)}")
print(f"Matched on unique name (changed teams): {len(name_matches)}")
print(f"Total matched players: {len(merged_df)}")
print(f"Unmatched CPS players (no salary data): {len(combined_cps_df) - len(merged_df)}")
print(f"Unmatched salary players (no CPS data): {len(salary_df) - len(merged_df)}")

# Suggest possible matches for the unmatched contracts (review these and add approved ones to name_map.py)
unmatched_salary = salary_df.drop(team_matches['index_salary']).drop(name_matches['index_salary'])
unmatched_cps = combined_cps_df.drop(team_matches['index_cps']).drop(name_matches['index_cps'])
print("Fuzzy match candidates for unmatched contracts (NOT applied):")
print_fuzzy_candidates(list(zip(unmatched_salary['player'], unmatched_salary['team_name'])),
                       list(zip(unmatched_cps['player'], unmatched_cps['Team'])))

# Display the first few rows of the merged dataset
print(merged_df.head())

# Save the merged DataFrame to a CSV file
output_file_path = '../data/processed/merged_player_goalie_cps_and_salaries.csv'
merged_df.to_csv(output_file_path, index=False)

