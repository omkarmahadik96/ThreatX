import os
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(BASE_DIR, "model.pkl")
vectorizer_path = os.path.join(BASE_DIR, "vectorizer.pkl")

data = {
    "text": [
        # 🔴 PHISHING
        "Click here to verify your bank account",
        "Urgent login required immediately",
        "Reset your password now",
        "Your account has been suspended verify now",
        "Win free money click here",
        "Bank alert update your details",
        "Confirm your OTP to continue",
        "Security alert login to secure account",
        "Your payment failed update now",
        "Congratulations you won a prize click link",
        "Verify your email immediately to avoid suspension",
        "Login to your account using this secure link",
        "Your Netflix account needs verification now",
        "Update billing details to avoid service interruption",
        "Suspicious login detected click here to secure account",
        "Your PayPal account is limited login now",
        "You have won a lottery click to claim",
        "Immediate action required verify your identity",
        "Your account will be blocked confirm now",
        "Click below link to unlock your account",

        # 🟢 SAFE
        "Meeting schedule attached",
        "Project discussion tomorrow",
        "Invoice attached please check",
        "Let's catch up tomorrow",
        "Dinner plan for tonight",
        "Your order has been shipped",
        "Team meeting at 5 PM",
        "Please review the document",
        "Happy birthday have a great day",
        "See you at the event",
        "Your subscription is active",
        "Thanks for your support",
        "Google Drive link for project files",
        "Join the meeting using this Teams link",
        "Here is the report for your review",
        "Your package has been delivered successfully",
        "Let's discuss the updates in tomorrow's call",
        "Reminder for scheduled appointment",
        "Attached is the presentation file",
        "Please check the updated document"
    ],
    "label": [1]*20 + [0]*20
}

df = pd.DataFrame(data)

vectorizer = TfidfVectorizer(
    stop_words="english",
    ngram_range=(1,3),
    max_features=8000
)

X = vectorizer.fit_transform(df["text"])
y = df["label"]

# 🔥 SPLIT
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LogisticRegression(max_iter=300, class_weight="balanced")

model.fit(X_train, y_train)

# 🔥 ACCURACY
y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))

pickle.dump(model, open(model_path, "wb"))
pickle.dump(vectorizer, open(vectorizer_path, "wb"))

print("[SUCCESS] Model trained & saved")