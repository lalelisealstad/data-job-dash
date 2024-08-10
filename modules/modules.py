import polars as pl
from datetime import datetime, timedelta

def filter_df(df, filter1, filter2,start_date, end_date, filter4 ):
    # Apply filters
    if filter1:
        print(filter1)
        df = df.filter(pl.col("job_type").is_in(filter1))
        print('jobtype', df)

    if filter2:
        df = df.filter(pl.col("seniority").is_in(filter2))
        print('seniority', df)

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        df = df.filter((pl.col("date") >= start_date) & (pl.col("date") < end_date))
        print('date', df)

    if filter4:
        print(filter4)
        df = df.filter(
            df['skills'].map_elements(lambda x: all(skill in x for skill in filter4), return_dtype=pl.List(pl.String))
        )
        print('skill', df)

    print('filtered', df)
    return df


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

# function to make all the necessary tables for figures
import polars as pl
def make_tables(df):
    total_job_postings = len(df)

    job_type_share = df['job_type'].value_counts().with_columns(
        (pl.col("count").alias("counts") / total_job_postings * 100).alias("percentage").round(0).cast(pl.Int16)
    )
    # Explode the 'skills' column and calculate value counts
    skills_counts = df.explode("skills").group_by("skills").len(name="counts").with_columns(
        (pl.col("counts") / total_job_postings * 100).alias("percentage").round(0).cast(pl.Int16)
    )

    # make dfs for coding languages and cloud 
    df_coding_languages = skills_counts.filter(pl.col("skills").is_in(coding_languages))
    df_cloud_skills = skills_counts.filter(pl.col("skills").is_in(list(cloud_skills.values()) + list(cloud_skills.keys())))

    return job_type_share, df_coding_languages, df_cloud_skills


# make standard figure matching dashboard style
import plotly.express as px

def create_bar_chart(x, y, title, x_label = 'skill(s)'):
    fig = px.bar(x=x, y=y, title=title)
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(
        plot_bgcolor='#010103',
        showlegend=False,
        template='plotly_dark',
        paper_bgcolor='#010103',
        font=dict(
            family='Poppins, sans-serif',  # Apply Poppins font
            size=14,  # Set the default font size (adjust as needed)
            color='white'  # Set the font color
        ), 
        title={
            'text': f"{title}<br><span style='font-size:10px;'>The figure shows the percentage of job applications requiring the skill(s)</span>",
        }
    )
    fig.update_xaxes(title_text=x_label)  # Explicitly set the x-axis label
    fig.update_yaxes(title_text='% of job postings'    
                    ,title_font=dict(
        family='Poppins, sans-serif',  # Font family
        size=12,  # Font size (adjust as needed)
        color='white'))  # Font color)  # Explicitly set the y-axis label)
    return fig