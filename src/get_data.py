"""
Get the data, spotrac.com/nhl, csv files from naturalstattrick.com and nhl.com/stats

Author: Kevin Kang
"""

import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# Get today's date and format it
today = datetime.today().strftime('%Y-%m-%d')

# List of NHL teams by their URL slug
teams = {
    "anaheim-ducks": "Anaheim Ducks",
    "boston-bruins": "Boston Bruins",
    "buffalo-sabres": "Buffalo Sabres",
    "calgary-flames": "Calgary Flames",
    "carolina-hurricanes": "Carolina Hurricanes",
    "chicago-blackhawks": "Chicago Blackhawks",
    "colorado-avalanche": "Colorado Avalanche",
    "columbus-blue-jackets": "Columbus Blue Jackets",
    "dallas-stars": "Dallas Stars",
    "detroit-red-wings": "Detroit Red Wings",
    "edmonton-oilers": "Edmonton Oilers",
    "florida-panthers": "Florida Panthers",
    "los-angeles-kings": "Los Angeles Kings",
    "minnesota-wild": "Minnesota Wild",
    "montreal-canadiens": "Montreal Canadiens",
    "nashville-predators": "Nashville Predators",
    "new-jersey-devils": "New Jersey Devils",
    "new-york-islanders": "New York Islanders",
    "new-york-rangers": "New York Rangers",
    "ottawa-senators": "Ottawa Senators",
    "philadelphia-flyers": "Philadelphia Flyers",
    "pittsburgh-penguins": "Pittsburgh Penguins",
    "san-jose-sharks": "San Jose Sharks",
    "seattle-kraken": "Seattle Kraken",
    "st-louis-blues": "St. Louis Blues",
    "tampa-bay-lightning": "Tampa Bay Lightning",
    "toronto-maple-leafs": "Toronto Maple Leafs",
    "utah-hockey-club": "Utah Hockey Club",
    "vancouver-canucks": "Vancouver Canucks",
    "vegas-golden-knights": "Vegas Golden Knights",
    "washington-capitals": "Washington Capitals",
    "winnipeg-jets": "Winnipeg Jets"
}
base_url = "https://www.spotrac.com/nhl/{}/cap/"

# Identify the scraper and wait between requests to be polite to the server
headers = {'User-Agent': 'Mozilla/5.0 (compatible; nhlsalarycap-scraper/1.0)'}
request_delay = 1  # seconds

# Step 1: Scrape the Team Salary Page
def scrape_team_page(url):
    response = requests.get(url, headers=headers)
    time.sleep(request_delay)
    soup = BeautifulSoup(response.content, 'html.parser')

    player_data = []
    table = soup.find('table', {'class': 'table-internal-sort'})
    rows = table.find_all('tr')

    for row in rows[1:]:  # Skip header row
        try:
            player_name = row.find('a').text
            player_url = row.find('a')['href']
            full_url = player_url
            cols = row.find_all('td')
            cap_hit = cols[2].text.strip()
            cap_hit_pct = cols[4].text.strip()
            base_salary = cols[5].text.strip()
            signing_bonus = cols[6].text.strip()

            player_data.append({
                'name': player_name, 
                'url': full_url,
                'cap_hit': cap_hit,
                'cap_hit_pct': cap_hit_pct,
                'base_salary': base_salary,
                'signing_bonus': signing_bonus
            })
        except Exception as e:
            print(f"Error fetching player info: {e}")
    
    return player_data

# Step 2: Scrape Each Player's Profile for Contract Details and Additional Information
def scrape_player_profile(player):
    response = requests.get(player['url'], headers=headers)
    time.sleep(request_delay)
    soup = BeautifulSoup(response.content, 'html.parser')

    try:
        contract_term = soup.find(string='Contract Terms:').find_next('div').text
        contract_years_signed = int(contract_term.split(" ")[0])

        salary_signed = contract_term.split("/")[1].strip()
        
        free_agent_info = soup.find(string='Free Agent:').find_next('div').text.split("/")
        free_agent_year = int(free_agent_info[0].strip())
        free_agent_status = free_agent_info[1].strip()

        current_year = 2024
        contract_start_year = free_agent_year - contract_years_signed
        contract_years_left = free_agent_year - current_year

        player_age_info = None
        birthday = None
        experience = None
        country = None
        college = None
        drafted = None

        try:
            player_age_info = soup.find(string='Age:').find_next('span').text.strip()
            birthday = player_age_info.split('(')[1].replace(')', '')
        except (AttributeError, IndexError):
            pass

        try:
            experience = soup.find(string='Exp:').find_next('span').text.strip()
        except (AttributeError, IndexError):
            pass

        try:
            country = soup.find(string='Country:').find_next('span').text.strip()
        except (AttributeError, IndexError):
            pass

        try:
            college = soup.find(string='College:').find_next('span').text.strip()
        except (AttributeError, IndexError):
            pass

        try:
            drafted = soup.find(string='Drafted:').find_next('span').text.strip()
        except (AttributeError, IndexError):
            pass

        player['contract_start_year'] = contract_start_year
        player['contract_years_signed'] = contract_years_signed
        player['contract_years_left'] = contract_years_left
        player['free_agent_year'] = free_agent_year
        player['salary_signed'] = salary_signed
        player['status_after_contract'] = free_agent_status
        player['age'] = player_age_info.split('(')[0].strip() if player_age_info else None
        player['birthday'] = birthday
        player['experience'] = experience
        player['country'] = country
        player['college'] = college
        player['drafted'] = drafted

        return player

    except Exception as e:
        print(f"Error scraping contract data for {player['name']}: {e}")
        return None

def main():
    combined_player_data = []  # To hold data for all players

    for team_slug, team_name in teams.items():
        team_url = base_url.format(team_slug)
        print(f"Scraping data for team: {team_name}")
        
        player_data = scrape_team_page(team_url)

        for player in player_data:
            print(f"  Scraping data for {player['name']}...")
            contract_data = scrape_player_profile(player)
            if contract_data:
                contract_data['team_name'] = team_name
                combined_player_data.append(contract_data)

    combined_df = pd.DataFrame(combined_player_data)
    combined_df.replace({r'\$': '', ',': '', '%': ''}, regex=True, inplace=True)

    output_dir = "../data/raw"  
    os.makedirs(output_dir, exist_ok=True)

    # Save the combined data to a CSV file in the specified directory
    combined_file_name = os.path.join(output_dir, f'all_player_contract_data_{today}.csv')
    combined_df.to_csv(combined_file_name, index=False)

    print(f"Combined data saved as {combined_file_name}")

if __name__ == '__main__':
    main()


