import pandas as pd
import joblib
from sklearn.ensemble import IsolationForest

def train_model():
    data_from_file = pd.read_csv('../uploads/csv/creditcard.csv')
    features = data_from_file.iloc[:, 1:29]

    model = IsolationForest(n_estimators=100, contamination=0.002, random_state=42)
    model.fit(features)

    joblib.dump(model, '../uploads/ml_model.pkl')
    print("✅ Модель обучена и сохранена!")

if __name__ == "__main__":
    train_model()