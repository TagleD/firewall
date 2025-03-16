import os

import joblib
import pandas as pd

from core import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, 'uploads', 'ml_model.pkl')

model = joblib.load(MODEL_PATH)

def predict_anomaly(features):
    feature_names = [f'V{i}' for i in range(1, 29)]  # V1 - V28
    df = pd.DataFrame([features], columns=feature_names)  # Создаём DataFrame с именами колонок
    return model.predict(df)[0] == -1  # True = мошенничество

