import polars as pl
from datetime import datetime, timedelta

def load_data():
    file_path_gcp = "gs://oslo-linkedin-dataengineer-jobs/transformed/*.parquet"
    df = pl.read_parquet(file_path_gcp)
    df = df.with_columns(
        pl.when(pl.col("seniority").is_null())
        .then(pl.lit("Mid / not specified"))
        .otherwise(pl.col("seniority"))
        .alias("seniority")
        )
    return df

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
    'Python', 'Javascript', 'Java', 'C++', 'C#', 'Php', 'Ruby', 'Swift', 'Kotlin', 'Typescript',
    'Go', 'Rust', 'Sql', 'R', 'Html', 'Css', 'Bash', 'Perl', 'Objective-C', 'Scala',
    'Lua', 'Haskell', 'Matlab', 'Dart', 'Visual Basic .Net', 'Assembly Language', 'F#', 'Groovy', 'Elixir', 'Clojure',
    'Erlang', 'Julia', 'Vbscript', 'Lisp', 'Prolog', 'Scheme', 'Ada', 'Fortran', 'Cobol', 'Pascal',
    'Racket', 'Scratch', 'Tcl', 'Smalltalk', 'Actionscript', 'Awk', 'Ocaml', 'Pl/Sql', 'Sas', 'Logo'
]
cloud_skills = {
    'Aws': 'Amazon Web Services',
    'Gcp': 'Google Cloud Platform',
    'Azure': 'Microsoft Azure',
    'Ibm': 'Ibm Cloud',
    'Oci': 'Oracle Cloud',
    'Sf': 'Salesforce',
    'Sap': 'Sap Cloud',
    'Do': 'Digitalocean'
}

# function to make all the necessary tables for figures
def make_tables(df):
    total_job_postings = len(df)

    job_type_share = df['job_type'].value_counts().with_columns(
        (pl.col("count").alias("counts") / total_job_postings * 100).alias("percentage").round(0).cast(pl.Int16)
    ).with_columns([
    pl.col("job_type").str.to_titlecase().alias("job_type")
    ])
    # Explode the 'skills' column and calculate value counts
    skills_counts = df.explode("skills").group_by("skills").len(name="counts").with_columns(
        (pl.col("counts") / total_job_postings * 100).alias("percentage").round(0).cast(pl.Int16)
    ).with_columns([
    pl.col("skills").str.to_titlecase().alias("skills")
    ])
    skills_counts = skills_counts.unique(subset=["skills"], keep="first")
    skills_counts = skills_counts.filter(pl.col("skills").is_not_null())
    
    # make dfs for coding languages and cloud 
    df_coding_languages = skills_counts.filter(pl.col("skills").is_in(coding_languages))
    df_cloud_skills = skills_counts.filter(pl.col("skills").is_in(list(cloud_skills.values()) + list(cloud_skills.keys())))

    return job_type_share, df_coding_languages, df_cloud_skills, skills_counts


# make standard figure matching dashboard style
import plotly.express as px
def create_bar_chart(x, y, title, x_label='skill(s)'):
    fig = px.bar(x=x, y=y, title=title)
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(
        plot_bgcolor='#010103',
        showlegend=False,
        template='plotly_dark',
        paper_bgcolor='#010103',
        font=dict(
            family='Poppins, sans-serif',  # Apply Poppins font
            size=18,  # Set the default font size (adjust as needed)
            color='white'  # Set the font color
        ), 
        title={
            'text': f"{title}",
        }
    )
    fig.update_xaxes(title_text=x_label)  # Explicitly set the x-axis label
    fig.update_yaxes(title_text='% of job postings',
                     title_font=dict(
                         family='Poppins, sans-serif',  # Font family
                         size=16,  # Font size (adjust as needed)
                         color='white'))  # Font color
    
    fig.update_traces(marker_color='#08519c', marker_line_color='#f7fbff',
                      marker_line_width=1.5, opacity=0.8,
                      hovertemplate='<span style="font-family:Poppins, sans-serif; font-size:20px;"><b>Skill:</b> %{x}<br><b>Percentage:</b> %{y}%</span>')
    
    return fig

# blue colors same as treemap
#f7fbff
#deebf7
#c6dbef
#9ecae1
#6baed6
#4292c6
#2171b5
#08519c
#08306b


import plotly.express as px

def make_treemap(skills_counts):
    skills_counts_dict = {
        "skills": skills_counts["skills"].to_list(),
        "percentage": skills_counts["percentage"].to_list()
    }
    print(skills_counts_dict)
    # Create a treemap using Plotly
    treemap = px.treemap(
        skills_counts_dict,
        path=['skills'],  # This creates the hierarchical path
        values='percentage',
        color='percentage',  # Optional: color by frequency
        color_continuous_scale='Blues',  # Optional: color scale
        height=750,  # Adjust height as needed
    )
    # Update layout to apply black background and Poppins font
    treemap.update_layout(
        plot_bgcolor='#010103',  # Background color of the plot
        paper_bgcolor='#010103',  # Background color of the paper
        font=dict(
            family='Poppins, sans-serif',  # Apply Poppins font
            size=18,  # Set the default font size
            color='white'  # Set the font color
        ),
        title='', 
        coloraxis_showscale=False 
    )

    treemap.update_traces(
        hovertemplate='<span style="font-family:Poppins, sans-serif; font-size:20px;"><b>Skill</b>: %{label}<br><b>Percent</b>: %{value}%</span><extra></extra>'
    )

    # Show the plot
    return treemap
