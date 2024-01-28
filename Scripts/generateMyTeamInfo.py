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



# Make request call to get the team data for each league joined and save the outputs in different excel files
## A function that takes in a sum of points acquired in the last 5 matches for each player and returns a recommendation
def recommendation_func(listt):
    if sum(listt) <= 0:
        return "Does not score"
    elif 0 < sum(listt) < 11:
        return "Not recommended"
    elif 10 < sum(listt) < 21:
        return "it can be better"
    elif 20 < sum(listt) < 31:
        return "Good moment"
    elif 30 < sum(listt) < 41:
        return "Excellent way"
    elif 40 < sum(listt):
        return "On fire"
    
## Make request call to get the team data for each league joined
for key, value in leagues_info.items():
    response = requests.get('https://api.laligafantasymarca.com/api/v3/leagues/'+str(value[0])+'/teams/'+str(value[1]), headers=headers)
    r = response.text
    team_page_info = json.loads(r)
    player_dict = team_page_info['players']
    players_data_dict = {
                        'Player id': [],
                        'Name': [], 
                        'Market Value': [], 
                        'Release Clause': [], 
                        'end_release_clause': [], 
                        'Condition': [], 
                        'Avg Pts': [], 
                        'Latest Form': [],
                        'Recommendation': []
                        }
    for element in range(len(player_dict)):
        players_data_dict['Player id'].append(player_dict[element]['playerMaster']['id'])
        players_data_dict['Name'].append(player_dict[element]['playerMaster']['nickname'])
        players_data_dict['Condition'].append(player_dict[element]['playerMaster']['playerStatus'])
        players_data_dict['Avg Pts'].append(round(player_dict[element]['playerMaster']['averagePoints'], 2))
        latest_form_array = []
        for j in player_dict[element]['playerMaster']['lastStats']:
            latest_form_array.append(j['totalPoints'])
        players_data_dict['Latest Form'].append(latest_form_array)
        players_data_dict['Recommendation'].append(recommendation_func(latest_form_array))
        players_data_dict['Market Value'].append(player_dict[element]['playerMaster']['marketValue'])
        players_data_dict['Release Clause'].append(player_dict[element]['buyoutClause'])
        players_data_dict['end_release_clause'].append(player_dict[element]['buyoutClauseLockedEndTime'])
    players_dataframe = pd.DataFrame(players_data_dict)
    players_dataframe['end_release_clause'] = players_dataframe['end_release_clause'].apply(lambda x: ":".join(x.split(":", 2)[:2])).str.replace('T', ' ')
    players_dataframe['end_release_clause'] = pd.to_datetime(players_dataframe['end_release_clause'], format="%Y-%m-%d %H:%M")
    players_dataframe['Open for RC'] = players_dataframe.end_release_clause.apply(lambda x: True if '-' in str(x - pd.Timestamp.now()) else False)
    players_dataframe = players_dataframe[['Player id', 'Name', 'Condition', 'Avg Pts', 'Latest Form', 'Recommendation', 'Market Value', 'Release Clause', 'Open for RC']]

    ## Make Request Call for each player to get their market value difference in last 5 days
    value_diff_list = []
    for id in players_dataframe['Player id']:
        response = requests.get("https://api.laligafantasymarca.com/api/v3/player/" + str(id) + "/market-value", headers=headers)
        r = response.text
        team_page_info = json.loads(r)
        value_diff_list.append(team_page_info[-5:][-1]['marketValue'] - team_page_info[-5:][0]['marketValue'])
    players_dataframe['value_difference_since_5_days'] = value_diff_list
    players_dataframe = players_dataframe.sort_values(by='value_difference_since_5_days', ascending=False)

    ## Save excel file
    path = str(user).split('@')[0] + '\\datasets\\'
    if not os.path.exists(path):
        os.makedirs(path)
    players_dataframe.to_excel(path+'TeamInfo_'+str(key).replace(' ', '_')+'.xlsx', index=False)