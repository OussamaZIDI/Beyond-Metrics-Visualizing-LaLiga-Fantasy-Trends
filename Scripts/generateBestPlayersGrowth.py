# Libs
import json
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import os
import sys



# Make API calls to get the necessary informations to scarp data (league_id, league_name, team_id)
## Read Login Details
with open('Scripts\login_info.txt') as f:
    read_file = f.read()
    user = read_file.strip().split('\n')[0].split('Email:')[1].strip()
    password = read_file.strip().split('\n')[1].split('Password:')[1].strip()

## Submit the POST request through the session to get the identification code
s = requests.Session()
policy = "B2C_1A_ResourceOwnerv2"
payload = {
    "username": user,
    "password": password,
    "policy": policy
}
url = "https://api-fantasy.llt-services.com/login/v3/email/auth?x-lang=en"
p = s.post(url, data=payload)
response = p.text
json_response = json.loads(response)
id_code = json_response['code']

## Submit the POST request through the session to get the token using the identificaiton code
url = 'https://api-fantasy.llt-services.com/login/v3/email/token?x-lang=en'
payload = {
    "code": id_code,
    "policy": policy
}
p = s.post(url, data=payload)
r = p.text
json_r = json.loads(r)
authorization = json_r['access_token']
authorization = 'Bearer ' + authorization

## Make request call to get data about the leagues we are participating in
headers = {'authorization': authorization}
response = requests.get("https://api.laligafantasymarca.com/api/v4/leagues?x-lang=en", headers=headers)
r = response.text
leagues_json = json.loads(r)

### get league name
league_names = []
for i in range(len(leagues_json)):
    league_names.append(leagues_json[i]['name'])

### get league id
league_ids = []
for i in range(len(leagues_json)):
    league_ids.append(leagues_json[i]['id'])

### get team id
team_ids = []
for i in range(len(leagues_json)):
    team_ids.append(leagues_json[i]['team']['id'])

### Creating League dictionary
zipped_list = list(zip(league_ids, team_ids))
leagues_info = dict(zip(league_names, zipped_list))



# Make necessary requests to get Top league players with Most Growing Value since 5 days and save results into an excel file
## Make Request Call to get a dataframe of all players [id, name, market_value]
response = requests.get('https://api.laligafantasymarca.com/api/v3/players/', headers=headers)
r = response.text
team_page_info = json.loads(r)
players_dict = {
                'player_id': [],
                'player_name': []
                }
player_id = []
player_name = []
for i in range(len(team_page_info)):
    players_dict['player_id'].append(team_page_info[i]['id'])
    players_dict['player_name'].append(team_page_info[i]['nickname'])
players_df = pd.DataFrame(players_dict)

## Make Request Call for each player to get their market value difference in last 5 days
value_diff_list = []
for id in players_df.player_id:
    response = requests.get("https://api.laligafantasymarca.com/api/v3/player/" + str(id) + "/market-value", headers=headers)
    r = response.text
    team_page_info = json.loads(r)
    value_diff_list.append(team_page_info[-5:][-1]['marketValue'] - team_page_info[-5:][0]['marketValue'])
players_df['value_difference_since_5_days'] = value_diff_list
players_df = players_df.sort_values(by='value_difference_since_5_days', ascending=False)

## Save results into excel file
path = str(user).split('@')[0] + '\\datasets\\'    
if not os.path.exists(path):
        os.makedirs(path)
players_df.head(20).to_excel(path+'Top_20_Growing_players.xlsx', index=False)