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



# Looping into leagues dicionary to make calls and load results for each league into excel files
for k, v in leagues_info.items():
    df2 = pd.DataFrame()
    ## Loop for each fixture in the league
    for fixture in range(1, 39):
        r = requests.get('https://api-fantasy.llt-services.com/api/v3/leagues/'+str(v[0])+ '/ranking/'+str(fixture), headers=headers)
        r = r.text
        r = json.loads(r)
        managerNameList = []
        Round = []
        Points = []
        ### Loop for each manager in the fixture
        for manager in range(len(r)):
            managerNameList.append(r[manager]['team']['manager']['managerName'])
            Round.append(fixture)
            Points.append(r[manager]['points'])
        df = pd.DataFrame()
        df['managerName'] = managerNameList
        df['Round'] = Round
        df['Points'] = Points
        df2 = pd.concat([df, df2])
    df2 = df2.sort_values(by='Round')    
    df1 = df2.groupby(['Round']).Points.sum().reset_index()
    df1['Points'] = df1['Points'].replace(0, np.nan)
    df1 = df1.dropna()[['Round']]
    df2 = df1.merge(df2, how='left', on='Round')[['managerName', 'Round', 'Points']]
    ### Save excel file
    path = str(user).split('@')[0] + '\\datasets\\'
    if not os.path.exists(path):
        os.makedirs(path)
    df2.to_excel(path+'Total_standings_'+str(k).replace(' ', '_')+'.xlsx', index=False)
    ## Get My standings Points:
    r = requests.get('https://api-fantasy.llt-services.com/api/v3/user/me?x-lang=en', headers=headers)
    r = r.text
    r = json.loads(r)
    ### Save My excel file
    df2[df2.managerName==str(r['managerName'])].to_excel(path+'MyStandings_'+str(k).replace(' ', '_')+'.xlsx', index=False)
