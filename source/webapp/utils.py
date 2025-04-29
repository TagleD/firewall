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


def generate_firewall_rules(ip, port, bytes_number, connection_time, protocol, risk_score, location, is_fraud):
    rules = []
    if not ip:
        ip = "0.0.0.0/0"
    if not port:
        port = 0
    if not protocol:
        protocol = "tcp"

    protocol = protocol.lower()

    # Правила для протоколов
    if protocol in ["http", "https"]:
        if risk_score > 80 or is_fraud:
            rules.append(f"# BLOCK: High-risk HTTP/HTTPS connection")
            rules.append(f"iptables -A INPUT -p tcp --dport {port} -s {ip} -j DROP")
        else:
            rules.append(f"# ALLOW: Safe HTTP/HTTPS connection with traffic limit")
            rules.append(f"iptables -A INPUT -p tcp --dport {port} -s {ip} -m limit --limit 100/minute -j ACCEPT")

    elif protocol == "icmp":
        if risk_score > 80:
            rules.append(f"# BLOCK: ICMP (Ping Flood) suspected")
            rules.append(f"iptables -A INPUT -p icmp -s {ip} -j DROP")
        else:
            rules.append(f"# LIMIT: ICMP requests to avoid ping flood")
            rules.append(f"iptables -A INPUT -p icmp -s {ip} -m limit --limit 10/second -j ACCEPT")

    elif protocol in ["ftp", "tcp", "udp"]:
        if port in [5432, 3306, 27017]:  # PostgreSQL, MySQL, MongoDB
            rules.append(f"# BLOCK: Database port suspicious access")
            rules.append(f"iptables -A INPUT -p {protocol} --dport {port} -s {ip} -j DROP")
        else:
            if bytes_number > 1000000:
                rules.append(f"# BLOCK: Possible DDoS attack (huge traffic)")
                rules.append(f"iptables -A INPUT -p {protocol} --dport {port} -s {ip} -j DROP")
            else:
                rules.append(f"# ALLOW: Standard {protocol.upper()} traffic")
                rules.append(f"iptables -A INPUT -p {protocol} --dport {port} -s {ip} -j ACCEPT")

    # Правила по стране (геолокация)
    if location:
        suspicious_countries = ["Россия", "Китай", "Иран", "Северная Корея"]
        if any(country in location for country in suspicious_countries):
            rules.append(f"# BLOCK: Suspicious country {location}")
            rules.append(f"iptables -A INPUT -s {ip} -j DROP")
        else:
            rules.append(f"# LOG: Traffic from {location}")
            rules.append(f"iptables -A INPUT -s {ip} -j LOG --log-prefix \"FIREWALL:LOCATION: \" --log-level 6")

    # Общие правила при высоком риске
    if risk_score > 80:
        rules.append(f"# HARD BLOCK: Extremely high risk")
        rules.append(f"nft add rule inet filter input ip saddr {ip} drop")  # nftables пример

    # fail2ban-like правило имитация
    if is_fraud:
        rules.append(f"# FAIL2BAN: Block IP {ip} due to fraud detection")
        rules.append(f"iptables -I INPUT -s {ip} -j DROP")

    return rules
