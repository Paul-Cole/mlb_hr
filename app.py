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
from pybaseball import cache
cache.disable()

# In[6]:


hits = pb.batting_stats_range("2025-07-16", "2025-07-17")


# In[8]:


drake = [592450.0,
 553993.0,
 695578.0,
 666176.0,
 606466.0,
 592885.0,
 682829.0,
 669257.0,
 518692.0,
 677800.0]

trey = [691718.0,
 673548.0,
 682985.0,
 679529.0,
 596019.0,
 664040.0,
 663656.0,
 669224.0,
 670623.0,
 641355.0]

ty = [660271.0,
 665742.0,
 683737.0,
 621439.0,
 592518.0,
 607043.0,
 696100.0,
 596115.0,
 514888.0,
 571970.0]

nick = [656941.0,
 624413.0,
 605141.0,
 670541.0,
 667670.0,
 608070.0,
 650402.0,
 592663.0,
 664056.0,
 547180.0]

paul = [621566.0,
 665862.0,
 691406.0,
 677951.0,
 663728.0,
 682998.0,
 669065.0,
 606192.0,
 646240.0,
 543807.0]

positions = ['C','1B','2B','SS','3B','LF','CF','RF','DH','WC']


# In[9]:


def create_subset(name, ids):
    subset = hits[hits.mlbID.isin(ids)].sort_values(by="mlbID", key=lambda x: x.map({v: i for i, v in enumerate(ids)}))[['Name','Tm','HR']].copy()
    subset['name'] = name
    
    # Ensure the length matches the number of positions
    if len(subset) < len(positions):
        for _ in range(len(positions) - len(subset)):
            subset = pd.concat([subset, pd.DataFrame([{'Name': 'inactive', 'Tm': 'inactive', 'name': name}])], ignore_index=True)

    
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
    # fig = px.bar(filtered_df, x='Player', y='HR', color='Name',
    #              title='Home Runs by Player',
    #              labels={'HR': 'Home Runs', 'Player': 'Player'})
    fig = px.bar(
        filtered_df,
        x='Player',
        y='HR',
        color='Name',  # Color by team/owner
        title='Total Home Runs by All Players (Color Coded by Team)',
        labels={'HR': 'Home Runs', 'Player': 'Player'},
        text='HR'
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title='Total Home Runs',
        xaxis_title='Player',
        uniformtext_minsize=8,
        uniformtext_mode='hide'
    )

    
    # Calculate overall HR leaders
    hr_leaders = df.groupby('Name').agg({'HR': 'sum'}).reset_index()
    hr_leaders = hr_leaders.sort_values(by='HR', ascending=False).to_dict('records')
    
    return fig, hr_leaders

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
