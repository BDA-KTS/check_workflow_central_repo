import joblib

def load_ml_artifacts():
    model = joblib.load(ML_PATH/"model.joblib")
    vectorizer = joblib.load(ML_PATH/ "vectorizer.joblib")
    mlb = joblib.load(ML_PATH / "mlb.joblib")
    return model, vectorizer, mlb

def predict_labels_with_probability(path: Path ,threshold: float = 0.5):
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
    text = extract_text_from_content(path)
    model, vectorizer, mlb = load_ml_artifacts()
    vec = vectorizer.transform([text])
    probs = model.predict_proba(vec)[0]
    probability_map = {
        label: float(prob)
        for label, prob in zip(mlb.classes_, probs)
    }
    
    predicted = [
        label for label, prob in probability_map.items()
        if prob >= threshold
    ]
    if predicted:
        predicted.sort(key=lambda label: probability_map[label], reverse=True)
        result['messages'] = [f"Predicted labels: {', '.join(predicted) if predicted else 'none'}", f"Probability: {round(probability_map[predicted[0]] * 100, 2)}%"]
    else:
        result['messages'] = ["No labels predicted with probability above threshold."]
    result['ifpassed'] = True
    return result

