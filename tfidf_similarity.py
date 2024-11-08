import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def load_ticket_data(resolved_tickets):
    """
    Load ticket data from a CSV file containing resolved tickets.

    Args:
        resolved_tickets (str): The path to the CSV file containing resolved tickets.

    Returns:
        pd.DataFrame: A DataFrame containing the ticket data with 'Subject' and 'Resolution' columns.

    Raises:
        ValueError: If the required columns 'Subject' and 'Resolution' are not present in the CSV file.
    """
    df = pd.read_csv(resolved_tickets)
    if 'Subject' not in df.columns or 'Resolution' not in df.columns:
        raise ValueError("CSV file must contain 'Subject' and 'Resolution' columns.")
    return df

def vectorize_subjects(df):
    """
    Create a TF-IDF vectorization of ticket subjects.

    Args:
        df (pd.DataFrame): DataFrame containing ticket data with a 'Subject' column.

    Returns:
        tuple: A tuple containing:
            - tfidf_matrix (sparse matrix): TF-IDF matrix of the 'Subject' column.
            - vectorizer (TfidfVectorizer): The TF-IDF vectorizer used for transformation.
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Subject'])
    return tfidf_matrix, vectorizer

def vectorize_resolutions(df):
    """
    Create a TF-IDF vectorization of ticket resolutions.

    Args:
        df (pd.DataFrame): DataFrame containing ticket data with a 'Resolution' column.

    Returns:
        tuple: A tuple containing:
            - tfidf_matrix (sparse matrix): TF-IDF matrix of the 'Resolution' column.
            - vectorizer (TfidfVectorizer): The TF-IDF vectorizer used for transformation.
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df['Resolution'])
    return tfidf_matrix, vectorizer

def find_similar_ticket(new_subject, tfidf_matrix, df, vectorizer):
    """
    Find the most similar ticket to a new subject based on cosine similarity.

    Args:
        new_subject (str): The subject of the new ticket to find a similar ticket for.
        tfidf_matrix (sparse matrix): TF-IDF matrix of the existing ticket subjects.
        df (pd.DataFrame): DataFrame containing ticket data with 'Subject' and 'Resolution' columns.
        vectorizer (TfidfVectorizer): The TF-IDF vectorizer used for the 'Subject' column.

    Returns:
        tuple: A tuple containing:
            - subject (str): The subject of the most similar ticket.
            - resolution (str): The resolution of the most similar ticket.
    """
    new_tfidf = vectorizer.transform([new_subject])
    cosine_similarities = cosine_similarity(new_tfidf, tfidf_matrix).flatten()
    most_similar_idx = np.argmax(cosine_similarities)
    most_similar_ticket = df.iloc[most_similar_idx]
    
    return most_similar_ticket['Subject'], most_similar_ticket['Resolution']

def compare_ai_response_to_resolution(ai_response, resolution, df):
    """
    Compare an AI-generated response to an existing ticket resolution using cosine similarity.

    Args:
        ai_response (str): The AI-generated response to compare.
        resolution (str): The actual resolution to compare against.
        df (pd.DataFrame): DataFrame containing ticket data.

    Returns:
        float: The similarity score as a percentage between the AI response and the actual resolution.
    """
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform([resolution, ai_response])
    cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2]).flatten()
    similarity_score = cosine_similarities[0] * 100
    
    return similarity_score
