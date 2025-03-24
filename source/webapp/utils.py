import os
import shap

import joblib
import numpy as np
import pandas as pd

from core import settings

MODEL_PATH = os.path.join(settings.BASE_DIR, 'uploads', 'ml_model.pkl')

model = joblib.load(MODEL_PATH)

def predict_anomaly(features):
    feature_names = [f'V{i}' for i in range(1, 29)]  # V1 - V28
    df = pd.DataFrame([features], columns=feature_names)  # Создаём DataFrame с именами колонок

    # Предсказание аномалии
    is_fraud = model.predict(df)[0] == -1  # True = мошенничество

    # Анализ важности признаков с SHAP
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(df)

    # Определяем вклад каждого признака
    impact_scores = np.abs(shap_values[0])  # Абсолютные значения важности
    risk_score = np.clip(np.sum(impact_scores) * 10, 0, 100)  # Рейтинг риска (0–100%)

    # Определяем все факторы, влияющие на мошенничество
    fraud_factors = sorted(
        zip(feature_names, shap_values[0]),
        key=lambda x: -abs(x[1])  # Сортируем по абсолютной важности
    )

    explanation = "\n".join([f"{name}: {value:.2f}" for name, value in fraud_factors if abs(value) > 0.1])

    return is_fraud, round(risk_score, 2), explanation

