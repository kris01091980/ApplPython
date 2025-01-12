import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt


# Функция для определения сезона
def get_current_season(date):
    month = date.month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


# Функция для получения текущей температуры через OpenWeatherMap API
def get_current_temperature(city, api_key):
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "units": "metric",
        "appid": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        return data["main"]["temp"], None
    elif response.status_code == 401:
        return None, "Invalid API key"
    else:
        return None, f"Error: {response.status_code}"


# Функция для сравнения текущей температуры с историческими данными
def compare_with_historical(city, current_temp, season, historical_data):
    city_season_data = historical_data[(historical_data["city"] == city) & (historical_data["season"] == season)]
    if not city_season_data.empty:
        mean_temp = city_season_data["temperature"].mean()
        std_temp = city_season_data["temperature"].std()
        lower_bound = mean_temp - 2 * std_temp
        upper_bound = mean_temp + 2 * std_temp

        if lower_bound <= current_temp <= upper_bound:
            return f"Температура {current_temp}°C является нормальной для сезона {season}.", "normal"
        else:
            return f"Температура {current_temp}°C аномальна для сезона {season}!", "anomalous"
    else:
        return "Нет исторических данных для выбранного города и сезона.", "no_data"


# Интерфейс Streamlit
st.title("Приложение для анализа температур")

# Загрузка файла с историческими данными
uploaded_file = st.file_uploader("Загрузите файл с историческими данными (CSV):")
if uploaded_file is not None:
    historical_data = pd.read_csv(uploaded_file)
    historical_data["timestamp"] = pd.to_datetime(historical_data["timestamp"])
    historical_data["season"] = historical_data["timestamp"].apply(get_current_season)

    # Выбор города
    cities = historical_data["city"].unique()
    selected_city = st.selectbox("Выберите город:", cities)

    # Отображение описательной статистики
    city_data = historical_data[historical_data["city"] == selected_city]
    st.subheader(f"Описательная статистика для {selected_city}")
    st.write(city_data.describe())

    # Построение временного ряда
    st.subheader("Временной ряд температур с выделением аномалий")
    city_data["rolling_mean"] = city_data["temperature"].rolling(window=30).mean()
    mean = city_data["temperature"].mean()
    std = city_data["temperature"].std()
    city_data["is_anomaly"] = (city_data["temperature"] < (mean - 2 * std)) | \
                              (city_data["temperature"] > (mean + 2 * std))

    plt.figure(figsize=(10, 6))
    plt.plot(city_data["timestamp"], city_data["temperature"], label="Температура")
    plt.scatter(city_data["timestamp"][city_data["is_anomaly"]],
                city_data["temperature"][city_data["is_anomaly"]],
                color="red", label="Аномалии")
    plt.plot(city_data["timestamp"], city_data["rolling_mean"], label="Скользящее среднее", linestyle="--")
    plt.legend()
    plt.xlabel("Дата")
    plt.ylabel("Температура (°C)")
    plt.title(f"Температурный ряд для {selected_city}")
    st.pyplot(plt)

    # Построение сезонных профилей
    st.subheader("Сезонные профили температур")
    seasonal_stats = city_data.groupby("season")["temperature"].agg(["mean", "std"])
    st.bar_chart(seasonal_stats)

    # Ввод API-ключа
    api_key = st.text_input("Введите API-ключ OpenWeatherMap:")
    if api_key:
        current_temp, error = get_current_temperature(selected_city, api_key)
        if error:
            st.error(error)
        elif current_temp is not None:
            current_date = datetime.now()
            current_season = get_current_season(current_date)
            result, status = compare_with_historical(selected_city, current_temp, current_season, historical_data)
            st.subheader("Текущая температура")
            st.write(f"Текущая температура в городе {selected_city}: {current_temp}°C")
            st.write(result)
else:
    st.info("Пожалуйста, загрузите файл с историческими данными.")
