import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import os

# Initialize the Dash app
app = dash.Dash(__name__)

# Load data
def load_data():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"../service-account-details.json" 
    file_path_gcp = "gs://oslo-linkedin-dataengineer-jobs/transformed"
    df = pd.read_parquet(file_path_gcp)
    df = df.replace({'seniority':{None:'Mid / not specified'}})
    return df

# Define the layout of the app
app.layout = html.Div([
    html.Div([
        html.H2("Filters"),
        html.Label("Filter 1"),
        dcc.Dropdown(id='filter1', options=[], multi=False),
        html.Label("Filter 2"),
        dcc.Dropdown(id='filter2', options=[], multi=False),
        html.Label("Filter 3"),
        dcc.Dropdown(id='filter3', options=[], multi=False),
        html.Label("Filter 4"),
        dcc.Dropdown(id='filter4', options=[], multi=False),
    ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px', 'backgroundColor': '#f4f4f4'}),
    
    html.Div([
        html.H2("Filtered Data Plot"),
        dcc.Graph(id='graph')
    ], style={'width': '75%', 'display': 'inline-block', 'padding': '20px'}),
])

# Callback to populate the dropdowns with unique values
@app.callback(
    [Output('filter1', 'options'),
     Output('filter2', 'options'),
     Output('filter3', 'options'),
     Output('filter4', 'options')],
    [Input('filter1', 'id')]  # Dummy input to trigger the callback
)
def set_dropdown_options(_):
    df = load_data()
    return [
        [{'label': i, 'value': i} for i in df.job_type.unique().tolist()],
        [{'label': i, 'value': i}for i in df.seniority.unique().tolist()],
        [{'label': i, 'value': i}for i in df['date'].dt.date.unique().tolist()],
        df.explode('skills')['skills'].tolist(),
    ]

# Callback to update the graph based on selected filters
@app.callback(
    Output('graph', 'figure'),
    [Input('filter1', 'value'),
     Input('filter2', 'value'),
     Input('filter3', 'value'),
     Input('filter4', 'value')]
)
def update_graph(filter1, filter2, filter3, filter4):
    df = load_data()

    # Apply filters
    if filter1:
        df = df[df['job_type'] == filter1]
    if filter2:
        df = df[df['seniority'] == filter2]
    if filter3:
        df = df[df['date'] == filter3]
    if filter4:
        df = df[df['skills'].map(lambda x: filter4 in x)]
    
    #### MAKE GRAPH
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

    # share job_type of filtered df
    job_type_share = (df.job_type.value_counts(normalize=True) * 100).astype(int)

    # Explode the 'skills' column and calculate value counts
    skills_counts = pd.DataFrame(df.explode('skills')['skills'].value_counts())

    # Calculate the total number of skills observations
    total_skills = len(df)

    skills_counts = pd.DataFrame(df.explode('skills')['skills'].value_counts())

    skills_counts['percent'] = (((skills_counts['count'] / total_skills) * 100).astype(int))

    # Filter coding languages and cloud skills
    df_coding_languages = skills_counts[skills_counts.index.isin(coding_languages)].reset_index()
    df_cloud_skills = skills_counts[skills_counts.index.isin(list(cloud_skills.values())+list((cloud_skills.keys())))]


    import plotly
    import plotly.express as px


    fig = px.bar(df_coding_languages, x='skills', y='percent', title='Coding skills', labels={'skills': 'Skills', 'percent': 'Percentage of job applications'})
    fig.update_yaxes(range=[0, 100])


    return fig

if __name__ == '__main__':
    app.run_server(debug=True)