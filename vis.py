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
# Calculate percentages
melted_df['Total'] = melted_df.groupby('Status')['Count'].transform('sum')  # Total count per Status
melted_df['Percentage'] = (melted_df['Count'] / melted_df['Total']) * 100  # Percent calculation
melted_df['Percentage_Text'] = melted_df['Percentage'].apply(lambda x: f"{x:.1f}%")  # Format for display
print(melted_df)


# Plot with Plotly Express as a stacked bar chart
status_fig = px.bar(melted_df, x='Status', y='Count', color='afstand',
             title="Beskæftigede efter socioøkonomisk status",
             labels={'Count': 'Antal', 'Status': 'Socioøkonomisk status'},
             text='Percentage_Text',  # Show counts on bars
             color_discrete_sequence=px.colors.qualitative.Plotly,
            hover_data={
                    'Status':False,
                    'Count': True,             # Show raw counts
                    'Percentage': ':.2f',      # Show percentage with 2 decimal points
                    'Total': False,            # Exclude total from hover
                    'Percentage_Text': False   # Exclude the formatted percentage text
                })

# Load GeoJSON files
with open("data/simplified_geojson_file.geojson") as f:
    kommune_geojson = json.load(f)

with open("data/regioner-geojson-wgs84.json") as f:
    regioner_geojson = json.load(f)

#_____________________________________________________________________DASH APP________________________________________________________________
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Nutidsbillede af erhvervspendling', style={'margin': 'auto', 'padding':'20px'}),
    html.H3('Beskæftigede efter pendlingsafstand og socioøkonomisk status'),
    dcc.Graph(figure=status_fig),

    html.Div([
        html.H3('Antal beskæftigede efter arbejdsstedsområde, køn, tid og pendlingsafstand'),
        html.P('Viser antallet af personer, der pendler til (og fra) deres arbejdssted efter pendlingsafstand i km og kommune'),
        dcc.Store(id='kommune_data', data=kommune_geojson),
        dcc.Dropdown(
            id='afstand_km',
            options= options,
            value='I alt',  # Default value for Map 
            style={'width': '120px'} 
        ),
        dcc.Dropdown(
            id='segment',
            options = [
                {"label": "I alt", "value": 0},
                {"label": "Kvinder", "value": 1},
                {"label": "Mænd", "value": 2}
            ],
            value=0,  # Default value for Map 
            style={'width': '120px'} 
        ),
        dcc.Graph(id='arbejdsområdeIKm_graph')
        ],
        style={'width': '43%', 'display': 'inline-block', 'padding': '20px'}),
        html.Div([
        html.H3('Antal beskæftigede efter bopælsområde, køn, tid og pendlingsafstand'),
        html.P('Viser antallet af personer, der pendler fra (og til) deres hjem efter pendlingsafstand i km og kommune'),
        dcc.Dropdown(
            id='afstand_km_bopæl',
            options= ['I alt', 'Ingen pendling', 'Indtil 5 km', '5-10 km','10-20 km','20-30 km','30-40 km','40-50 km','Over 50 km','Ikke beregnet'],
            value='I alt',  # Default value for Map 
            style={'width': '120px'} 
        ),
        dcc.Dropdown(
            id='segment_bopæl',
            options = [
                {"label": "I alt", "value": 0},
                {"label": "Kvinder", "value": 1},
                {"label": "Mænd", "value": 2}
            ],
            value=0,  # Default value for Map,
            style={'width': '120px'} 
        ),
        dcc.Graph(id='bopælsområdeIKm_graph')
        ],
        style={'width': '43%', 'display': 'inline-block', 'padding': '20px', 'float':'right'}),
        html.Div([
            html.H3('Histogram'),
            dcc.Dropdown(id='histogram_dropdown',
                         options = [
                            {"label": "i alt", "value": "i alt"},
                            {"label": "kvinder", "value": "kvinder"},
                            {"label": "mænd", "value": "mænd"}
                        ], value="i alt",  # Default value for Map,
                        style={'width': '120px'} ),
            dcc.Graph(id='histogram')]),

        html.Div(
            html.H1('Nutidsbillede af flytransport', style={'margin': 'auto', 'padding':'20px'}),
            
        )
]),

#____________________________________________________________CALLBACKS_________________________________________________________________
@app.callback(
    Output('histogram', 'figure'),
    Input('histogram_dropdown', 'value')
)

def histogram(segment):
    data = data_dict[segment]
    years = [i for i in data['år']]
    filtered_data = {
    'hele landet' : [i for i in data['Hele landet']],
    'region hovedstaden' : [i for i in data['Region Hovedstaden']],
    'region sjaelland' : [i for i in data['Region Sjælland']],
    'region syddanmark' : [i for i in data['Region Syddanmark']],
    'region midtjylland' : [i for i in data['Region Midtjylland']],
    'region nordjylland' : [i for i in data['Region Nordjylland']]}
    fig = go.Figure()

    for key, value in filtered_data.items():
        fig.add_trace(go.Scatter(x=years, y=value, mode='lines', name=key))

    # Update layout
    fig.update_layout(
        title=f"Udvikling i pendlingsafstand ({segment})",
        xaxis_title="År",
        yaxis_title="Afstand i km",
        template="ggplot2"
    )
    return fig

# Callback to update map based on dropdown selection
@app.callback(
    Output('bopælsområdeIKm_graph', 'figure'),
    [Input('kommune_data', 'data'), Input('afstand_km_bopæl', 'value'), Input('segment_bopæl', 'value')]
)

def kommune_map_bopæl(data, afstand_km, segment):
    fig = px.choropleth_mapbox(
        segment_data_bopæl[segment],
        geojson=data,
        locations="kommune",     # This is the column in your data with kommune IDs
        featureidkey='properties.navn',  # This should match the ID key in your GeoJSON
        color=afstand_km,       # Optional: hover info
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": 56.2639, "lon": 9.5018},  # Center on Denmark
        zoom=5.5,
        )

    fig.update_layout(
        title="Danish Municipality Data",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    return fig

# Callback to update map based on dropdown selection
@app.callback(
    Output('arbejdsområdeIKm_graph', 'figure'),
    [Input('kommune_data', 'data'), Input('afstand_km', 'value'), Input('segment', 'value')]
)

def update_kommune_map_arbejde(data, afstand_km, segment):
    fig = px.choropleth_mapbox(
        segment_efterArbejde[segment],
        geojson=data,
        locations="kommune",     # This is the column in your data with kommune IDs
        featureidkey='properties.navn',  # This should match the ID key in your GeoJSON
        color=afstand_km,       # Optional: hover info
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": 56.2639, "lon": 9.5018},  # Center on Denmark
        zoom=5.5,
        )

    fig.update_layout(
        title="Danish Municipality Data",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)