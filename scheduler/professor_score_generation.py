import joblib
import nltk
from nltk.corpus import stopwords
import os

# File location of model
current_dir = os.path.dirname(__file__)
filename = os.path.join(current_dir, "model_and_vectorizer.joblib")

# Import model and vectorizer
model, vectorizer = joblib.load(filename)

# Checks if libraries are downloaded
for resource in ["punkt", "stopwords"]:
    try:
        nltk.data.find(f"tokenizers/{resource}" if resource == "punkt" else f"corpora/{resource}")
    except LookupError:
        nltk.download(resource, quiet=True)
stop_words = set(stopwords.words('english'))

# Tokenize, lowercase, and remove stopwords from each text
def __preprocess_text(text):
    tokens = nltk.word_tokenize(text.lower())
    filtered_tokens = [word for word in tokens if word not in stop_words]
    return ' '.join(filtered_tokens)

def analyze_review(review: str):
    """
    Analyze a given text review and return model predictions.

    This function preprocesses the input review text, transforms it using
    a pre-fitted vectorizer, and applies a trained model to generate
    predictions such as sentiment or category classification.

    Args:
        review (str): The raw text of the review to be analyzed.

    Returns:
        str: The predicted label for the review (e.g., 'positive' or 'negative').

    Raises:
        ValueError: If the input review is empty or invalid.
    """

    # Raise error if input is empty or otherwise invalid
    if not isinstance(review, str) or not review.strip():
        raise ValueError("Input review must be a non-empty string.")

    # Preprocess the input
    processed_review = __preprocess_text(review)
    # Convert into feature vector using pre-trained vectorizer
    X_new = vectorizer.transform([processed_review])
    # Use training model to generate prediction
    predictions = model.predict(X_new)
    return predictions[0]