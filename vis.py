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

#STATUS BARPLOT.....
status_df = pd.read_csv('data/i_alt/afstandIFTstatus2022.csv', delimiter=',', encoding='utf-8')
status_df = status_df.drop([0, 1, 2,3])
df_total = status_df[status_df['afstand'] != 'total']

# Melt the DataFrame to long format for Plotly Express
melted_df = df_total.melt(id_vars=['afstand'], var_name='Status', value_name='Count')
# Calculate percentages
melted_df['Total'] = melted_df.groupby('Status')['Count'].transform('sum')  # Total count per Status
melted_df['Percentage'] = (melted_df['Count'] / melted_df['Total']) * 100  # Percent calculation
melted_df['Percentage_Text'] = melted_df['Percentage'].apply(lambda x: f"{x:.1f}%")  # Format for display

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

#JOSON.....
# Load GeoJSON files
with open("data/simplified_geojson_file.geojson") as f:
    kommune_geojson = json.load(f)

with open("data/regioner-geojson-wgs84.json") as f:
    regioner_geojson = json.load(f)

#FLIGHTS MAP......
import pandas as pd
passagertal = pd.read_csv('data/i_alt/passagertal.csv', delimiter=';', encoding='utf-8')
airports = {
    "København": (55.6181, 12.6565),
    "Billund": (55.7403, 9.1522),
    "Aarhus": (56.2990, 10.6190),
    "Aalborg": (57.0928, 9.8494),
    "Karup": (56.3088, 9.1451),
    "Esbjerg": (55.5255, 8.5534),
    "Bornholm": (55.0633, 14.7594),
    "Sønderborg": (54.9642, 9.7913),
    "Roskilde": (55.5851, 12.1289),
    "Thisted": (56.9565, 8.6857),
}
#_____________________________________________________________________DASH APP________________________________________________________________
app = Dash(__name__)

app.layout = html.Div([
    html.H1('Nutidsbillede af erhvervspendling', style={'padding': '10px', 'text-align':'center', 'width': '80%'}),
    html.P('Figuren viser fordelingen af pendlingsafstand i procenter for hver socioøkonomisk status.', style={'padding': '10px', 'width': '80%', 'margin':'auto'}),
    dcc.Graph(figure=status_fig),
    html.H2('Heatmaps', style={'padding': '10px', 'text-align':'center', 'width': '80%'}),
    html.P('Figuren viser to separate heatmaps, der illustrerer antallet af beskæftigede i Danmark baseret på henholdsvis arbejdsstedsområde og bopælsområde. De anvendte data stammer fra Danmarks Statistik og er opgjort efter arbejdsstedets kommune og bopælskommunen, henholdsvis.', style={'padding': '10px', 'width': '80%', 'margin':'auto'}),
    html.Br(),
    html.P('Heatmap for arbejdsstedsområde: Dette viser, hvor mange personer der er beskæftiget i forskellige kommuner, som pendler fra deres arbejde til deres hjem, uden hensyn til hvor deres bopæl ligger. Fordelt på afstand i km.', style={'padding': '10px', 'width': '80%', 'margin':'auto'}),
    html.Br(),
    html.P('Heatmap for bopælsområde: Dette viser antallet af beskæftigede, der bor i forskellige kommuner og pendler fra deres hjem til arbejde, uden hensyn til hvor arbejdsstedet ligger. Fordelt på afstand i km.', style={'padding': '10px', 'width': '80%', 'margin':'auto'}),
    html.Div([
        html.H3('Antal beskæftigede efter arbejdsstedsområde, køn, tid og pendlingsafstand'),
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
        style={'width': '43%', 'display': 'inline-block', 'padding': '20px', 'float':'right', 'margin-left':'20px'}),
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

        html.Div([
            html.H1('Nutidsbillede af flytransport', style={'margin': 'auto', 'padding':'20px'}),
            html.P('Her vises et kort og et diagram for afrejsende passagerer (Enhed : 1.000 personer) på indenrigsruter, med start- og slutdestinationer. Kortet viser ruter, mens Sankey-diagrammet illustrerer fordelingen af afrejsende passagerer til de forskellige destinationer. Du kan vælge den lufthavn, hvor passagererne rejser fra, i menuen nedenfor.', style={'width': '80%', 'display': 'inline-block', 'padding': '20px', 'float':'left'}),
            dcc.RadioItems(
                style={'width': '20%', 'display': 'inline-block', 'padding': '5px', 'float':'left'},
                id='fra_lufthavn', 
                options=passagertal['fra_lufthavn'].unique(),
                value="Fra København"
            ),
            dcc.Graph(
                id='flight_map',
                style={'width': '50%', 'display': 'inline-block', 'padding': '20px', 'float':'right'}),
            dcc.Graph(
                id='flight_sankey',
                style={'width': '40%', 'display': 'inline-block', 'padding': '5px', 'float':'left'})
])
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
        margin={"r":0,"t":0,"l":0,"b":0},
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

@app.callback(
    Output("flight_map", "figure"), 
    Input("fra_lufthavn", "value"))
def display_cflights(lufthavn):
    fig_flight_map = go.Figure()
    passagertal_aktiv = passagertal.loc[(passagertal['fra_lufthavn']==lufthavn) & (passagertal['år']==2023)]
    passagertal_aktiv = passagertal_aktiv.drop(columns=['Til_øvrige_lufthavne'])
    passagertal_aktiv = passagertal_aktiv.dropna(axis='columns')
    print(passagertal_aktiv)
    for column in passagertal_aktiv.iloc[:,2:]: 
        if int(passagertal_aktiv[column]) > 0 :
            fig_flight_map.add_trace(go.Scattermapbox(
                mode = "lines",
                lon=[
                    airports[lufthavn.split(' ')[1]][1],  # Longitude of source airport
                    airports[column.split('_')[1]][1]  # Longitude of destination airport
                ],
                lat=[
                    airports[lufthavn.split(' ')[1]][0],  # Latitude of source airport
                    airports[column.split('_')[1]][0]  # Latitude of destination airport
                ],
                line=dict(
                        width=4,
                        color=px.colors.sequential.Plasma[min(int(passagertal_aktiv[column]) // 50, 9)]  # Adjust scale for color
                    ),
                hoverinfo="text",
                text=f"Passengers: {int(passagertal_aktiv[column].iloc[0])}"))
    fig_flight_map.update_layout(
        mapbox={
            'style': "open-street-map",
            'center': {'lon': 10, 'lat': 56},  # Center over Denmark
            'zoom': 5
        },
        margin={'l': 0, 't': 0, 'b': 0, 'r': 0},
        showlegend=False
    )
    return fig_flight_map

import plotly.graph_objects as go

@app.callback(
    Output("flight_sankey", "figure"),
    Input("fra_lufthavn", "value")
)
def display_sankey(lufthavn):
    # Filter the data for the selected airport and year 2023
    passagertal_aktiv = passagertal.loc[
        (passagertal['fra_lufthavn'] == lufthavn) & (passagertal['år'] == 2023)
    ]
    passagertal_aktiv = passagertal_aktiv.drop(columns=['Til_øvrige_lufthavne']).dropna(axis='columns')

    # Create lists for Sankey diagram nodes and links
    source_airports = [lufthavn.split(' ')[1]]  # Extract the source airport name
    target_airports = [col.split('_')[1] for col in passagertal_aktiv.columns[2:] if col.split('_')[1] in airports]
    traffic_amounts = [int(passagertal_aktiv[col]) for col in passagertal_aktiv.columns[2:] if col.split('_')[1] in airports]

    # Filter out zero traffic amounts
    target_airports = [target for target, traffic in zip(target_airports, traffic_amounts) if traffic > 0]
    traffic_amounts = [traffic for traffic in traffic_amounts if traffic > 0]

    # Combine source and target airports into a single list of nodes
    all_airports = source_airports + target_airports
    airport_indices = {airport: i for i, airport in enumerate(all_airports)}  # Map airports to indices

    # Define Sankey diagram links
    links = {
        "source": [airport_indices[source_airports[0]]] * len(target_airports),
        "target": [airport_indices[airport] for airport in target_airports],
        "value": traffic_amounts
    }

    # Define Sankey diagram nodes
    nodes = {
        "label": all_airports
    }

    # Create the Sankey diagram
    fig_sankey = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=nodes["label"]
        ),
        link=dict(
            source=links["source"],
            target=links["target"],
            value=links["value"]
        )
    ))

    # Update layout
    fig_sankey.update_layout(
        title_text=f"Antal afrejsende fra {lufthavn.split(' ')[1]}",
        font_size=10
    )

    return fig_sankey

if __name__ == '__main__':
    app.run_server(debug=True)