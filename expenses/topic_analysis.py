import pandas as pd
import expenses.data_handler as data_handler  # Use absolute import in your project

from datetime import date
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

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
    """
    Combine 'name' and 'description' fields for text analysis.
    """
    return df['name'].fillna('') + ' ' + df['description'].fillna('')

def apply_kmeans(text_data: pd.Series, n_clusters: int) -> pd.Series:
    """
    Apply KMeans clustering to the text data using Spanish stopwords.
    Return a Series of labeled categories using the most representative word for each cluster.
    """
    # Vectorize the text data
    vectorizer = TfidfVectorizer(stop_words=SPANISH_STOPWORDS)
    X = vectorizer.fit_transform(text_data)

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    labels = kmeans.fit_predict(X)

    # Get feature names and cluster centers
    feature_names = vectorizer.get_feature_names_out()
    cluster_centers = kmeans.cluster_centers_

    # Extract top term for each cluster
    top_terms = []
    for i in range(n_clusters):
        top_index = cluster_centers[i].argmax()
        top_term = feature_names[top_index]
        top_terms.append(top_term)

    # Map numeric labels to top terms
    label_to_term = {i: top_terms[i] for i in range(n_clusters)}
    labeled_series = pd.Series(labels).map(label_to_term)

    return labeled_series

def get_category_distribution(
        is_fixed: bool, 
        n_clusters: int,
        date: date
    ) -> pd.DataFrame:
    """
    Load expenses, apply clustering, and return category distribution.
    """
    df = data_handler.load_expenses_by_month(is_fixed, date)
    if df.empty:
        return pd.DataFrame(columns=["Category", "amount"])
    # group same name expenses
    df['name'] = df['name'].str.lower().str.strip()
    df = df.groupby('name', as_index=False).agg({
        'amount': 'sum',
        'description': lambda x: ' '.join(x),  # Combine descriptions
        'date': 'first'          # Keep the first date
    })

    text_data = preprocess_text(df)
    labels = apply_kmeans(text_data, n_clusters)
    df['Category'] = labels
    return df