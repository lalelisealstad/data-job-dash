import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import os
from collections import Counter
from datetime import datetime
from datetime import date
import dash_bootstrap_components as dbc

global gdf
global df

# Initialize the Dash app
app = dash.Dash(__name__)


# Load data
def load_data():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"../service-account-details.json" 
    file_path_gcp = "gs://oslo-linkedin-dataengineer-jobs/transformed"
    df = pd.read_parquet(file_path_gcp)
    df = df.replace({'seniority': {None: 'Mid / not specified'}})
    return df

gdf = load_data()

# Define the layout of the app
app.layout = html.Div([
    html.Div([
        html.H2("Filters"),

        html.Div([
            html.Label("Filter job type "),
            dcc.Dropdown(id='filter1', options=[{'label': 'Data Analyst', 'value': 'Data Analyst'},
                                                {'label': 'Data Engineer', 'value': 'Data Engineer'},
                                                {'label': 'Data Scientist', 'value': 'Data Scientist'}],
                         multi=True, value=[], placeholder="Filter job type", clearable=False),
        ], className='filter-div'),  # Add className for custom styling

        html.Div([
            html.Label("Filter seniority "),
            dcc.Dropdown(id='filter2', options=[{'label': 'Mid / not specified', 'value': 'Mid / not specified'},
                                                {'label': 'Junior', 'value': 'Junior'},
                                                {'label': 'Senior', 'value': 'Senior'},
                                                {'label': 'Lead', 'value': 'Lead'},
                                                {'label': 'Manager', 'value': 'Manager'}],
                         multi=True, value=[], placeholder="Filter seniority type", clearable=True),
        ], className='filter-div'),  # Add className for custom styling

        html.Div([
            html.Label("Filter skills  "),
            dcc.Dropdown(id='filter4', placeholder='Filter skills', options=[], multi=True, clearable=True),
        ], className='filter-div'),  # Add className for custom styling

        html.Div([
            html.Label("Filter date posted   "),
            dcc.DatePickerRange(
                id='filter3',
                start_date=None,
                end_date=None,
                display_format='YYYY-MM-DD',
            ),
        ], className='custom-date-picker', style={'width': '100%'}),  # Add className for custom styling

    ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px', 'backgroundColor': '#f4f4f4'}),
    
    html.Div([
        html.H2("Filtered Data Plot"),
        dcc.Graph(id='graph')
    ], style={'width': '75%', 'display': 'inline-block', 'padding': '20px'}),
])


# Callback to populate the date picker and dropdowns with unique values
@app.callback(
    [Output('filter3', 'start_date'),
     Output('filter3', 'end_date'),
     Output('filter4', 'options')],
    [Input('filter1', 'value')]
)

def set_dropdown_options(_):
    if gdf.date.max().date() < date.today():
        df = load_data()
    else: 
        df = gdf
    
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    skill_options = df.explode('skills')['skills'].tolist()
    
    return min_date, max_date, skill_options

# Callback to update the graph based on selected filters
@app.callback( 
    Output('graph', 'figure'),
    [Input('filter1', 'value'),
     Input('filter2', 'value'),
     Input('filter3', 'start_date'),
     Input('filter3', 'end_date'),
     Input('filter4', 'value')]
)
def update_graph(filter1, filter2, start_date, end_date, filter4):
    df = gdf
    print(df)
    
    # Apply filters
    if filter1:
        print(filter1)
        df = df[df['job_type'].isin(filter1)]
        print('jobtype', df)
    if filter2:
        df = df[df['seniority'].isin(filter2)]
        print('seniority', df)
    if start_date and end_date:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date) + pd.Timedelta(days=1)
        df['date'] = pd.to_datetime(df['date'])
        print(start_date, end_date)
        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
        print('date',df)
    if filter4:
        print(filter4)
        df = df[df['skills'].map(lambda x: all(skill in x for skill in filter4))]
        print('skill', df)
    print('filtered', df)
    # Define coding languages and cloud skills
    coding_languages = [
        'python', 'javascript', 'java', 'c++', 'c#', 'php', 'ruby', 'swift', 'kotlin', 'typescript',
        'go', 'rust', 'sql', 'r', 'html', 'css', 'bash', 'perl', 'objective-c', 'scala',
        'lua', 'haskell', 'matlab', 'dart', 'visual basic .net', 'assembly language', 'f#', 'groovy', 'elixir', 'clojure',
        'erlang', 'julia', 'vbscript', 'lisp', 'prolog', 'scheme', 'ada', 'fortran', 'cobol', 'pascal',
        'racket', 'scratch', 'tcl', 'smalltalk', 'actionscript', 'awk', 'ocaml', 'pl/sql', 'sas', 'logo'
    ]
    cloud_skills = {
        'aws': 'amazon web services',
        'gcp': 'google cloud platform',
        'azure': 'microsoft azure',
        'ibm': 'ibm cloud',
        'oci': 'oracle cloud',
        'sf': 'salesforce',
        'sap': 'sap cloud',
        'do': 'digitalocean'
    }

    job_type_share = (df.job_type.value_counts(normalize=True) * 100).astype(int)
    # Explode the 'skills' column and calculate value counts\
    skills_counts = pd.DataFrame(df.explode('skills')['skills'].value_counts())
    
    total_skills = len(df)
    skills_counts['percent'] = ((skills_counts['count'] / total_skills) * 100).astype(int)

    # Filter coding languages and cloud skills
    df_coding_languages = skills_counts[skills_counts.index.isin(coding_languages)].reset_index()
    df_cloud_skills = skills_counts[skills_counts.index.isin(list(cloud_skills.values()) + list(cloud_skills.keys()))]
    print(df_coding_languages)
    # Create the bar chart
    fig = px.bar(df_coding_languages, x='skills', y='percent', title='Coding skills', labels={'index': 'Skills', 'percent': 'Percentage of job applications'})
    fig.update_yaxes(range=[0, 100])

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
