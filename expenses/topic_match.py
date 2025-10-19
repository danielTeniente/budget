import pandas as pd
import json
from datetime import date
import expenses.data_handler as data_handler  # Use absolute import in your project
from sklearn.feature_extraction.text import TfidfVectorizer
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
    return df['name'].fillna('') + ' ' + df['description'].fillna('')

def load_topics(topic_file: str) -> dict:
    with open(topic_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def assign_topics(text_data: pd.Series, topic_keywords: dict) -> pd.Series:
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

def get_category_distribution(is_fixed: bool, date: date) -> pd.DataFrame:
    topic_file = 'data/expense_topics.json'
    df = data_handler.load_expenses_by_month(is_fixed, date)
    if df.empty:
        return pd.DataFrame(columns=["Category", "amount"])

    df['name'] = df['name'].str.lower().str.strip()
    df = df.groupby('name', as_index=False).agg({
        'amount': 'sum',
        'description': lambda x: ' '.join(x),
        'date': 'first'
    })

    text_data = preprocess_text(df)
    topic_keywords = load_topics(topic_file)
    labels = assign_topics(text_data, topic_keywords)
    df['Category'] = labels
    return df