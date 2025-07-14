#!/usr/bin/env python
# coding: utf-8

# In[188]:


import pybaseball as pb
from pybaseball import statcast,batting_stats,statcast_batter_expected_stats,chadwick_register,batting_stats_range
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output,dash_table
pd.options.display.max_columns = 999
from datetime import datetime
# Get today's date
today = datetime.today().strftime('%Y-%m-%d') 
import glob
import os

# Format today's date as a string in yyyy-mm-dd format


# In[189]:


hits = pb.batting_stats_range("2025-07-06", today)


# In[190]:


picks = pd.read_csv('picks.csv')


# In[191]:


groups = (
    picks.groupby('pick')['player_id']
    .apply(lambda x: list(dict.fromkeys(int(i) for i in x if pd.notna(i))))
    .to_dict()
)

# Dynamically assign each list to a variable like drake, trey, etc.
for name, numbers in groups.items():
    globals()[name] = numbers


# In[192]:


positions = ['C','1B','2B','SS','3B','LF','CF','RF','DH','WC']


# In[193]:


def create_subset(name, ids):
    # Sort by order of IDs
    subset = hits[hits.mlbID.isin(ids)].sort_values(
        by="mlbID", key=lambda x: x.map({v: i for i, v in enumerate(ids)})
    )[['Name', 'Tm', 'HR']].copy()

    subset['name'] = name

    # Pad with 'inactive' rows if too short
    while len(subset) < len(positions):
        inactive_row = pd.DataFrame([{
            'Name': 'inactive', 'Tm': 'inactive', 'HR': 0, 'name': name
        }])
        subset = pd.concat([subset, inactive_row], ignore_index=True)

    # Truncate if too long
    subset = subset.iloc[:len(positions)].copy()

    # Assign positions
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


# In[194]:


merged_df.to_csv(f'./hr_over_time/hr_tracking_{today}.csv', index=False)


# In[195]:


# Read all CSVs into a single DataFrame
all_files = glob.glob("./hr_over_time/hr_tracking*.csv")

dfs = []
for file in all_files:
    df_time = pd.read_csv(file)
    df_time['Date'] = os.path.basename(file).split('_')[-1].replace('.csv', '')  # extract date from filename
    dfs.append(df_time)

tracking_df = pd.concat(dfs)




from dash import Dash, dcc, html, dash_table, Input, Output
import pandas as pd
import plotly.express as px

# Convert Date to date only (no time)
tracking_df['Date'] = pd.to_datetime(tracking_df['Date']).dt.date

# Create Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    html.H2("Total Home Runs by Player"),
    dash_table.DataTable(
        id='total-hr-by-name-table',
        columns=[
            {"name": "Name", "id": "name"},
            {"name": "Total HR", "id": "total_hr"}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    ),

    html.Hr(),

    html.H2("Total Home Runs Over Time"),
    dcc.Graph(id='total-hr-over-time'),

    html.Hr(),

    html.H2("Home Runs Over Time by Player"),
    html.Div([
        html.Label("Select Team/Owner"),
        dcc.Dropdown(
            id='name-dropdown',
            options=[{'label': n, 'value': n} for n in sorted(tracking_df['name'].unique())],
            value=sorted(tracking_df['name'].unique())[0]
        ),
        html.Label("Select Player"),
        dcc.Dropdown(
            id='player-dropdown',
            clearable=True  # <-- Allow clearing to show all players
        ),
    ], style={'width': '40%', 'display': 'inline-block', 'verticalAlign': 'top'}),

    dcc.Graph(id='player-hr-over-time'),

    html.Hr(),

    html.H2("Current Day HR Table"),
    dash_table.DataTable(
        id='hr-leaders-table',
        columns=[{"name": col, "id": col} for col in ['Name', 'Tm', 'HR', 'name', 'Date']],
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left'},
    )
])

# Callback to update player dropdown
@app.callback(
    Output('player-dropdown', 'options'),
    Output('player-dropdown', 'value'),
    Input('name-dropdown', 'value')
)
def update_player_dropdown(selected_name):
    players = tracking_df[tracking_df['name'] == selected_name]['Name'].unique()
    options = [{'label': p, 'value': p} for p in sorted(players)]
    # Default to None to show all players initially
    return options, None

# Callback to update total HR over time chart
@app.callback(
    Output('total-hr-over-time', 'figure'),
    Input('name-dropdown', 'value')
)
def update_total_hr_chart(_):
    totals = tracking_df.groupby(['Date', 'name'])['HR'].sum().reset_index()
    totals = totals.sort_values('Date')

    fig = px.line(
        totals,
        x='Date',
        y='HR',
        color='name',
        markers=False,
        title='Total HRs Over Time',
        labels={'HR': 'Home Runs', 'Date': 'Date', 'name': 'Name'}
    )

    unique_dates = sorted(totals['Date'].astype(str).unique())
    fig.update_xaxes(
        type='category',
        categoryorder='array',
        categoryarray=unique_dates,
        tickmode='array',
        tickvals=unique_dates,
        ticktext=unique_dates
    )

    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Total HRs',
        legend_title='Name'
    )

    return fig

# Callback to update individual player chart
@app.callback(
    Output('player-hr-over-time', 'figure'),
    Input('name-dropdown', 'value'),
    Input('player-dropdown', 'value')
)
def update_player_chart(selected_name, selected_player):
    if not selected_name:
        return {}

    if selected_player:
        # Filter for specific player
        filtered = tracking_df[
            (tracking_df['name'] == selected_name) &
            (tracking_df['Name'] == selected_player)
        ].sort_values('Date')

        title = f'HRs Over Time for {selected_player}'
    else:
        # Show all players for the selected name
        filtered = tracking_df[
            tracking_df['name'] == selected_name
        ].sort_values(['Name', 'Date'])

        title = f'HRs Over Time for All Players under {selected_name}'

    if filtered.empty:
        return {}

    fig = px.line(
        filtered,
        x='Date',
        y='HR',
        color='Name' if not selected_player else None,  # color by player if showing all
        markers=False,
        title=title,
        labels={'HR': 'Home Runs', 'Date': 'Date'}
    )

    unique_dates = sorted(filtered['Date'].astype(str).unique())
    fig.update_xaxes(
        type='category',
        categoryorder='array',
        categoryarray=unique_dates,
        tickmode='array',
        tickvals=unique_dates,
        ticktext=unique_dates
    )

    fig.update_layout(xaxis_title='Date', yaxis_title='HRs')

    return fig

# Callback to update current day HR table
@app.callback(
    Output('hr-leaders-table', 'data'),
    Input('name-dropdown', 'value')
)
def update_hr_table(_):
    latest_date = tracking_df['Date'].max()
    table = tracking_df[tracking_df['Date'] == latest_date].sort_values(by='HR', ascending=False)
    return table.to_dict('records')

# Callback to populate total HR by name table
@app.callback(
    Output('total-hr-by-name-table', 'data'),
    Input('name-dropdown', 'value')  # still used just to trigger update
)
def update_total_hr_table(_):
    latest_date = tracking_df['Date'].max()
    filtered = tracking_df[tracking_df['Date'] == latest_date]
    summary = filtered.groupby('name')['HR'].sum().reset_index().rename(columns={'HR': 'total_hr'})
    summary = summary.sort_values(by='total_hr', ascending=False)
    return summary.to_dict('records')

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)


# In[ ]:
