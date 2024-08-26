#!/usr/bin/env python
# coding: utf-8

# In[4]:


import pybaseball as pb
from pybaseball import statcast,batting_stats,statcast_batter_expected_stats,chadwick_register,batting_stats_range
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output,dash_table
pd.options.display.max_columns = 999
from datetime import datetime
# Get today's date
today = datetime.today().strftime('%Y-%m-%d') 

# Format today's date as a string in yyyy-mm-dd format


# In[6]:


hits = pb.batting_stats_range("2024-07-29", today)


# In[8]:


drake = [668939,547180,606466,677951,666624,641933,671218,666969,542303]

trey = [663728,624413,669357,683002,553993,667670,606192,663656,519317]

ty = [669257,665489,514888,596019,646240,668804,686668,665742,656941]

nick = [669127,572233,650402,607208,608070,595777,701538,623993,660271]

paul = [521692,647304,543760,608369,663586,670541,592450,592206,624585]

positions = ['C','1B','2B','SS','3B','LF','CF','RF','DH']


# In[9]:


def create_subset(name, ids):
    subset = hits[hits.mlbID.isin(ids)].sort_values(by="mlbID", key=lambda x: x.map({v: i for i, v in enumerate(ids)}))[['Name', 'Tm', 'HR']].copy()
    subset['name'] = name
    
    # Ensure the length matches the number of positions
    if len(subset) < len(positions):
        additional_rows = pd.DataFrame({'Name': ['inactive'] * (len(positions) - len(subset)),
                                        'Tm': ['inactive'] * (len(positions) - len(subset)),
                                        'HR': [None] * (len(positions) - len(subset)),
                                        'name': [name] * (len(positions) - len(subset))})
        subset = pd.concat([subset, additional_rows], ignore_index=True)
    
    subset['Position'] = positions
    return subset.set_index('Position')

# Create subsets for each name
drake_df = create_subset('Drake', drake)
trey_df = create_subset('Trey', trey)
ty_df = create_subset('Ty', ty)
nick_df = create_subset('Nick', nick)
paul_df = create_subset('Paul', paul)

# Merge all DataFrames on the index (position)
merged_df  = pd.concat([drake_df,paul_df,nick_df,ty_df,trey_df])
df = merged_df.sort_values('HR',ascending=False).reset_index()
df.rename(columns={'Name':'Player','name':'Name','Tm':'Team','position':'Position'},inplace=True)


# In[10]:


# Create Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.Div([
        html.H2("Overall HR Leaders"),
        dash_table.DataTable(id='hr-leaders-table')
    ], style={'width': '70%', 'display': 'inline-block'}),
    html.H1("Home Runs by Player"),
    html.Div([
        html.Label("Position"),
        dcc.Dropdown(
            id='position-dropdown',
            options=[{'label': pos, 'value': pos} for pos in ['All'] + df['Position'].unique().tolist()],
            value='All'
        ),
        html.Label("Name"),
        dcc.Dropdown(
            id='name-dropdown',
            options=[{'label': name, 'value': name} for name in ['All'] + df['Name'].unique().tolist()],
            value='All'
        ),
    ], style={'width': '25%', 'display': 'inline-block'}),
    dcc.Graph(id='bar-chart')
    
])

# Callback to update the bar chart and table
@app.callback(
    [Output('bar-chart', 'figure'),
     Output('hr-leaders-table', 'data')],
    [Input('position-dropdown', 'value'),
     Input('name-dropdown', 'value')]
)
def update_dashboard(selected_position, selected_name):
    filtered_df = df.copy()
    if selected_position != 'All':
        filtered_df = filtered_df[filtered_df['Position'] == selected_position]
    if selected_name != 'All':
        filtered_df = filtered_df[filtered_df['Name'] == selected_name]
    
    # Create the bar chart
    fig = px.bar(filtered_df, x='Player', y='HR', color='Name',
                 title='Home Runs by Player',
                 labels={'HR': 'Home Runs', 'Player': 'Player'})
    
    # Calculate overall HR leaders
    hr_leaders = df.groupby('Name').agg({'HR': 'sum'}).reset_index()
    hr_leaders = hr_leaders.sort_values(by='HR', ascending=False).to_dict('records')
    
    return fig, hr_leaders

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)


server = app.server




