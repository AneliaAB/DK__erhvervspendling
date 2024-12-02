import subprocess
import os
import sys
#_________________________________________________________INSTALLING PACKAGES__________________________________________________________
def run_bash_setup():
    if os.path.isfile("setup.sh"):
        print("Running setup.sh...")
        try:
            subprocess.run(["bash", "setup.sh"], check=True)
            print("setup.sh executed successfully.")
        except subprocess.CalledProcessError as e:
            print("An error occurred while running setup.sh:", e)
    else:
        print("No setup.sh file found. Skipping bash setup.")

# Run the setup steps
if __name__ == "__main__":
    run_bash_setup()

from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd
import sys
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import geopandas as gpd
#______________________________________________________HELPER FUNCTIONS______________________________________________________________
#for loading segment data
def load_and_process_data(files, delimiter, encoding='utf-8'):
    processed_data = []
    for file in files:
        # Read the data
        data = pd.read_csv(file, delimiter=delimiter, encoding=encoding)
        # Filter out 'København' and 'Aarhus' for heatmap readability
        data_filtered = data.loc[~data['kommune'].isin(['København', 'Aarhus'])]
        processed_data.append(data_filtered)
    return processed_data
#_________________________________________________________LOADING DATA_______________________________________________________________
files_arb = ['data/i_alt/efter_arbejde2022.csv','data/kvinder/efter_arbejde2022.csv','data/mænd/efter_arbejde2022.csv']
files_bo = ['data/i_alt/efter_bopæl2022.csv','data/kvinder/efter_bopæl2022.csv','data/mænd/efter_bopæl2022.csv']

# Load and process 'Beskæftigede' datasets
segment_efterArbejde = load_and_process_data(files_arb, delimiter=',') #Beskæftigede (ultimo november) efter arbejdsområde, socioøkonomisk status, køn og pendlingsafstand
segment_data_bopæl = load_and_process_data(files_bo, delimiter=';') #Beskæftigede (ultimo november) efter bopælsområde, socioøkonomisk status, køn og pendlingsafstand

#beskæftigede i alt efter år --> til histogram
data = pd.read_csv('data/beskæftigede_i_alt.csv', delimiter=';', encoding='latin-1')

#Beskæftigede (ultimo november) efter køn, tid, arbejdsstedsområde og pendlingsafstand
i_alt_km = pd.read_csv('data/km_ialt.csv', delimiter=',', encoding='latin-1')
kvinder_km = pd.read_csv('data/km_kvinder.csv', delimiter=',', encoding='latin-1')
mænd_km = pd.read_csv('data/km_men.csv', delimiter=',', encoding='latin-1')
#manually adding columns for visualising 
i_alt_km['id'] = [3,4,2,1,0] 
kvinder_km = kvinder_km.assign(køn=['kvinder', 'kvinder', 'kvinder', 'kvinder', 'kvinder'])
mænd_km = mænd_km.assign(køn=['mænd', 'mænd', 'mænd', 'mænd', 'mænd'])

#arbejdsåmråde
arbejdsområde_kommune = pd.read_csv('data/beskæftigedeEfterArbejdsområde.csv', delimiter=';', encoding='utf-8')

result = pd.concat([kvinder_km, mænd_km])

#histogram graph
i_alt = pd.read_csv('data/i_alt.csv', delimiter=';', encoding='utf-8')
kvinder = pd.read_csv('data/kvinder.csv', delimiter=';', encoding='utf-8')
mænd = pd.read_csv('data/mænd.csv', delimiter=';', encoding='utf-8')

data_dict = {'i alt': i_alt, 'kvinder': kvinder, 'mænd': mænd}

y_max = mænd.max()[1]
y_min = kvinder.min()

#variables 
options= ['I alt', '5-10 km', '20-30 km', '30-40 km', '40-50 km', 'Over 50 km']

#status barplot
status_df = pd.read_csv('data/i_alt/afstandIFTstatus2022.csv', delimiter=',', encoding='utf-8')
status_df = status_df.drop([0, 1, 2,3])
df_total = status_df[status_df['afstand'] != 'total']

# Melt the DataFrame to long format for Plotly Express
melted_df = df_total.melt(id_vars=['afstand'], var_name='Status', value_name='Count')

# Plot with Plotly Express as a stacked bar chart
status_fig = px.bar(melted_df, x='Status', y='Count', color='afstand',
             title="Beskæftigede efter socioøkonomisk status",
             labels={'Count': 'Antal', 'Status': 'Socioøkonomisk status'},
             text='Count',  # Show counts on bars
             color_discrete_sequence=px.colors.qualitative.Plotly)

# Load GeoJSON files
with open("data/simplified_geojson_file.geojson") as f:
    kommune_geojson = json.load(f)

with open("data/regioner-geojson-wgs84.json") as f:
    regioner_geojson = json.load(f)

segment_data = {
    "arbejde": [pd.read_csv('data/i_alt/efter_arbejde2022.csv'), pd.read_csv('data/kvinder/efter_arbejde2022.csv'), pd.read_csv('data/mænd/efter_arbejde2022.csv')],  # Replace with actual DataFrames
    "bopæl": [pd.read_csv('data/i_alt/efter_bopæl2022.csv'), pd.read_csv('data/kvinder/efter_bopæl2022.csv'), pd.read_csv('data/mænd/efter_bopæl2022.csv')],
}

# Initialize the app
app = Dash(__name__)

# Layout
app.layout = html.Div([
    html.H1('Erhvervspendling', style={'margin': 'auto', 'padding': '20px'}),
    html.H3('Beskæftigede efter pendlingsafstand og socioøkonomisk status'),
    dcc.Dropdown(
        id='data_dropdown',
        options=[
            {"label": "I alt", "value": "I alt"},
            {"label": "Kvinder", "value": "Kvinder"},
            {"label": "Mænd", "value": "Mænd"}
        ],
        value='I alt',
        style={'width': '200px'}
    ),
    dcc.Dropdown(
        id='afstand_dropdown',
        options=[
            {'label': 'I alt', 'value': 'I alt'},
            {'label': 'Ingen pendling', 'value': 'Ingen pendling'},
            {'label': 'Indtil 5 km', 'value': 'Indtil 5 km'},
            {'label': '10-20 km', 'value': '10-20 km'},
            {'label': '20-30 km', 'value': '20-30 km'},
            {'label': 'Over 50 km', 'value': 'Over 50 km'}
        ],
        value='I alt',
        style={'width': '200px'}
    ),
    dcc.Graph(id='map_graph', style={'padding': '20px'}),
    html.Div([
        html.H3('Histogram over pendlingsafstand'),
        dcc.Dropdown(
            id='histogram_dropdown',
            options=[
                {"label": "I alt", "value": "I alt"},
                {"label": "Kvinder", "value": "Kvinder"},
                {"label": "Mænd", "value": "Mænd"}
            ],
            value='I alt',
            style={'width': '200px'}
        ),
        dcc.Graph(id='histogram_graph', style={'padding': '20px'})
    ])
    ])

# Callbacks
@app.callback(
    Output('map_graph', 'figure'),
    [Input('data_dropdown', 'value'), Input('afstand_dropdown', 'value')]
)
def update_map(selected_gender, selected_distance):
    # Dynamically select dataset based on inputs
    gender_index = {"I alt": 0, "Kvinder": 1, "Mænd": 2}[selected_gender]
    data = segment_data['arbejde'][gender_index]
    
    # Create the choropleth map
    fig = px.choropleth_mapbox(
        data,
        geojson=kommune_geojson,
        locations="kommune",
        featureidkey="properties.navn",
        color=selected_distance,
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": 56.2639, "lon": 9.5018},
        zoom=6,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
