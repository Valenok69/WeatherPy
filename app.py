from flask import Flask, request, render_template, jsonify
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)
load_dotenv()

API_KEY = os.getenv('API_KEY')
def get_location_key(city_name, api_key):
    url = f'http://dataservice.accuweather.com/locations/v1/cities/search?q={city_name}&apikey={api_key}'
    response = requests.get(url)
    if response.status_code == 503:
        raise ValueError("Кончились попытки :(")

    if response.status_code != 200:
        raise ValueError(f"Ошибка API: {response.status_code}, {response.text}")
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


def get_current_conditions(location_key, api_key):
    # URL для текущих погодных условий
    url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    params = {"apikey": api_key, "details": "true"}  # Параметр details=true для получения полной информации
    response = requests.get(url, params=params)

    # Логирование ответа API
    print("Response from Current Conditions API: {response.text}")

    if response.status_code != 200:
        raise ValueError(f"Ошибка API: {response.status_code}, {response.text}")

    data = response.json()
    if not data:
        raise ValueError("Нет данных о текущих погодных условиях")

    return data[0]  # Возвращаем первый элемент массива


def get_weather(city_name):
    # Получаем ключ локации
    location_key = get_location_key(city_name, API_KEY)

    # Получаем текущие погодные условия
    current_conditions = get_current_conditions(location_key, API_KEY)

    # Извлекаем нужные данные
    temperature = current_conditions["Temperature"]["Metric"]["Value"]
    wind_speed = current_conditions["Wind"]["Speed"]["Metric"]["Value"]
    humidity = current_conditions.get("RelativeHumidity", 0)
    precipitation = 100 if current_conditions.get("HasPrecipitation", False) else 0

    return extract_weather_info(temperature, wind_speed, humidity, precipitation)

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
        weather_data = {
            'start_city': {
                'city': start_city,
                'weather': start_weather
            },
            'end_city': {
                'city': end_city,
                'weather': end_weather
            }
        }

        return render_template('index.html', weather=weather_data)

    except Exception as e:
        return render_template('index.html', error=str(e))

@app.route('/')
def index():
    return render_template('index.html')

def home():
    return "Работает!!"

if __name__ == "__main__":
    app.run(debug=True)