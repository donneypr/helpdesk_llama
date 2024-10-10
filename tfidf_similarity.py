import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def load_ticket_data(resolved_tickets):
    df = pd.read_csv(resolved_tickets)
    if 'Subject' not in df.columns or 'Resolution' not in df.columns:
        raise ValueError("CSV file must contain 'Subject' and 'Resolution' columns.")
    return df

def vectorize_subjects(df):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Subject'])
    return tfidf_matrix, vectorizer

def find_similar_ticket(new_subject, tfidf_matrix, df, vectorizer):
    new_tfidf = vectorizer.transform([new_subject])
    cosine_similarities = cosine_similarity(new_tfidf, tfidf_matrix).flatten()
    most_similar_idx = np.argmax(cosine_similarities)
    most_similar_ticket = df.iloc[most_similar_idx]
    return most_similar_ticket['Subject'], most_similar_ticket['Resolution']

if __name__ == "__main__":
    df = load_ticket_data('resolved_tickets.csv')
    tfidf_matrix, vectorizer = vectorize_subjects(df)
    subject, resolution = find_similar_ticket("Campus Groups Profile Access", tfidf_matrix, df, vectorizer)
    print(f"Similar Ticket: {subject}\nResolution: {resolution}")