import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
#cleanup the similarity score to increase similarity
## Plan to implement SQLite for .csv and Redis for caching later.

def load_ticket_data(resolved_tickets):
    df = pd.read_csv(resolved_tickets)
    if 'Subject' not in df.columns or 'Resolution' not in df.columns:
        raise ValueError("CSV file must contain 'Subject' and 'Resolution' columns.")
    return df

def vectorize_subjects(df):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Subject'])
    return tfidf_matrix, vectorizer

def vectorize_resolutions(df):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Resolution'])
    return tfidf_matrix, vectorizer

def find_similar_ticket(new_subject, tfidf_matrix, df, vectorizer):
    new_tfidf = vectorizer.transform([new_subject])
    cosine_similarities = cosine_similarity(new_tfidf, tfidf_matrix).flatten()
    most_similar_idx = np.argmax(cosine_similarities)
    most_similar_ticket = df.iloc[most_similar_idx]
    
    return most_similar_ticket['Subject'], most_similar_ticket['Resolution']

def compare_ai_response_to_resolution(ai_response, resolution, df):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resolution, ai_response])
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2]).flatten()
    similarity_score = cosine_similarities[0] * 100
    
    return similarity_score

if __name__ == "__main__":
    df = load_ticket_data('resolved_tickets.csv')
    tfidf_matrix, vectorizer = vectorize_subjects(df)
    new_subject = "Campus Groups Profile Access"
    subject, resolution = find_similar_ticket(new_subject, tfidf_matrix, df, vectorizer)
    print(f"Most Similar Ticket Subject: {subject}\nResolution: {resolution}")
    ai_response = "Ensure that you have the necessary permissions to access the profile. Contact admin if access is denied."
    similarity_score = compare_ai_response_to_resolution(ai_response, resolution, df)
    print(f"AI Response Similarity Score: {similarity_score:.2f}%")
