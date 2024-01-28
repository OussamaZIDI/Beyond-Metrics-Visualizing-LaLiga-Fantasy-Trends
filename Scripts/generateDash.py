# Libs
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objs as go
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
league_names = []
league_ids = []
team_ids = []

# get league name
for i in range(len(leagues_json)):
    league_names.append(leagues_json[i]['name'])

# get league id
for i in range(len(leagues_json)):
    league_ids.append(leagues_json[i]['id'])

# get team id
for i in range(len(leagues_json)):
    team_ids.append(leagues_json[i]['team']['id'])

# Creating League dictionary
zipped_list = list(zip(league_ids, team_ids))
leagues_info = dict(zip(league_names, zipped_list))



# Creating Dashboard for each League the player is currently on:
excel_directory = str(user).split('@')[0] + '\\datasets\\'
for name in league_names:
    ## Getting excel files for each League
    substring = name.replace(' ', '_')
    ### List all files in the directory
    all_files = os.listdir(excel_directory)
    ### Filter files based on the substring
    matching_files = [file for file in all_files if (substring in file)]
    for file in matching_files:
        file_path = os.path.join(excel_directory, file)
        df = pd.read_excel(file_path)
        #### Create subplot
        fig = sp.make_subplots(rows=5, cols=4,
                                specs=[
                                    [{"type": "Indicator", "colspan": 2}, None, {"type": "Indicator", "colspan": 2}, None],
                                    [{"colspan": 2}, None, {"colspan": 2}, None],
                                    [{"colspan": 2}, None, {}, {"type": "Indicator"}],
                                    [{}, {"type": "Indicator"}, {"type": "Table", "colspan": 2}, None],
                                    [{"colspan": 2}, None, {"colspan": 2}, None],
                                    ],
                                row_heights=[
                                    0.1, 
                                    1,
                                    1,
                                    1,
                                    1,
                                    ],
                                column_widths=[
                                    1, 
                                    0.5,
                                    1,
                                    0.5,
                                    ],
                            subplot_titles=[    
                                        "Current Balance", "Total Players Value",
                                        "Total Points By Manager", "My Points By Round",
                                        "My Players Market Value/Release Clause", "My Players Value Diff since 5 days", "",
                                        "My Players Average Points", "", "My Players Data",
                                        "Market Players Value Diff since 5 days", "Top League Players with Most Growing Value since 5 days",
                                    ],
                                )

    for file in matching_files:
        file_path = os.path.join(excel_directory, file)
        df = pd.read_excel(file_path)
        #### Total Standings Excel File
        if 'Total_standings' in file:
            r = requests.get('https://api-fantasy.llt-services.com/api/v3/user/me?x-lang=en', headers=headers)
            r = r.text
            r = json.loads(r)
            df = df.groupby(['managerName']).Points.sum().reset_index()
            df = df.sort_values(by='Points', ascending=0)
            colors = ['darkblue' if (row.managerName==str(r['managerName'])) else '#686cfc' for index,row in df.iterrows()]
            fig_6 = go.Bar(name='Total Points By Manager', y=df.Points, x=df.managerName, marker_color=colors)
            fig.add_trace(fig_6, row=2, col=1)
        #### My Standings
        if 'MyStandings' in file:
            df = df.sort_values(by='Round')
            fig_9 = px.line(df, x="Round", y="Points", title="My Points By Round")
            fig_9.update_layout(xaxis_title='', yaxis_title='', title_font_size=32)
            fig.add_trace(fig_9.data[0], row=2, col=3)
        #### My Player's Team Value Excel File
        if 'TeamInfo' in file:
            response = requests.get('https://api.laligafantasymarca.com/api/v3/leagues/'+str(leagues_info[name][0])+'/teams/'+str(leagues_info[name][1]), headers=headers)
            r = response.text
            team_page_info = json.loads(r)
            ## PLOT
            fig_15 = go.Indicator(
                value = team_page_info['teamMoney'],
                number = {'prefix': "$",
                          'font': {
                              'size': 32
                          }},
                gauge = {'axis': {'visible': False}},
                domain = {'row': 0, 'column': 0})
            fig.add_trace(fig_15, row=1, col=1)

            ## PLOT
            fig_17 = go.Indicator(
                value = team_page_info['teamValue'],
                number = {'prefix': "$",
                          'font': {
                              'size': 32
                          }},
                gauge = {'axis': {'visible': False}},
                domain = {'row': 0, 'column': 0})
            fig.add_trace(fig_17, row=1, col=3)


            ## PLOT
            df_sorted = df.sort_values(by='Market Value', ascending=0)
            fig_24 = go.Bar(name='Release Clause', y=df_sorted['Release Clause'], x=df_sorted['Name'], marker_color='cadetblue')
            fig_25 = go.Bar(name='Market Value', y=df_sorted['Market Value'], x=df_sorted['Name'], marker_color='#686cfc')
            fig.add_trace(fig_24, row=3, col=1)
            fig.add_trace(fig_25, row=3, col=1)

            ## PLOT
            fig_3 = px.bar(df.sort_values(by='value_difference_since_5_days', ascending=0), y=["value_difference_since_5_days"], x="Name", barmode="group", title="My Players Value Diff Since 5 days")
            fig_3.update_layout(xaxis_title='', yaxis_title='', title_font_size=32)
            fig_3.update_layout(
            legend=dict(
                orientation="h",  # "h" for horizontal, "v" for vertical
                x=0.8,  # Adjust the x-coordinate
                y=-0.2,  # Adjust the y-coordinate
            )
            )
            fig.add_trace(fig_3.data[0], row=3, col=3)

            ## PLOT
            fig_21 = go.Indicator(
                value = round(df['value_difference_since_5_days'].sum(), 2),
                number = {
                          'font': {
                              'size': 32
                          }},
                title = {'text': "Sum Players Value Diff",
                        'font': {
                              'size': 20
                          }},
                gauge = {'axis': {'visible': False}},
                domain = {'row': 0, 'column': 0})
            fig.add_trace(fig_21, row=3, col=4)

            
            ## PLOT
            fig_2 = px.bar(df.sort_values(by='Avg Pts', ascending=0), y=["Avg Pts"], x="Name", barmode="group", title="My Players Average Points")
            fig_2.update_layout(xaxis_title='', yaxis_title='', title_font_size=32)
            fig_2.update_layout(
            legend=dict(
                orientation="h",  # "h" for horizontal, "v" for vertical
                x=0.8,  # Adjust the x-coordinate
                y=-0.2,  # Adjust the y-coordinate
            )
            )
            fig.add_trace(fig_2.data[0], row=4, col=1)

            ## PLOT
            fig_16 = go.Indicator(
                value = round(df['Avg Pts'].mean(), 2),
                number = {
                          'font': {
                              'size': 32
                          }},
                title = {'text': "Total Players Avg",
                        'font': {
                              'size': 20
                          }},
                gauge = {'axis': {'visible': False}},
                domain = {'row': 0, 'column': 0})
            fig.add_trace(fig_16, row=4, col=2)

            ## PLOT
            df2 = df[['Name', 'Recommendation', 'Latest Form', 'Condition']]
            df2['Recommendation'] = pd.Categorical(df2['Recommendation'], ["On fire", "Excellent way", "Good moment", "it can be better", "Not recommended", "Does not score"], ordered=True)
            df2 = df2.sort_values(by='Recommendation')
            fig_22 = go.Table(
                header=dict(values=list(df2.columns),
                            fill_color='paleturquoise',
                            align='left'),
                cells=dict(values=[df2.Name, df2.Recommendation, df2['Latest Form'], df2.Condition],
                        fill_color='lavender',
                        align='left'))
            fig.add_trace(fig_22, row=4, col=3)
            
        #### Players Available in the Market
        if 'AvailableMarketPlayers' in file:
            fig_4 = px.bar(df.sort_values(by='value_difference_since_5_days', ascending=0), y=["value_difference_since_5_days"], x="player_name", barmode="group", title="Market Players Value Diff since 5 days")
            fig_4.update_layout(xaxis_title='', yaxis_title='', title_font_size=32)
            fig_4.update_layout(
            legend=dict(
                orientation="h",  # "h" for horizontal, "v" for vertical
                x=0.8,  # Adjust the x-coordinate
                y=-0.2,  # Adjust the y-coordinate
            )
            )
            fig.add_trace(fig_4.data[0], row=5, col=1)

        # Add top value growth players chart:
        df = pd.read_excel(excel_directory +'Top_20_Growing_players.xlsx')
        fig_5 = px.bar(df.sort_values(by='value_difference_since_5_days', ascending=0), y=["value_difference_since_5_days"], x="player_name", barmode="group", title="Players with most growing value since 5 days")
        fig_5.update_layout(xaxis_title='', yaxis_title='', title_font_size=32)
        fig_5.update_layout(
        legend=dict(
            orientation="h",  # "h" for horizontal, "v" for vertical
            x=0.8,  # Adjust the x-coordinate
            y=-0.2,  # Adjust the y-coordinate
        )
        )
        fig.add_trace(fig_5.data[0], row=5, col=3)
        
    # Update layout of individual plots
    fig.update_layout(height=2000, width=1550)
    # Update layout
    fig.update_layout(title= str(name) +": "+str(r['managerName'])+"'s Dashboard", showlegend=False)
    fig.update_layout(title_font_color='blue', title_font_size = 50, title_x=0.23)
    
    # Save the dashboard as an HTML file
    path2 = str(user).split('@')[0] + '\\dashboards\\'
    if not os.path.exists(path2):
        os.makedirs(path2)
    fig.write_html(path2 + str(name)+ "_dashboard.html")