from flask import Flask, request, render_template, jsonify
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)
API_KEY = "Gdup2wKwcPkIpRFfVKFuWkgLG3a68pJG"


def get_location_key(city_name, api_key):
    url = f'http://dataservice.accuweather.com/locations/v1/cities/search?q={city_name}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    if data:
        return data[0]['Key']
    else:
        raise ValueError("Не удалось найти город.")
def check_bad_weather(temperature, wind_speed, humidity, precipitation):
    if temperature < 0 or temperature > 35:
        return "Плохие погодные условия (температура)"
    if wind_speed > 50:
        return "Плохие погодные условия (ветер)"
    if precipitation > 70:
        return "Плохие погодные условия (осадки)"
    return "Хорошие погодные условия"
def get_weather(city_name):
    base_url = "http://dataservice.accuweather.com/forecasts/v1/daily/1day/"
    location_url = "http://dataservice.accuweather.com/locations/v1/cities/search"

    # Получение locationKey
    params = {"apikey": API_KEY, "q": city_name}
    response = requests.get(location_url, params=params)
    if response.status_code != 200:
        return {"error": f"Ошибка API: {response.status_code}, {response.text}"}
    location_data = response.json()
    if not location_data:
        return {"error": "Не удалось найти город"}

    location_key = location_data[0].get("Key")
    if not location_key:
        return {"error": "Не удалось получить locationKey"}
    forecast_url = f"{base_url}{location_key}"
    forecast_params = {"apikey": API_KEY, "metric": "true"}
    forecast_response = requests.get(forecast_url, params=forecast_params)
    if forecast_response.status_code != 200:
        return {"error": f"Ошибка API: {forecast_response.status_code}, {forecast_response.text}"}

    forecast_data = forecast_response.json()
    if "DailyForecasts" not in forecast_data or not forecast_data["DailyForecasts"]:
        return {"error": "Нет данных о прогнозе"}

        # Извлекаем необходимые данные
    daily_forecast = forecast_data["DailyForecasts"][0]
    temperature = daily_forecast.get("Temperature", {}).get("Maximum", {}).get("Value", 0)
    wind_speed = daily_forecast.get("Day", {}).get("Wind", {}).get("Speed", {}).get("Value", 0)
    humidity = daily_forecast.get("Day", {}).get("Humidity", 0)
    has_precipitation = daily_forecast.get("Day", {}).get("HasPrecipitation", False)
    precipitation = 100 if has_precipitation else 0
    weather_info = extract_weather_info(temperature, wind_speed, humidity, precipitation)

    return weather_info
def extract_weather_info(temperature, wind_speed, humidity, precipitation):
    weather_condition = check_bad_weather(temperature, wind_speed, humidity, precipitation)
    return {
        "Температура": temperature,
        "Скорость ветра": wind_speed,
        "Влажность": humidity,
        "Вероятность осадков": precipitation,
        "Погодные условия": weather_condition
    }

@app.route('/weather', methods=['POST'])
def weather():
    start_city = request.form.get('start_city')
    end_city = request.form.get('end_city')

    try:
        start_location_key = get_location_key(start_city, API_KEY)
        end_location_key = get_location_key(end_city, API_KEY)

        if not start_location_key or not end_location_key:
            raise ValueError("Не удалось найти один или оба города")

        start_weather = get_weather(start_location_key)
        end_weather = get_weather(end_location_key)

        if not start_weather or not end_weather:
            raise ValueError("Не удалось получить данные о погоде")

        # Оценка погодных условий
        #start_weather_status = check_bad_weather(start_weather)
        #end_weather_status = check_bad_weather(end_weather)

        # Формирование результата
        #weather_info = f"Погода в {start_city}: {start_weather_status}\nПогода в {end_city}: {end_weather_status}"
        weather_info = f"Погода в {start_city}: {start_weather}\nПогода в {end_city}: {end_weather}"
        return render_template('index.html', weather=weather_info)

    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/')
def index():
    return render_template('index.html')

def home():
    return "Работает!!"

if __name__ == "__main__":
    app.run(debug=True)
