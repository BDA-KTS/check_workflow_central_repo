import json
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, accuracy_score, classification_report
from sklearn.multiclass import OneVsRestClassifier
import joblib
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split

# --------------------------------------------------
# 1) JSONL laden
# --------------------------------------------------
def load_jsonl_to_dataframe(path: str) -> pd.DataFrame:
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))

    df = pd.DataFrame(rows)
    return df


df = load_jsonl_to_dataframe("training_data.jsonl")

# Nur die Spalten, die wir wirklich brauchen
df = df[["text", "labels"]].copy()

# --------------------------------------------------
# 2) Grundbereinigung
# --------------------------------------------------
df["text"] = df["text"].astype(str).str.strip()

# labels sollte eine Liste sein
df["labels"] = df["labels"].apply(
    lambda x: x if isinstance(x, list) else []
)

# Leere Texte entfernen
df = df[df["text"] != ""].copy()

# Optional: Beispiele ohne Labels entfernen
df = df[df["labels"].map(len) > 0].copy()

# Optional: Duplikate auf Textebene entfernen
df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)

print("Anzahl Beispiele:", len(df))

X=df["text"].astype(str)
y=df["labels"]

vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words="english",
    max_features=20000,
    ngram_range=(1, 2)
)

X_train_vec = vectorizer.fit_transform(X)

# Binarize labels
mlb = MultiLabelBinarizer()
y_train_bin = mlb.fit_transform(y)


print("X_train_vec:", X_train_vec.shape)
print("y_train_bin:", y_train_bin.shape)
print("Classes:", mlb.classes_)

# Model
model = OneVsRestClassifier(
    LogisticRegression(
        max_iter=2000,
        solver="liblinear"
    )
)

# Train
model.fit(X_train_vec, y_train_bin)

def predict_with_probabilities(text: str, threshold: float = 0.5):
    vec = vectorizer.transform([text])
    probs = model.predict_proba(vec)[0]
    predicted = [
        (label, float(prob))
        for label, prob in zip(mlb.classes_, probs)
        if prob >= threshold
    ]
    predicted.sort(key=lambda x: x[1], reverse=True)
    return predicted, dict(zip(mlb.classes_, map(float, probs)))

joblib.dump(model, "../models/model.joblib")
joblib.dump(vectorizer, "../models/vectorizer.joblib")
joblib.dump(mlb, "../models/mlb.joblib")