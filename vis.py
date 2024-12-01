import subprocess
import os
import sys

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

from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import geopandas as gpd

#Beskæftigede (ultimo november) efter arbejdsområde, socioøkonomisk status, køn og pendlingsafstand
i_alt_arb = pd.read_csv('data/i_alt/efter_arbejde2022.csv', delimiter=',', encoding='utf-8')
kvinder_arb = pd.read_csv('data/kvinder/efter_arbejde2022.csv', delimiter=',', encoding='utf-8')
mænd_arb = pd.read_csv('data/mænd/efter_arbejde2022.csv', delimiter=',', encoding='utf-8')
segment_data = []
for i in [i_alt_arb,kvinder_arb,mænd_arb]:
    i = i.loc[(i['kommune'] != 'København') & (i['kommune'] != 'Aarhus')]
    segment_data.append(i)

#Beskæftigede (ultimo november) efter bopælsområde, socioøkonomisk status, køn og pendlingsafstand
i_alt_bo = pd.read_csv('data/i_alt/efter_bopæl2022.csv', delimiter=';', encoding='utf-8')
kvinder_bo = pd.read_csv('data/kvinder/efter_bopæl2022.csv', delimiter=';', encoding='utf-8')
mænd_bo = pd.read_csv('data/mænd/efter_bopæl2022.csv', delimiter=';', encoding='utf-8')
segment_data_bopæl = []
for i in [i_alt_bo,kvinder_bo,mænd_bo]:
    i = i.loc[(i['kommune'] != 'København') & (i['kommune'] != 'Aarhus')]
    segment_data_bopæl.append(i)

data = pd.read_csv('data/beskæftigede_i_alt.csv', delimiter=';', encoding='latin-1')
#Beskæftigede (ultimo november) efter køn, tid, arbejdsstedsområde og pendlingsafstand
i_alt_km = pd.read_csv('data/km_ialt.csv', delimiter=',', encoding='latin-1')
kvinder_km = pd.read_csv('data/km_kvinder.csv', delimiter=',', encoding='latin-1')
mænd_km = pd.read_csv('data/km_men.csv', delimiter=',', encoding='latin-1')

i_alt_km['id'] = [3,4,2,1,0]
i_alt_km

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

# Load GeoJSON file
with open("data/simplified_geojson_file.geojson") as f:
    kommune_geojson = json.load(f)

with open("data/regioner-geojson-wgs84.json") as f:
    regioner_geojson = json.load(f)

app = Dash(__name__)

app.layout = html.Div([
    html.H1('Erhvervspendling', style={'margin': 'auto', 'padding':'20px'}),
    html.H3('Beskæftigede efter pendlingsafstand og socioøkonomisk status'),
    dcc.Graph(figure=status_fig),

    html.H3('Antal beskæftigede efter regioner og afstand'),
    dcc.Dropdown(
        id='data_dropdown',
        options= options,
        value='I alt',  # Default value for Map 2
        style={'width': '200px'}
    ),
    dcc.Graph(id='map_graph', style={'padding':'20px'}),

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
            dcc.Graph(id='histogram')
        ])
])

@app.callback(
    Output('histogram', 'figure'),
    Input('histogram_dropdown', 'value')
)

def histogram(segment):
    data = data_dict[segment]
    years = [i for i in data['år']]
    hele_landet = [i for i in data['Hele landet']]
    region_hovedstaden = [i for i in data['Region Hovedstaden']]
    region_sjaelland = [i for i in data['Region Sjælland']]
    region_syddanmark = [i for i in data['Region Syddanmark']]
    region_midtjylland = [i for i in data['Region Midtjylland']]
    region_nordjylland = [i for i in data['Region Nordjylland']]
    fig = go.Figure()

    # Adding each region's data as a line
    fig.add_trace(go.Scatter(x=years, y=hele_landet, mode='lines', name='Hele landet'))
    fig.add_trace(go.Scatter(x=years, y=region_hovedstaden, mode='lines', name='Region Hovedstaden'))
    fig.add_trace(go.Scatter(x=years, y=region_sjaelland, mode='lines', name='Region Sjælland'))
    fig.add_trace(go.Scatter(x=years, y=region_syddanmark, mode='lines', name='Region Syddanmark'))
    fig.add_trace(go.Scatter(x=years, y=region_midtjylland, mode='lines', name='Region Midtjylland'))
    fig.add_trace(go.Scatter(x=years, y=region_nordjylland, mode='lines', name='Region Nordjylland'))

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

def update_kommune_map(data, afstand_km, segment):
    fig = px.choropleth_mapbox(
        segment_data_bopæl[segment],
        geojson=data,
        locations="kommune",     # This is the column in your data with kommune IDs
        featureidkey='properties.navn',  # This should match the ID key in your GeoJSON
        color=afstand_km,       # Optional: hover info
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": 56.2639, "lon": 9.5018},  # Center on Denmark
        zoom=6,
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

def update_kommune_map(data, afstand_km, segment):
    fig = px.choropleth_mapbox(
        segment_data[segment],
        geojson=data,
        locations="kommune",     # This is the column in your data with kommune IDs
        featureidkey='properties.navn',  # This should match the ID key in your GeoJSON
        color=afstand_km,       # Optional: hover info
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": 56.2639, "lon": 9.5018},  # Center on Denmark
        zoom=6,
        )

    fig.update_layout(
        title="Danish Municipality Data",
        margin={"r":0,"t":0,"l":0,"b":0}
    )
    return fig

# Callback to update map based on dropdown selection
@app.callback(
    Output('map_graph', 'figure'),
    [Input('data_dropdown', 'value')]
)
def update_map(selected_data):
    # Create a choropleth map with the selected data column
    fig_map = px.choropleth_mapbox(
        i_alt_km,
        geojson=regioner_geojson,
        locations="id",
        featureidkey="id",
        color=selected_data,
        hover_name="region",
        color_continuous_scale="Viridis",
        mapbox_style="carto-positron",
        center={"lat": 56.2639, "lon": 9.5018},
        zoom=6,
    )

    fig_map.update_layout(
        title="Danish Municipality Data",
        margin={"r":0,"t":0,"l":0,"b":0}
    )

    return fig_map

if __name__ == '__main__':
    app.run_server(debug=True)