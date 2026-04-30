import requests
import time
import pandas as pd
from dotenv import load_dotenv
import os


def get_api_key():
    key = os.getenv("WEATHER_API_KEY")
    if not key or not key.strip():
        raise ValueError("WEATHER_API_KEY environment variable is not set or empty")
    return key


def save_weather_data(df_new, csv_path="weather_data.csv"):
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path, dtype={"zip_code": str})
        df_combined = pd.concat([df_existing, df_new], ignore_index=True)
        df_combined = df_combined.drop_duplicates(subset=["zip_code", "date"], keep="last")
    else:
        df_combined = df_new.copy()
    df_combined["zip_code"] = df_combined["zip_code"].astype(str)
    df_combined.to_csv(csv_path, index=False)


if __name__ == "__main__":
    load_dotenv()
    API_KEY = get_api_key()

    api_url = "https://api.weatherapi.com/v1/forecast.json"

    zip_codes = [
        "90045",  # Los Angeles, CA
        "10001",  # New York, NY
        "60601",  # Chicago, IL
        "98101",  # Seattle, WA
        "33101",  # Miami, FL
        "77001",  # Houston, TX
        "85001",  # Phoenix, AZ
        "19101",  # Philadelphia, PA
        "78201",  # San Antonio, TX
        "92101",  # San Diego, CA
        "75201",  # Dallas, TX
        "95101",  # San Jose, CA
        "78701",  # Austin, TX
        "30301",  # Atlanta, GA
        "28201",  # Charlotte, NC
        "43201",  # Columbus, OH
        "80201",  # Denver, CO
        "32201",  # Jacksonville, FL
        "46201",  # Indianapolis, IN
        "94101",  # San Francisco, CA
    ]

    results = []

    for zip_code in zip_codes:
        params = {
            "key": API_KEY,
            "q": zip_code,
            "days": 7
        }

        response = requests.get(api_url, params=params)
        data = response.json()

        city = data["location"]["name"]
        region = data["location"]["region"]

        for day in data["forecast"]["forecastday"]:
            results.append({
                "zip_code": zip_code,
                "city": city,
                "region": region,
                "date": day["date"],
                "max_temp_f": day["day"]["maxtemp_f"],
                "min_temp_f": day["day"]["mintemp_f"],
                "condition": day["day"]["condition"]["text"],
            })

        print(f"{zip_code} | {city}, {region} | {len(data['forecast']['forecastday'])} days fetched")

        time.sleep(1)

    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    print(f"\nShape: {df.shape[0]} rows x {df.shape[1]} columns")

    save_weather_data(df)
    print("Appended to weather_data.csv")
