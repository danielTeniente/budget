import pandas as pd
import json
from datetime import date
import expenses.data_handler as data_handler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


# Spanish stopwords list
SPANISH_STOPWORDS = [
    'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se', 'las', 'por', 'un', 'para',
    'con', 'no', 'una', 'su', 'al', 'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este',
    'sí', 'porque', 'esta', 'entre', 'cuando', 'muy', 'sin', 'sobre', 'también', 'me', 'hasta',
    'hay', 'donde', 'quien', 'desde', 'todo', 'nos', 'durante', 'todos', 'uno', 'les', 'ni',
    'contra', 'otros', 'ese', 'eso', 'ante', 'ellos', 'e', 'esto', 'mí', 'antes', 'algunos',
    'qué', 'unos', 'yo', 'otro', 'otras', 'otra', 'él', 'tanto', 'esa', 'estos', 'mucho',
    'quienes', 'nada', 'muchos', 'cual', 'poco', 'ella', 'estar', 'estas', 'algunas', 'algo',
    'nosotros', 'mi', 'mis', 'tú', 'te', 'ti', 'tu', 'tus', 'ellas', 'nosotras', 'vosotros',
    'vosotras', 'os', 'mío', 'mía', 'míos', 'mías', 'tuyo', 'tuya', 'tuyos', 'tuyas', 'suyo',
    'suya', 'suyos', 'suyas', 'nuestro', 'nuestra', 'nuestros', 'nuestras', 'vuestro',
    'vuestra', 'vuestros', 'vuestras', 'esos', 'esas'
]


def preprocess_text(df: pd.DataFrame) -> pd.Series:
    """Combine 'name' and 'description' fields for text analysis."""
    return df['name'].fillna('') + ' ' + df['description'].fillna('')


def load_topics(topic_file: str) -> dict:
    """Load topic keywords from JSON file."""
    with open(topic_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def assign_topics(text_data: pd.Series, topic_keywords: dict) -> pd.Series:
    """Assign topics to expenses based on TF-IDF cosine similarity."""
    topic_docs = [' '.join(words) for words in topic_keywords.values()]
    topic_names = list(topic_keywords.keys())

    combined_texts = topic_docs + list(text_data)

    vectorizer = TfidfVectorizer(stop_words=SPANISH_STOPWORDS)
    tfidf_matrix = vectorizer.fit_transform(combined_texts)

    topic_vectors = tfidf_matrix[:len(topic_docs)]
    expense_vectors = tfidf_matrix[len(topic_docs):]

    similarity_matrix = cosine_similarity(expense_vectors, topic_vectors)
    assigned_topics = [topic_names[i] for i in similarity_matrix.argmax(axis=1)]

    return pd.Series(assigned_topics)


def get_category_distribution(is_fixed: bool, selected_date: date) -> pd.DataFrame:
    """
    Load expenses, apply topic matching, and return categorized DataFrame.
    Returns full DataFrame with Category column for further analysis.
    """
    topic_file = 'data/expense_topics.json'
    df = data_handler.load_expenses_by_month(is_fixed, selected_date)
    
    # CAMBIO: Agregamos 'frequency' a las columnas por defecto
    if df.empty:
        return pd.DataFrame(columns=["name", "amount", "frequency", "description", "date", "Category"])

    df['name'] = df['name'].str.lower().str.strip()
    
    # CAMBIO IMPORTANTE: 
    # Usamos named aggregation para calcular la suma (amount) Y la cuenta (frequency) al mismo tiempo
    df = df.groupby('name', as_index=False).agg(
        amount=('amount', 'sum'),              # Suma total del dinero gastado en este item
        frequency=('amount', 'count'),         # Cuenta cuántas veces aparece este item
        description=('description', lambda x: ' '.join(x)),
        date=('date', 'first')
    )

    text_data = preprocess_text(df)
    topic_keywords = load_topics(topic_file)
    labels = assign_topics(text_data, topic_keywords)
    df['Category'] = labels
    return df


def get_top_category(df: pd.DataFrame) -> str:
    """Return the category with the highest total amount."""
    if df.empty:
        return ""
    category_totals = df.groupby('Category')['amount'].sum()
    return category_totals.idxmax()


def get_available_categories(df: pd.DataFrame) -> list[str]:
    """Return list of unique categories sorted by total amount (descending)."""
    if df.empty:
        return []
    category_totals = df.groupby('Category')['amount'].sum().sort_values(ascending=False)
    return category_totals.index.tolist()


def apply_kmeans(text_data: pd.Series, n_clusters: int = 3) -> pd.Series:
    """
    Apply K-Means clustering to text data using TF-IDF vectors.
    Returns labeled categories using the most representative word for each cluster center.
    """
    if len(text_data) == 0:
        return pd.Series(dtype=str)
    
    true_k = min(n_clusters, len(text_data))
    
    if true_k <= 1:
        term = text_data.iloc[0].split()[0] if text_data.iloc[0] else 'General'
        return pd.Series([term.capitalize()] * len(text_data))

    vectorizer = TfidfVectorizer(stop_words=SPANISH_STOPWORDS)
    X = vectorizer.fit_transform(text_data)
    
    kmeans = KMeans(n_clusters=true_k, n_init=10)
    labels = kmeans.fit_predict(X)
    
    feature_names = vectorizer.get_feature_names_out()
    label_to_term = {}
    ordered_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    
    for i in range(true_k):
        top_feature_index = ordered_centroids[i, 0]
        top_term = feature_names[top_feature_index]
        label_to_term[i] = top_term.capitalize()
    
    labeled_series = pd.Series(labels).map(label_to_term)
    
    return labeled_series


def get_subcategory_distribution(
    df: pd.DataFrame,
    category: str,
    n_clusters: int = 3
) -> pd.DataFrame:
    """
    Filter expenses by category and apply K-Means subcategorization.
    Returns DataFrame with Subcategory column.
    """
    # CAMBIO: Agregamos 'frequency' a las columnas por defecto
    if df.empty:
        return pd.DataFrame(columns=["name", "amount", "frequency", "description", "date", "Category", "Subcategory"])
    
    category_df = df[df['Category'] == category].copy()
    
    if category_df.empty:
        return pd.DataFrame(columns=["name", "amount", "frequency", "description", "date", "Category", "Subcategory"])
    
    text_data = preprocess_text(category_df)
    
    subcategory_labels = apply_kmeans(text_data, n_clusters=n_clusters)
    category_df['Subcategory'] = subcategory_labels.values
    
    return category_df