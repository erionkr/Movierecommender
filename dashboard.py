import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import no_update 
import pandas as pd
from recommendation import MovieRecommender  # Angenommen, diese Datei implementiert Empfehlungsalgorithmen
import data_visualisation as dv  # Angenommen, diese Datei implementiert Visualisierungsfunktionen
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import math
import json  # Für die Konvertierung zwischen Listen/Dictionaries und JSON-Strings

PAGE_SIZE = 5

# Initialisieren der MovieRecommender Instanz und Daten laden
movie_recommender = MovieRecommender('df_stream.csv')
movie_recommender.fit()

df = dv.MovieRecommenderViz.load_and_prepare_data('df_stream.csv')

def clean_genre(genre_str):
    return genre_str.strip("[]").replace("'", "").split(', ') if isinstance(genre_str, str) else []

df['genres'] = df['genres'].apply(clean_genre)
unique_genres = set(genre for sublist in df['genres'] for genre in sublist)

# Initialisierung der Dash-App, Bootstrap-Thema anpassen
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])  # Verwendung eines anderen Bootstrap-Themas für eine neue Optik

# Definieren des App-Layouts
app.layout = html.Div([
    dcc.Markdown('''
        ```css
        .Select-control {
            background-color: lightblue;
        }

        .Select--single > .Select-control .Select-value, .Select-placeholder {
            color: white;
        }
        ```
    ''', style={'display': 'none'}),
   html.H1("JELF's CineScope",
                style={'textAlign': 'center', 'color': '#87CEEB', 'fontSize': '48px', 'fontWeight': 'bold', 'marginBottom': '5px'}),
        html.H2('Entdecke Deine nächsten Filmfavoriten',
                style={'textAlign': 'center', 'color': '#ADD8E6', 'fontSize': '24px', 'fontWeight': 'lighter', 'marginTop': '5px'}),
        html.P("Lass dich von Fabian, Loan, Janine und Erion durch ein Meer von unentdeckten Schätzen und Blockbuster-Hits navigieren",
               style={'textAlign': 'center', 'color': 'white', 'fontSize': '18px', 'margin': '20px 0'}),
    dbc.Row([
        dbc.Col([
            dcc.Input(id='movie-title-input', type='text', placeholder='Geben Sie einen Filmtitel ein', debounce=True, className='mb-2 form-control'),
            html.Button('Empfehlungen finden', id='find-recommendations-button', n_clicks=0, className='btn btn-info me-2'),
        ], width=12),
    ], className='mb-3'),
    
    html.Div(id='title-recommendations-output', className='mb-3'),
    
    # Genre-, Jahr- und Bewertungsauswahl mit verbessertem Layout
    dbc.Row([
        dbc.Col([
             html.H4('Genre auswählen', style={'color': 'lightblue'}),  # Beispiel für eine Farbanpassung der Überschrift
            dcc.Dropdown(id='genre-dropdown', options=[{'label': genre, 'value': genre} for genre in unique_genres], multi=True, placeholder='Wählen Sie ein Genre', className='dropdown', ),
        ], md=4),
        dbc.Col([
            html.H4('Veröffentlichungsjahr', style={'color': 'lightblue'}),  # Anpassen der Überschriftfarbe
            dcc.RangeSlider(id='year-slider', min=df['release_year'].min(), max=df['release_year'].max(), value=[df['release_year'].min(), df['release_year'].max()], marks={str(year): {'label': str(year), 'style': {'color': 'white'}} for year in range(df['release_year'].min(), df['release_year'].max()+1, 10)}, step=1),
        ], md=4),
        dbc.Col([
            html.H4('IMDb-Bewertung', style={'color': 'lightblue'}),  # Anpassen der Überschriftfarbe
            dcc.Slider(id='rating-slider', min=0, max=10, step=0.1, value=5, marks={str(i): {'label': str(i), 'style': {'color': 'white'}} for i in range(0, 11)}),
        ], md=4),
    ], className='mb-3'),
    
    html.Div(id='foreign-perc-output'),
    dcc.Store(id='last-action-store', storage_type='session'),
    dcc.Store(id='stored-recommendations'),

    dbc.Row([
        dbc.Col([
            html.H4('Streaming-Dienst auswählen'),
            dcc.Dropdown(id='streaming-service-dropdown', options=[{'label': service, 'value': service} for service in df['streaming_service'].unique()], placeholder='Wählen Sie einen Streaming-Dienst'),
        ], md=6),
        dbc.Col([
            html.Button('Suche starten', id='submit-filter-button', n_clicks=0, className='btn btn-primary mt-4'),  # Button-Stil anpassen
            html.Button('Suche zurücksetzen', id='reset-button', n_clicks=0, className='btn btn-secondary mt-4 ml-2'),  # Button-Stil anpassen
        ], md=6),
    ], className='mb-3'),
    
    html.Div(id='filter-recommendations-output', className='mb-3'),
    
    dcc.Dropdown(
        id='analysis-selector',
        options=[
            {'label': 'Prozentuale Verteilung von ausländischen Filmen', 'value': 'foreign_perc'},
            {'label': 'KDE Plots für verschiedene Streaming-Dienste', 'value': 'kde_plots'},
            {'label': 'Top Budget Filme', 'value': 'budget_visualizations'}
        ],
        placeholder='Wähle eine Analyse',
        className='mb-3'
    ),
    
    html.Div(id='analysis-output', className='mb-3'),
    
    html.Div(id='page-content'),  # Container für Filmempfehlungen
    dbc.Pagination(id="pagination", max_value=1, active_page=1, size="sm", style={'marginTop': 30, 'marginBottom': '20px'}),  # Pagination-Stil anpassen
], style={'textAlign': 'center', 'width': '80%', 'height': '100vh', 'minHeight': '100vh', 'margin': '0 auto', 'padding': '20px', 'backgroundImage': 'url(https://repository-images.githubusercontent.com/275336521/20d38e00-6634-11eb-9d1f-6a5232d0f84f)', 'backgroundSize': 'cover', 'backgroundPosition': 'center center', 'color': '#f8f9fa'})

# Callbacks und Logik für die Interaktion hier hinzufügen...

@app.callback(
    [Output('movie-title-input', 'value'),
     Output('title-recommendations-output', 'children'),
     Output('filter-recommendations-output', 'children'),
     Output('stored-recommendations', 'data'),
     Output('genre-dropdown', 'value'),
     Output('year-slider', 'value'),
     Output('rating-slider', 'value'),
     Output('streaming-service-dropdown', 'value'),
     Output('pagination', 'active_page'),
     Output('pagination', 'max_value')],
    [Input('reset-button', 'n_clicks'),
     Input('submit-filter-button', 'n_clicks'),
     Input('find-recommendations-button', 'n_clicks')],
    [State('genre-dropdown', 'value'),
     State('year-slider', 'value'),
     State('rating-slider', 'value'),
     State('streaming-service-dropdown', 'value'),
     State('movie-title-input', 'value'),
     State('last-action-store', 'data')]
)
def update_outputs(reset_clicks, filter_clicks, find_clicks, genres, year_range, rating, service, movie_title, last_action_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'reset-button':
        empty_df = pd.DataFrame(columns=['title', 'description'])  # Füge hier alle notwendigen Spalten hinzu
        # Konvertiere das leere DataFrame in das 'split' JSON-Format
        empty_df_json = empty_df.to_json(date_format='iso', orient='split')
        return ('',  # Leere das Texteingabefeld
                [],  # Leere die Titel-Empfehlungen
                [],  # Leere die Filter-Empfehlungen
                empty_df_json,  # Leere die gespeicherten Empfehlungen, aber im korrekten Format
                [],  # Setze die Genres zurück
                [df['release_year'].min(), df['release_year'].max()],  # Setze das Veröffentlichungsjahr zurück
                5,  # Setze die IMDb-Bewertung zurück
                None,  # Setze den Streaming-Service zurück
                1,  # Setze die aktive Seite zurück
                1  # Setze die maximale Seitenzahl zurück
            )


    elif button_id == 'submit-filter-button':
        filtered_df = df.copy()
        if genres:
            filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: any(g in genres for g in x))]
        if year_range:
            filtered_df = filtered_df[(filtered_df['release_year'] >= year_range[0]) & (filtered_df['release_year'] <= year_range[1])]
        if rating:
            filtered_df = filtered_df[filtered_df['imdb_score'] >= rating]
        if service:
            filtered_df = filtered_df[filtered_df['streaming_service'] == service]

        if filtered_df.empty:
            return no_update, no_update, 'Keine Filme gefunden, die den Kriterien entsprechen.', None, no_update, no_update, no_update, no_update, no_update, no_update
        else:
            recommendations_json = filtered_df.to_json(date_format='iso', orient='split')
            total_pages = math.ceil(len(filtered_df) / PAGE_SIZE)
            return no_update, no_update, no_update, recommendations_json, no_update, no_update, no_update, no_update, 1, total_pages
    elif button_id == 'find-recommendations-button':
        recommendations = movie_recommender.recommend(movie_title)
        if recommendations.empty:
            return no_update, 'Keine Empfehlungen gefunden.', no_update, None, no_update, no_update, no_update, no_update, 1, no_update
        else:
            recommendations_json = recommendations.to_json(date_format='iso', orient='split')
            total_pages = math.ceil(len(recommendations) / PAGE_SIZE)
            return no_update, no_update, no_update, recommendations_json, no_update, no_update, no_update, no_update, 1, total_pages
    else:
        raise PreventUpdate
    
@app.callback(
    Output('analysis-output', 'children'),
    [Input('analysis-selector', 'value')]
)
def update_analysis(selected_analysis):
    if selected_analysis == 'foreign_perc':
        fig = dv.MovieRecommenderViz.calculate_foreign_perc(df)
        return dcc.Graph(figure=fig)
    elif selected_analysis == 'kde_plots':
        fig = dv.MovieRecommenderViz.plot_kde_plots(df)
        return dcc.Graph(figure=fig)
    elif selected_analysis == 'budget_visualizations':
        fig = dv.MovieRecommenderViz.plot_budget_visualizations(df)
        return dcc.Graph(figure=fig)
    return html.Div()

def generate_movie_tiles(data):
    """Generieren der Filmkacheln basierend auf den Filmempfehlungen."""
    tiles = []
    for _, row in data.iterrows():
        card = dbc.Card(
            dbc.CardBody([
                html.H5(row['title'], className='card-title'),
                html.P(row['description'], className='card-text'),
            ]),
            style={'margin': '10px', 'flex': '1 0 18%'}  # Angepasster Stil für Flexbox-Layout
        )
        tiles.append(dbc.Col(card, md=2))  # Angepasste Spaltenbreite für 5 Kacheln pro Zeile
    return html.Div(tiles, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})

@app.callback(
    Output('page-content', 'children'),
    [Input('pagination', 'active_page'), Input('stored-recommendations', 'data')]
)
def update_page_content_and_pagination(active_page, stored_data):
    if stored_data is None or stored_data == json.dumps([]):  # Überprüfe, ob die Daten leer sind
        raise dash.exceptions.PreventUpdate
    
    recommendations = pd.read_json(stored_data, orient='split')
    total_pages = math.ceil(len(recommendations) / PAGE_SIZE)
    start_index = (active_page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    page_data = recommendations.iloc[start_index:end_index]

    # Generieren der Filmkacheln für die aktuelle Seite
    tiles = generate_movie_tiles(page_data)

    return tiles, total_pages


if __name__ == '__main__':
    app.run_server(debug=True)