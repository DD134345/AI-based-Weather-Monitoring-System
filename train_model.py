import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os

os.makedirs("models", exist_ok=True)

np.random.seed(42)
temperature = np.random.normal(loc=30, scale=5, size=1000)
humidity = np.random.normal(loc=70, scale=10, size=1000)
pressure = np.random.normal(loc=1013, scale=7, size=1000)
target_temp = temperature + np.random.normal(0, 1, 1000)  # dự đoán nhiệt độ tiếp theo

df = pd.DataFrame({
    "temperature": temperature,
    "humidity": humidity,
    "pressure": pressure,
    "target_temp": target_temp
})

X = df[["temperature", "humidity", "pressure"]]
y = df["target_temp"]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, "models/weather_model.joblib")
joblib.dump(scaler, "models/weather_scaler.joblib")

print("Model have been trained and save in models")