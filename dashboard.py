import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import pandas as pd
from recommendation import MovieRecommender
import data_visualisation as dv
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

# Initialisieren der MovieRecommender Instanz und Daten laden
movie_recommender = MovieRecommender('df_stream.csv')
movie_recommender.fit()

df = dv.MovieRecommenderViz.load_and_prepare_data('df_stream.csv')

def clean_genre(genre_str):
    return genre_str.strip("[]").replace("'", "").split(', ') if isinstance(genre_str, str) else []

df['genres'] = df['genres'].apply(clean_genre)
unique_genres = set(genre for sublist in df['genres'] for genre in sublist)

# Initialisierung der Dash-App
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Anzahl der Filme pro Seite
PAGE_SIZE = 5

# Seitenleiste für die Paginierung
max_value = (len(df) - 1) // PAGE_SIZE + 1
pagination = dbc.Pagination(id="pagination", size="sm", max_value=max_value, style={'margin-top': '10px'})

# Definieren des App-Layouts
app.layout = html.Div([
    html.H1('Filmempfehlungs-Dashboard'),
    dcc.Input(id='movie-title-input', type='text', placeholder='Geben Sie einen Filmtitel ein'),
    html.Button('Empfehlungen finden', id='find-recommendations-button', n_clicks=0),
    html.Div(id='title-recommendations-output'),

    html.H4('Genre auswählen'),
    dcc.Dropdown(id='genre-dropdown', options=[{'label': genre, 'value': genre} for genre in unique_genres], multi=True, placeholder='Wählen Sie ein Genre'),
    
    html.H4('Veröffentlichungsjahr'),
    dcc.RangeSlider(id='year-slider', min=df['release_year'].min(), max=df['release_year'].max(), value=[df['release_year'].min(), df['release_year'].max()], marks={str(year): str(year) for year in range(df['release_year'].min(), df['release_year'].max()+1, 10)}, step=1),
    
    html.H4('IMDb-Bewertung'),
    dcc.Slider(id='rating-slider', min=0, max=10, step=0.1, value=5, marks={str(i): str(i) for i in range(0, 11)}),
    
    html.H4('Streaming-Dienst auswählen'),
    dcc.Dropdown(id='streaming-service-dropdown', options=[{'label': service, 'value': service} for service in df['streaming_service'].unique()], placeholder='Wählen Sie einen Streaming-Dienst'),
    
    html.Button('Suche starten', id='submit-filter-button', n_clicks=0),
    html.Button('Suche zurücksetzen', id='reset-button', n_clicks=0),
    html.Div(id='filter-recommendations-output'),
    dcc.Dropdown(
        id='analysis-selector',
        options=[
            {'label': 'Prozentuale Verteilung von ausländischen Filmen', 'value': 'foreign_perc'},
            {'label': 'KDE Plots für verschiedene Streaming-Dienste', 'value': 'kde_plots'},
            {'label': 'Top Budget Filme', 'value': 'budget_visualizations'}
        ],
        placeholder='Wähle eine Analyse'
    ),
    html.Div(id='analysis-output'),
    html.Button('Berechne ausländische Prozentanteile', id='calculate-foreign-perc-button', n_clicks=0),
    html.Div(id='foreign-perc-output'),
    
    # Seitenleiste für die Paginierung
    pagination,
    html.Div(id='page-content')
], style={'textAlign': 'center', 'width': '80%', 'margin': 'auto'})

@app.callback(
    [Output('movie-title-input', 'value'),
     Output('title-recommendations-output', 'children'),
     Output('filter-recommendations-output', 'children')],
    [Input('reset-button', 'n_clicks'),
     Input('submit-filter-button', 'n_clicks'),
     Input('find-recommendations-button', 'n_clicks')],
    [State('genre-dropdown', 'value'),
     State('year-slider', 'value'),
     State('rating-slider', 'value'),
     State('streaming-service-dropdown', 'value'),
     State('movie-title-input', 'value')]
)
def update_outputs(reset_clicks, filter_clicks, find_clicks, genres, year_range, rating, service, movie_title):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise PreventUpdate
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'reset-button':
        return '', None, None
    elif button_id == 'submit-filter-button':
        filtered_df = df.copy()
        if genres:
            filtered_df = filtered_df[filtered_df['genres'].apply(lambda x: any(g in genres for g in x))]
        if year_range:
            filtered_df = filtered_df[(filtered_df['release_year'] >= year_range[0]) & (filtered_df['release_year'] <= year_range[1])]
        if rating:
            filtered_df = filtered_df[filtered_df['imdb_score'] >= rating]  # 'imdb_score' anstelle von 'rating'
        if service:
            filtered_df = filtered_df[filtered_df['streaming_service'] == service]
        if filtered_df.empty:
            return dash.no_update, dash.no_update, 'Keine Filme gefunden, die den Kriterien entsprechen.'
        else:
            return dash.no_update, dash.no_update, generate_movie_tiles(filtered_df)
    elif button_id == 'find-recommendations-button':
        if not movie_title:
            raise PreventUpdate
        recommendations = movie_recommender.recommend(movie_title)
        if recommendations.empty:
            return dash.no_update, 'Keine Empfehlungen gefunden.', dash.no_update
        else:
            return '', generate_movie_tiles(recommendations), dash.no_update
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
    return html.Div('Bitte wähle eine Analyse.')

@app.callback(
    Output('foreign-perc-output', 'children'),
    [Input('calculate-foreign-perc-button', 'n_clicks')]
)
def update_foreign_perc(n_clicks):
    if n_clicks > 0:
        df = dv.MovieRecommenderViz.load_and_prepare_data('df_stream.csv')
        foreign_perc = dv.MovieRecommenderViz.calculate_foreign_perc(df)
        fig = go.Figure(data=[
            go.Bar(
                x=foreign_perc['streaming_service'],
                y=foreign_perc['Perc'],
                text=foreign_perc['Perc'],
                textposition='auto',
            )
        ])
        fig.update_layout(title='Prozentuale Verteilung von ausländischen Filmen', xaxis_title='Streaming-Dienst', yaxis_title='Prozent')
        
        return dcc.Graph(figure=fig)

def generate_movie_tiles(movies_df):
    movie_tiles = []
    for _, movie in movies_df.iterrows():
        movie_tile = dbc.Card(
            dbc.CardBody(
                [
                    html.H5(movie["title"], className="card-title"),
                    html.P(movie["description"], className="card-text"),
                ]
            ),
            style={"width": "18rem"},  # Kartenbreite
        )
        movie_tiles.append(html.Div(movie_tile))
    return movie_tiles


@app.callback(
    Output('page-content', 'children'),
    [Input('pagination', 'active_page')],
    [State('filter-recommendations-output', 'children')]
)
def update_page(active_page, recommendations):
    if recommendations is None:
        return None
    start_idx = (active_page - 1) * PAGE_SIZE
    end_idx = active_page * PAGE_SIZE
    movies_on_page = recommendations[start_idx:end_idx]  # Correctly paginate the data
    return generate_movie_tiles(movies_on_page)

@app.callback(
    Output('pagination', 'max_value'),
    [Input('filter-recommendations-output', 'children')]
)
def update_pagination_max_value(recommendations):
    if recommendations is None:
        return 1
    num_pages = (len(recommendations) - 1) // PAGE_SIZE + 1
    return num_pages

if __name__ == '__main__':
    app.run_server(debug=True)
