import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import os
from collections import Counter
from datetime import date, timedelta
import dash_bootstrap_components as dbc
import polars as pl
from google.cloud import storage
import gcsfs
from apps.modules import load_data, filter_df, make_tables, create_bar_chart, make_treemap, empty_fig
import plotly.graph_objects as go

global gdf
global df

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"../service-account-details.json" 

# Initialize the Dash app
app = dash.Dash(__name__)

gdf = load_data()

# Define the layout of the app
app.layout = html.Div([
    # Left side pane
    html.Div([
        html.H1("Explore data jobs in London"),
        html.H4("Interact with the filters below to see the skills mentioned in job postings for data-related roles"),
        html.Div([
            dcc.Dropdown(id='filter1', options=[{'label': 'Data Analyst', 'value': 'Data Analyst'},
                                                {'label': 'Data Engineer', 'value': 'Data Engineer'},
                                                {'label': 'Data Scientist', 'value': 'Data Scientist'}],
                         multi=True, value=[], placeholder="Filter job type", clearable=False),
        ], className='filter-div'),  

        html.Div([
            dcc.Dropdown(id='filter2', options=[{'label': 'Mid / not specified', 'value': 'Mid / not specified'},
                                                {'label': 'Junior', 'value': 'Junior'},
                                                {'label': 'Senior', 'value': 'Senior'},
                                                {'label': 'Lead', 'value': 'Lead'},
                                                {'label': 'Manager', 'value': 'Manager'}],
                         multi=True, value=[], placeholder="Filter seniority type", clearable=True),
        ], className='filter-div'),  

        html.Div([
            dcc.Dropdown(id='filter4', placeholder='Filter skills', options=[], multi=True, clearable=True),
        ], className='filter-div'), 

        html.Div([
            dcc.DatePickerRange(
                id='filter3',
                start_date=None,
                end_date=None,
                display_format='YYYY-MM-DD',
                min_date_allowed = '2024-08-08'
            ),
        ], className='custom-date-picker'),  
        
        html.Div(
            html.P(id ='text-output_filter', className="footer")
        ), 
        
        html.Div([
            html.Div(
                html.H5("This data is based on a sample of LinkedIn data-related job postings with the search terms 'Data Scientist','Data Engineer' and 'Data Analyst' based in London, UK. The data collected using a custom web scraping pipeline I built. The pipeline is updated every evening with a sample of up to 75 job postings that were posted that day. For more information, see my GitHub repos for the dashboard and the datapipeline.", className='footer')
            ), 
            html.Div(
                html.A("See my GitHub", href="https://github.com/lalelisealstad", target="_blank", className="footer")
        )], style= { 'boxSizing': 'border-box','position': 'relative', 'margin-top': '200px' })
        
    ], style={'width': '25%', 'height': '100vh', 'display': 'inline-block', 'verticalAlign': 'top', 'padding': '20px', 'background-color': 'transparent', 'boxSizing': 'border-box'}),
    
    # figures 
    html.Div([
        html.H2("Percentage of job postings that mentiones skill(s)"),
        html.Div(
            html.P(id ='text-output_len_jobs', className= 'total_jobs')
        ), 
        html.Div([
            dcc.Graph(id='graph', style={'height': '500px', 'width': '33%'}),
            dcc.Graph(id='graph_cloud', style={'height': '500px', 'width': '33%'}),
            dcc.Graph(id='graph_job_type', style={'height': '500px', 'width': '33%', 'paddingRight': '10px'})  
        ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '0px'}),
        
        dcc.Graph(id='treemap', style={'height': '680px', 'width': '100%', 'marginTop': '0px'}),
    ], style={'width': '75%', 'display': 'inline-block', 'padding': '10px', 'boxSizing': 'border-box'}),
    
], style={ "transform-origin": "top left",  'background-color': 'black'})



# Callback to populate the date picker and dropdowns with unique values
@app.callback(
    [Output('filter3', 'start_date'),
     Output('filter3', 'end_date'),
     Output('filter4', 'options')],
    [Input('filter1', 'value')]
)

def set_dropdown_options(_):
    # make global so it will be used in update figures
    global gdf
    # function to make sure data is only loaded once
    yesterday = date.today() - timedelta(days=1)
    # Check if the max date in the DataFrame is less than yesterday
    if gdf.select(pl.col("date").max()).item().date() < yesterday:
        gdf = load_data()
    else:
        gdf = gdf

    min_date = gdf.select(pl.col("date").min()).item().date()
    max_date = gdf.select(pl.col("date").max()).item().date()
    skill_options = gdf.select(pl.col("skills")).explode("skills").to_series().to_list()
    
    return min_date, max_date, skill_options

# Callback to update the graph based on selected filters
@app.callback(
    [Output('graph', 'figure'),
     Output('graph_cloud', 'figure'), 
     Output('graph_job_type', 'figure'), 
     Output('treemap', 'figure'),
     Output('text-output_filter', 'children'),
     Output('text-output_len_jobs', 'children'),],
    [Input('filter1', 'value'),
     Input('filter2', 'value'),
     Input('filter3', 'start_date'),
     Input('filter3', 'end_date'),
     Input('filter4', 'value')]
)
def update_graph(filter1, filter2, start_date, end_date, filter4):

    # filter global dataframe 
    df = filter_df(gdf, filter1, filter2,start_date, end_date, filter4 )

    # if filtered df has no rows, return filter warning and empty figures
    if len(df) < 1: 
        filter_warning = 'No job postings with the selected filters!'
        return empty_fig(), empty_fig(), empty_fig(), empty_fig(), filter_warning, ''
    else: 
        job_type_share, df_coding_languages, df_cloud_skills, skills_counts = make_tables(df)    
        
        total_jobs_text = f"Out of {len(df)} job postings in the selected date interval"
        filter_warning = ''

        # Create bar chart for coding languages
        if len(df_coding_languages) > 0: 
            fig_code = create_bar_chart(
                x=df_coding_languages['skills'],
                y=df_coding_languages['percentage'],
                title='Coding language',
            )
        else: 
            fig_code = empty_fig()
            filter_warning = 'There are no coding languages in job postings with the selected filters!'

        # Create fig for cloud provider
        if len(df_cloud_skills) > 0: 
            fig_cloud = create_bar_chart(
                x=df_cloud_skills['skills'],
                y=df_cloud_skills['percentage'],
                title='Cloud service provider experience',
            )
        else: 
            fig_cloud = empty_fig()
            filter_warning = 'There are no cloud providers in job postings with the selected filters!'


        # Create bar chart for job type
        if len(job_type_share) > 0: 
            fig_job_type = create_bar_chart(
                x=job_type_share['job_type'],
                y=job_type_share['percentage'],
                title='Job type',
                x_label='job type',
            )
        else: 
            fig_job_type = empty_fig()
            filter_warning = 'There are no job types in job postings with the selected filters!'

        # tree map of all skills
        if len(skills_counts) > 0: 
            treemap = make_treemap(skills_counts)
        else: 
            treemap = empty_fig()
            filter_warning = 'There are no job postings with the selected filters!'

        return fig_code, fig_cloud, fig_job_type, treemap, filter_warning, total_jobs_text

if __name__ == '__main__':
    app.run_server(debug=True)
