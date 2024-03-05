import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from cleantext import clean
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
import ast
import string 

class MovieRecommender:
    def __init__(self, df_stream_dir_path):
        self.df = pd.read_csv(df_stream_dir_path)
        self.df = self.df[self.df["type"] == "MOVIE"].reset_index(drop=True)
        self.prepare_data()
        self.tfidf = TfidfVectorizer()
        self.count = CountVectorizer()
        self.tfidf_matrix = None
        self.count_matrix = None
        self.hybrid_cosine_sim = None
        # Vorbereitung der NLTK-Ressourcen
        nltk.download('stopwords')
        nltk.download('punkt')
        nltk.download('wordnet')

    def prepare_data(self):
        self.df = self.df[["title", "description", "genres", "name", "primaryName"]].copy()
        self.df["description"] = self.df["description"].apply(self.preprocess_text)
        self.df["genres"] = self.df["genres"].apply(self.literally)
        self.df["name"] = self.df["name"].apply(self.lower_strip).apply(lambda x: self.top_cast(x, 1))
        self.df["primaryName"] = self.df["primaryName"].apply(self.lower_strip_str)
        self.df["soup"] = self.df.apply(self.metadata_soup, axis=1)

    def preprocess_text(self, text):
        # Kombinierte Vorverarbeitungsfunktionen ohne den no_emoji-Parameter
        text = clean(text).lower().translate(str.maketrans('', '', string.punctuation))
        stop_words = set(stopwords.words("english"))
        tokens = word_tokenize(text)
        filtered = [WordNetLemmatizer().lemmatize(w) for w in tokens if not w in stop_words]
        return ' '.join(filtered)


    def lower_strip(self, text_lst):
        if isinstance(text_lst, list):
            try:
                text_lst = [str.lower(i.replace(" ", "")) for i in text_lst]
            except:
                text_lst = ''
        else:
            text_lst = ''
        return text_lst

    def lower_strip_str(self, text):
        if isinstance(text, str):
            text = str.lower(text.replace(" ", ""))
        else:
            text = ''
        return text

    def literally(self, text):
        try:
            text = ast.literal_eval(text)
        except:
            text = float('nan')
        return text

    def top_cast(self, cast, n):
        return cast[:n] if len(cast) > n else cast

    def metadata_soup(self, df):
        return " ".join(df["genres"]) + " " + " ".join(df["name"]) + " " + df["primaryName"]

    def fit(self):
        self.tfidf_matrix = self.tfidf.fit_transform(self.df["description"])
        self.count_matrix = self.count.fit_transform(self.df['soup'])
        tfidf_cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        count_cosine_sim = cosine_similarity(self.count_matrix, self.count_matrix)
        A, B = 2, 1  # Gewichtungsfaktoren
        self.hybrid_cosine_sim = A * tfidf_cosine_sim + B * count_cosine_sim

    def recommend(self, movie_title):
        # Filter DataFrame für den gegebenen Filmtitel
        filtered_df = self.df[self.df['title'] == movie_title]

        # Überprüfe, ob der gefilterte DataFrame leer ist
        if filtered_df.empty:
            # Keine Empfehlungen gefunden, gebe eine leere Liste oder eine Fehlermeldung zurück
            return pd.DataFrame(columns=["title", "description"])

        # Wenn der DataFrame nicht leer ist, fahre mit der Empfehlungslogik fort
        index = filtered_df.index[0]
        similarity_scores = pd.Series(self.hybrid_cosine_sim[index]).sort_values(ascending=False)
        top_indices = similarity_scores.iloc[1:11].index  # Top 10 Empfehlungen, ohne den Film selbst
        recommendations = self.df.iloc[top_indices]
        return recommendations[["title", "description"]]

