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



# Looping into leagues dicionary to make calls and save results into different excel files
for k, v in leagues_info.items():
    ## Make request call to get a list of market dataframe about the leagues we are participating in
    response = requests.get('https://api.laligafantasymarca.com/api/v3/league/'+str(v[0])+'/market', headers=headers)
    r = response.text
    market_available_JSON = json.loads(r)
    market_available_dict = {
                        'player_id': [],
                        'player_name': [], 
                        'market_value': []
                    }
    market_available_JSON = market_available_JSON[:12]
    for i in range(len(market_available_JSON)):
        market_available_dict['player_id'].append(market_available_JSON[i]['playerMaster']['id'])
        market_available_dict['player_name'].append(market_available_JSON[i]['playerMaster']['nickname'])
        market_available_dict['market_value'].append(market_available_JSON[i]['playerMaster']['marketValue'])
    market_available_dataframe = pd.DataFrame(market_available_dict)

    ## making another request call for each available player in the market of each league to check their value growth over the last 5 days
    value_growth_list = []
    for id in market_available_dataframe.player_id:                                  
        response = requests.get("https://api.laligafantasymarca.com/api/v3/player/" + str(id) + "/market-value", headers=headers)
        r = response.text
        market_value_JSON = json.loads(r)
        value_growth_list.append(-1 * ((market_value_JSON[-5:][0]['marketValue'] - market_value_JSON[-5:][-1]['marketValue']) / market_value_JSON[-5:][-1]['marketValue']))
    market_available_dataframe['market_value_growth_perc_last_5_days'] = value_growth_list
    market_available_dataframe['market_value_since_5_days'] = market_available_dataframe.apply(lambda x: (x.market_value + (x['market_value_growth_perc_last_5_days'] * -x.market_value)) \
                                                                                               if x.market_value_growth_perc_last_5_days < 0 \
                                                                                               else (x.market_value - (x['market_value_growth_perc_last_5_days'] * x.market_value)), axis = 1)
    market_available_dataframe['value_difference_since_5_days'] = market_available_dataframe.apply(lambda x: int(x.market_value) - int(x.market_value_since_5_days), axis=1)
    market_available_dataframe = market_available_dataframe.sort_values(by='value_difference_since_5_days', ascending=False)

    ## Save the results into an excel file
    path = str(user).split('@')[0] + '\\datasets\\'
    if not os.path.exists(path):
        os.makedirs(path)
    market_available_dataframe.to_excel(path+'AvailableMarketPlayers_'+str(k).replace(' ', '_')+'.xlsx', index=False)