import numpy as np
import pandas as pd
from wordcloud import WordCloud
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from cleantext import clean
import plotly.graph_objects as go
import string
from scipy import stats
import plotly.express as px

class MovieRecommenderViz:
    @staticmethod
    def load_and_prepare_data(filepath):
        df = pd.read_csv(filepath)
        df.drop(df[df['streaming_service'].isin(["crunchyroll", "rakuten"])].index, inplace=True)
        df["US"] = df["production_countries"].apply(lambda x: 1 if 'US' in x else 0)
        return df

    @staticmethod
    def calculate_foreign_perc(df):
        foreign_perc = df.groupby("streaming_service")["US"].agg(Perc=lambda x: (x.count() - x.sum()) * 100 / x.count()).reset_index()
        fig = px.bar(foreign_perc, x='streaming_service', y='Perc', title='Prozentuale Verteilung von ausländischen Filmen')
        fig.update_layout(xaxis_title='Streaming-Dienst', yaxis_title='Prozent')
        return fig

    @staticmethod
    def plot_kde_plots(df):
        fig = go.Figure()
        services = ['netflix', 'amazon', 'disney', 'hulu', 'hbo', 'darkmatter', 'paramount']
        for service in services:
            service_df = df[(df["US"] == 0) & (df["streaming_service"] == service)]
            fig.add_trace(go.Histogram(x=service_df['imdb_score'], name=service, histnorm='probability density'))
        fig.update_layout(title='KDE Plots für verschiedene Streaming-Dienste', xaxis_title='IMDb Score', yaxis_title='Dichte', barmode='overlay')
        fig.update_traces(opacity=0.75)
        return fig

    @staticmethod
    def calculate_variance_and_ttest(df):
        nfx_intl = df[(df["US"] == 0) & (df["streaming_service"] == 'netflix')]
        amz_intl = df[(df["US"] == 0) & (df["streaming_service"] == 'amazon')]
        result = stats.ttest_ind(a=nfx_intl['imdb_score'], b=amz_intl['imdb_score'], alternative='greater', equal_var=True)
        return {'var_nfx': np.var(nfx_intl['imdb_score']), 'var_amz': np.var(amz_intl['imdb_score']), 't_statistic': result.statistic, 'p_value': result.pvalue}

    @staticmethod
    def plot_budget_visualizations(df):
        df_top_budg = df.sort_values(by='budget', ascending=False).head(10)
        fig = px.bar(df_top_budg, x='title', y='budget', title='Top Budget Films')
        fig.update_layout(xaxis_title='Film Title', yaxis_title='Budget')
        return fig

    @staticmethod
    def clean_and_process_text(text):
        text = clean(text, no_emoji=True).lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(text)
        tokens = [w for w in tokens if not w in stop_words]
        lemmatizer = WordNetLemmatizer()
        lemmas = [lemmatizer.lemmatize(w) for w in tokens]
        return ' '.join(lemmas)
