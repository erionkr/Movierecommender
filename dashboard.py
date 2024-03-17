import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash import no_update 
import pandas as pd
from recommendation import MovieRecommender  
import data_visualisation as dv  
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import math
import json  
import sqlite3
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
# Datenbanktabelle erstellen, wenn sie nicht existiert

#def create_users_table():
#    conn = sqlite3.connect('userdata.db')
#    c = conn.cursor()
#    c.execute('''CREATE TABLE IF NOT EXISTS users
#                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
#                  username TEXT UNIQUE,
#                  password TEXT,
#                  favorite_genre TEXT,
#                  favorite_streaming_service TEXT)''')
#    conn.commit()
#    conn.close()


#create_users_table()

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
        html.P("Lassen Sie sich von Fabian, Loan, Janine und Erion durch ein Meer von unentdeckten Schätzen und Blockbuster-Hits navigieren",
               style={'textAlign': 'center', 'color': 'white', 'fontSize': '18px', 'margin': '20px 0'}),
    dcc.Location(id='url', refresh=False),
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H2("Login")),
                    dbc.CardBody([
                        dcc.Input(id='login-username', type='text', placeholder='Username'),
                        dcc.Input(id='login-password', type='password', placeholder='Password'),
                        html.Button('Login', id='auth-button', n_clicks=0, className='mt-3')
                    ])
                ]),
                html.Div(id='auth-feedback', className='mt-3')
            ], width=6),
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H2("Register")),
                    dbc.CardBody([
                        dcc.Input(id='reg-username', type='text', placeholder='Username'),
                        dcc.Input(id='reg-password', type='password', placeholder='Password'),
                        dcc.Dropdown(id='reg-favorite-genre',
                                     options=[{'label': genre, 'value': genre} for genre in unique_genres],
                                     placeholder='Bitte wählen Sie Ihr Lieblingsgenre aus', className='mb-3'),
                        dcc.Dropdown(id='reg-favorite-streaming-service',
                                     options=[{'label': service, 'value': service} for service in df['streaming_service'].unique()],
                                     placeholder='Bitte wählen Sie Ihren Lieblingsstreamingdienst aus', className='mb-3'),
                        html.Button('Register', id='register-button', n_clicks=0, className='mt-3')
                    ])
                ]),
                html.Div(id='reg-feedback', className='mt-3')
            ], width=6)
        ], className='mt-5'),
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Input(id='movie-title-input', type='text', placeholder='Geben Sie einen Filmtitel ein', debounce=True, className='mb-2 form-control'),
            html.Button('Empfehlungen finden', id='find-recommendations-button', n_clicks=0, className='btn btn-info me-2'),
        ], width=12),
    ], className='mb-3'),
    
    html.Div(id='title-recommendations-output', className='mb-3'),
    

    dbc.Row([
        dbc.Col([
             html.H4('Genre auswählen', style={'color': 'lightblue'}),  
            dcc.Dropdown(id='genre-dropdown', options=[{'label': genre, 'value': genre} for genre in unique_genres], multi=True, placeholder='Bitte wählen Sie ein Genre aus', className='dropdown', ),
        ], md=4),
        dbc.Col([
            html.H4('Veröffentlichungsjahr', style={'color': 'lightblue'}),  
            dcc.RangeSlider(id='year-slider', min=df['release_year'].min(), max=df['release_year'].max(), value=[df['release_year'].min(), df['release_year'].max()], marks={str(year): {'label': str(year), 'style': {'color': 'white'}} for year in range(df['release_year'].min(), df['release_year'].max()+1, 10)}, step=1),
        ], md=4),
        dbc.Col([
            html.H4('IMDb-Bewertung', style={'color': 'lightblue'}), 
            dcc.Slider(id='rating-slider', min=0, max=10, step=0.1, value=5, marks={str(i): {'label': str(i), 'style': {'color': 'white'}} for i in range(0, 11)}),
        ], md=4),
    ], className='mb-3'),
    
    html.Div(id='foreign-perc-output'),
    dcc.Store(id='last-action-store', storage_type='session'),
    dcc.Store(id='stored-recommendations'),

    dbc.Row([
        dbc.Col([
            html.H4('Streaming-Dienst auswählen'),
            dcc.Dropdown(id='streaming-service-dropdown', options=[{'label': service, 'value': service} for service in df['streaming_service'].unique()], placeholder='Bitte wählen Sie einen Streaming-Dienst aus'),
        ], md=6),
        dbc.Col([
            html.Button('Suche starten', id='submit-filter-button', n_clicks=0, className='btn btn-primary mt-4'), 
            html.Button('Suche zurücksetzen', id='reset-button', n_clicks=0, className='btn btn-secondary mt-4 ml-2'), 
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
        placeholder='Bitte wählen Sie eine Analyse aus',
        className='mb-3'
    ),
    
    html.Div(id='analysis-output', className='mb-3'),
    
    html.Div(id='page-content'), 
    dbc.Pagination(id="pagination", max_value=1, active_page=1, size="sm", style={'marginTop': 30, 'marginBottom': '20px'}), 
], style={'textAlign': 'center', 'width': '80%', 'height': '100vh', 'minHeight': '100vh', 'margin': '0 auto', 'padding': '20px', 'backgroundImage': 'url(https://repository-images.githubusercontent.com/275336521/20d38e00-6634-11eb-9d1f-6a5232d0f84f)', 'backgroundSize': 'cover', 'backgroundPosition': 'center center', 'color': '#f8f9fa'})


def authenticate_user(username, password, cursor):
    cursor.execute('''SELECT * FROM users WHERE username=? AND password=?''', (username, password))
    return cursor.fetchone()
@app.callback(
    [Output('auth-feedback', 'children'),
    Output('genre-dropdown', 'value'),
    Output('streaming-service-dropdown', 'value'),
    Output('movie-title-input', 'value'),
    Output('title-recommendations-output', 'children'),
    Output('filter-recommendations-output', 'children'),
    Output('stored-recommendations', 'data'),
    Output('pagination', 'active_page'),
    Output('pagination', 'max_value')],
    [Input('auth-button', 'n_clicks'),
     Input('register-button', 'n_clicks'),
     Input('reset-button', 'n_clicks'),
     Input('submit-filter-button', 'n_clicks'),
     Input('find-recommendations-button', 'n_clicks')],
    [State('login-username', 'value'), State('login-password', 'value'),
     State('reg-username', 'value'), State('reg-password', 'value'),
     State('reg-favorite-genre', 'value'), State('reg-favorite-streaming-service', 'value'),
     State('genre-dropdown', 'value'), State('year-slider', 'value'),
     State('rating-slider', 'value'), State('streaming-service-dropdown', 'value'),
     State('movie-title-input', 'value'), State('last-action-store', 'data')]
)
def update_outputs(auth_clicks, register_clicks, reset_clicks, filter_clicks, find_clicks,
                   username, password, reg_username, reg_password, reg_genre, reg_service,
                   genres, year_range, rating, service, movie_title, last_action_data):

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'auth-button':
        if auth_clicks:
            conn = sqlite3.connect('userdata.db')
            c = conn.cursor()
            user = authenticate_user(username, password, c)
            if user:
                auth_feedback = html.Div('Authentication successful!', style={'color': 'green'})
                favorite_genre = user[3]
                favorite_streaming_service = user[4]
                conn.close()
                return (auth_feedback, favorite_genre, favorite_streaming_service,
                        movie_title, [], [], None, 1, 1)
                
            else:
                auth_feedback = html.Div('Invalid username or password. Please try again.', style={'color': 'red'})
                conn.close()
                return (auth_feedback, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update)
        else:
            raise PreventUpdate

    elif button_id == 'register-button':
        if register_clicks:
            if reg_username and reg_password and reg_genre and reg_service:
                conn = sqlite3.connect('userdata.db')
                c = conn.cursor()
                try:
                    c.execute('''INSERT INTO users (username, password, favorite_genre, favorite_streaming_service)
                                VALUES (?, ?, ?, ?)''', (reg_username, reg_password, reg_genre, reg_service))
                    conn.commit()
                    reg_feedback = html.Div('Registration successful!', style={'color': 'green'})
                except sqlite3.IntegrityError:
                    reg_feedback = html.Div('Username already exists. Please choose another one.', style={'color': 'red'})
                conn.close()
                return (reg_feedback, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update)
            else:
                reg_feedback = html.Div('Please fill out all fields.', style={'color': 'red'})
                return (reg_feedback, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update)
        else:
            raise PreventUpdate

    elif button_id == 'reset-button':
        empty_df = pd.DataFrame(columns=['title', 'description'])  
        empty_df_json = empty_df.to_json(date_format='iso', orient='split')
        return ('', [], [], '', html.Div(), html.Div(), empty_df_json, 1, 1)

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
            return (dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, no_update, 'Keine Filme gefunden, die den Kriterien entsprechen.',
                    None, dash.no_update, dash.no_update)
        else:
            recommendations_json = filtered_df.to_json(date_format='iso', orient='split')
            total_pages = math.ceil(len(filtered_df) / PAGE_SIZE)
            return (dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, no_update, no_update,
                    recommendations_json, dash.no_update, total_pages)

    elif button_id == 'find-recommendations-button':
        if not movie_title:
            # Wenn der Filmtitel leer ist, gibt es keine gültige Suche.
            return ('Ungültige Suche. Bitte geben Sie einen Filmtitel ein.', no_update, no_update,
                    no_update, no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update)
        
        recommendations = movie_recommender.recommend(movie_title)
        if isinstance(recommendations, str):
            # Wenn 'recommendations' ein String ist, gibt es keine passenden Empfehlungen.
            return ('Keine Empfehlungen gefunden.', no_update, no_update,
                    no_update, no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update)
        elif recommendations.empty:
            # Wenn 'recommendations' ein DataFrame ist und leer ist, gibt es keine passenden Empfehlungen.
            return ('Keine Empfehlungen gefunden.', no_update, no_update,
                    no_update, no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update)
        else:
            # Wenn 'recommendations' nicht leer ist, gibt es Empfehlungen.
            recommendations_json = recommendations.to_json(date_format='iso', orient='split')
            total_pages = math.ceil(len(recommendations) / PAGE_SIZE)
            return (dash.no_update, dash.no_update, dash.no_update,
                    no_update, no_update, no_update,
                    recommendations_json, dash.no_update, total_pages)

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
            style={'margin': '10px', 'flex': '1 0 18%'} 
        )
        tiles.append(dbc.Col(card, md=2))  
    return html.Div(tiles, style={'display': 'flex', 'flexWrap': 'wrap', 'justifyContent': 'center'})

@app.callback(
    Output('page-content', 'children'),
    [Input('pagination', 'active_page'), Input('stored-recommendations', 'data')]
)
def update_page_content_and_pagination(active_page, stored_data):
    if stored_data is None or stored_data == json.dumps([]):  
        raise dash.exceptions.PreventUpdate
    
    recommendations = pd.read_json(stored_data, orient='split')
    total_pages = math.ceil(len(recommendations) / PAGE_SIZE)
    start_index = (active_page - 1) * PAGE_SIZE
    end_index = start_index + PAGE_SIZE
    page_data = recommendations.iloc[start_index:end_index]

 
    tiles = generate_movie_tiles(page_data)

    return tiles, total_pages



if __name__ == '__main__':
    app.run_server(debug=True)