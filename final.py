
"""
###############################################################################
# PROJECT: SkyShield
# TEAM: BlueForce
# CREATOR: Ahmed Wael
# EVENT: NASA Space Apps Challenge 2025
# DESCRIPTION: Air Quality Monitoring and Pollution Analysis System
# REPOSITORY: [https://github.com/ahmedwa1111/SkyShield---Project/]
# NASA PROJECT PAGE: [https://www.spaceappschallenge.org/2025/find-a-team/bulra-force/?tab=details]
###############################################################################
"""
"""
SkyShield - NASA Space Apps Challenge 2025
Team: BlueForce
Creator: Ahmed Wael
File: {Final}.py
Description: {Your challenge is to develop a web-based app that forecasts air quality by integrating real-time TEMPO data with ground-based air quality measurements and weather data}
Last Updated: {10/3/2025}

NASA Challenge: {Monitoring of Pollution (TEMPO) mission is revolutionizing air quality monitoring across North America by enabling better forecasts and reducing pollutant exposure}
"""

"""
SkyShield - North America Air Quality Monitoring with Weather Data
NASA Space Apps Challenge 2024 - Team BlueForce
Creator: Ahmed Wael
Region: North America
"""

import os
import time
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import sys
import json
import threading

# ---------------------------
# Setup logging
# ---------------------------
def setup_logging():
    """Setup logging with proper encoding handling"""
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='Y-%m-%d %H:%M:%S'
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler('north_america_air_quality.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

# Initialize logging
logger = setup_logging()

# ---------------------------
# CONFIGURATION FOR NORTH AMERICA
# ---------------------------
CONFIG = {
    "location": {
        "name": "North America Region",
        "lat": 40.7128,
        "lon": -74.0060,
        "city": "New York",
        "state": "New York",
        "country": "USA"
    },
    "update_interval_minutes": 5,
    "data_sources": {
        "iqair": "https://api.airvisual.com/v2/",
        "open_weather": "https://api.openweathermap.org/data/2.5/",
        "weather_api": "http://api.weatherapi.com/v1/"
    },
    "api_keys": {
        "iqair": "f60e848b-f405-4bfe-a096-c9935e595165",
        "openweather": "b1e04e3b1c8a4c0c8a8e4a4e4a4e4a4e"  # Free tier key
    },
    "north_america_cities": [
        {
            "city": "New York", "state": "New York", "country": "USA",
            "lat": 40.7128, "lon": -74.0060, "timezone": "America/New_York"
        },
        {
            "city": "Los Angeles", "state": "California", "country": "USA",
            "lat": 34.0522, "lon": -118.2437, "timezone": "America/Los_Angeles"
        },
        {
            "city": "Chicago", "state": "Illinois", "country": "USA",
            "lat": 41.8781, "lon": -87.6298, "timezone": "America/Chicago"
        },
        {
            "city": "Toronto", "state": "Ontario", "country": "Canada",
            "lat": 43.6532, "lon": -79.3832, "timezone": "America/Toronto"
        },
        {
            "city": "Vancouver", "state": "British Columbia", "country": "Canada",
            "lat": 49.2827, "lon": -123.1207, "timezone": "America/Vancouver"
        },
        {
            "city": "Mexico City", "state": "Mexico City", "country": "Mexico",
            "lat": 19.4326, "lon": -99.1332, "timezone": "America/Mexico_City"
        },
        {
            "city": "Montreal", "state": "Quebec", "country": "Canada",
            "lat": 45.5017, "lon": -73.5673, "timezone": "America/Montreal"
        },
        {
            "city": "Houston", "state": "Texas", "country": "USA",
            "lat": 29.7604, "lon": -95.3698, "timezone": "America/Chicago"
        }
    ]
}

# ---------------------------
# HEALTH THRESHOLDS
# ---------------------------
HEALTH_THRESHOLDS = {
    "PM2_5": {
        "GOOD": 12.0, "MODERATE": 35.4, "BAD": 55.4, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - healthy air quality",
        "MODERATE_DESC": "Moderate - acceptable air quality",
        "BAD_DESC": "Unhealthy for sensitive groups"
    },
    "NO2": {
        "GOOD": 40, "MODERATE": 100, "BAD": 200, "UNITS": "ppb",
        "GOOD_DESC": "Good - low vehicle pollution",
        "MODERATE_DESC": "Moderate - medium NO2 levels",
        "BAD_DESC": "Unhealthy - high nitrogen dioxide"
    },
    "O3": {
        "GOOD": 50, "MODERATE": 70, "BAD": 85, "UNITS": "ppb",
        "GOOD_DESC": "Good - low ozone levels",
        "MODERATE_DESC": "Moderate - increased ozone",
        "BAD_DESC": "Unhealthy - high ozone levels"
    },
    "CO2": {
        "GOOD": 450, "MODERATE": 600, "BAD": 1000, "UNITS": "ppm",
        "GOOD_DESC": "Excellent - fresh outdoor air",
        "MODERATE_DESC": "Moderate - typical urban levels",
        "BAD_DESC": "Poor - elevated CO2 levels"
    }
}

# Global variables
current_data = []
weather_data = {}
monitoring_active = True
run_count = 0

# ---------------------------
# WEATHER DATA FUNCTIONS
# ---------------------------
def get_weather_data(city_info):
    """Get comprehensive weather data for a city"""
    try:
        # Method 1: OpenWeatherMap (primary)
        weather = get_openweather_data(city_info)
        if weather:
            return weather

        # Method 2: Fallback to simple weather estimation
        return get_basic_weather_estimation(city_info)

    except Exception as e:
        logger.error(f"Weather data error for {city_info['city']}: {e}")
        return get_basic_weather_estimation(city_info)

def get_openweather_data(city_info):
    """Get weather data from OpenWeatherMap"""
    try:
        api_key = CONFIG["api_keys"]["openweather"]
        lat, lon = city_info["lat"], city_info["lon"]

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'units': 'metric'  # Celsius for metric
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return process_openweather_data(data, city_info)
        else:
            logger.warning(f"OpenWeather API status {response.status_code} for {city_info['city']}")
            return None

    except Exception as e:
        logger.error(f"OpenWeather error for {city_info['city']}: {e}")
        return None

def process_openweather_data(data, city_info):
    """Process OpenWeatherMap API response"""
    try:
        main = data.get('main', {})
        weather_info = data.get('weather', [{}])[0]
        wind = data.get('wind', {})
        clouds = data.get('clouds', {})
        sys = data.get('sys', {})

        # Calculate air quality impact from weather
        aqi_impact = calculate_weather_aqi_impact(data)

        weather_data = {
            'city': city_info['city'],
            'country': city_info['country'],
            'temperature': main.get('temp'),
            'feels_like': main.get('feels_like'),
            'humidity': main.get('humidity'),
            'pressure': main.get('pressure'),
            'wind_speed': wind.get('speed'),
            'wind_direction': wind.get('deg'),
            'cloudiness': clouds.get('all'),
            'weather_main': weather_info.get('main'),
            'weather_description': weather_info.get('description'),
            'visibility': data.get('visibility'),
            'sunrise': sys.get('sunrise'),
            'sunset': sys.get('sunset'),
            'aqi_impact': aqi_impact,
            'source': 'OpenWeatherMap',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"Weather data collected for {city_info['city']}")
        return weather_data

    except Exception as e:
        logger.error(f"OpenWeather processing error: {e}")
        return None

def get_basic_weather_estimation(city_info):
    """Fallback weather estimation based on location and time"""
    try:
        now = datetime.now()
        month = now.month
        hour = now.hour

        # Seasonal adjustments
        if month in [12, 1, 2]:  # Winter
            base_temp = -5 if city_info['country'] == 'Canada' else 10
        elif month in [3, 4, 5]:  # Spring
            base_temp = 10 if city_info['country'] == 'Canada' else 20
        elif month in [6, 7, 8]:  # Summer
            base_temp = 25 if city_info['country'] == 'Canada' else 30
        else:  # Fall
            base_temp = 15 if city_info['country'] == 'Canada' else 22

        # Time of day adjustment
        if 6 <= hour <= 18:  # Daytime
            temp_adjustment = 5
        else:  # Nighttime
            temp_adjustment = -5

        estimated_temp = base_temp + temp_adjustment

        # City-specific adjustments
        city_temp_adjustments = {
            "Los Angeles": 8, "Mexico City": 5, "Houston": 7,
            "Vancouver": -2, "Toronto": -3, "Montreal": -4
        }

        estimated_temp += city_temp_adjustments.get(city_info['city'], 0)

        # Simple weather condition based on season and time
        if month in [6, 7, 8]:  # Summer
            condition = "Clear" if hour < 20 else "Partly Cloudy"
        elif month in [12, 1, 2]:  # Winter
            condition = "Cloudy" if city_info['country'] == 'Canada' else "Clear"
        else:
            condition = "Partly Cloudy"

        return {
            'city': city_info['city'],
            'country': city_info['country'],
            'temperature': estimated_temp,
            'humidity': 65,
            'pressure': 1013,
            'wind_speed': 3.5,
            'weather_main': condition,
            'weather_description': f'{condition} skies',
            'aqi_impact': 'NEUTRAL',
            'source': 'Estimated',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'Estimated weather data'
        }

    except Exception as e:
        logger.error(f"Weather estimation error: {e}")
        return None

def calculate_weather_aqi_impact(weather_data):
    """Calculate how weather conditions affect air quality"""
    try:
        score = 0

        # Wind speed - higher wind disperses pollutants
        wind_speed = weather_data.get('wind', {}).get('speed', 0)
        if wind_speed < 2:
            score += 30  # Poor dispersion
        elif wind_speed < 5:
            score += 15  # Moderate dispersion
        else:
            score += 5   # Good dispersion

        # Humidity - high humidity can trap pollutants
        humidity = weather_data.get('main', {}).get('humidity', 50)
        if humidity > 80:
            score += 20
        elif humidity > 60:
            score += 10

        # Temperature inversion conditions (cold air trapped under warm)
        temp = weather_data.get('main', {}).get('temp', 15)
        if temp < 5:
            score += 15  # More likely inversion

        # Cloud cover - can trap pollutants
        clouds = weather_data.get('clouds', {}).get('all', 0)
        if clouds > 80:
            score += 10

        # Determine impact level
        if score >= 50:
            return "HIGH_NEGATIVE"
        elif score >= 30:
            return "MODERATE_NEGATIVE"
        elif score >= 15:
            return "LOW_NEGATIVE"
        else:
            return "POSITIVE"

    except Exception as e:
        logger.error(f"AQI impact calculation error: {e}")
        return "UNKNOWN"

# ---------------------------
# AIR QUALITY FUNCTIONS
# ---------------------------
def get_health_rating(pollutant_type, value):
    """Get health rating for a pollutant value"""
    if pollutant_type not in HEALTH_THRESHOLDS:
        return "UNKNOWN", "[?]", "No rating available"

    thresholds = HEALTH_THRESHOLDS[pollutant_type]

    if value <= thresholds["GOOD"]:
        return "GOOD", "[G]", thresholds["GOOD_DESC"]
    elif value <= thresholds["MODERATE"]:
        return "MODERATE", "[M]", thresholds["MODERATE_DESC"]
    elif value <= thresholds["BAD"]:
        return "UNHEALTHY", "[U]", thresholds["BAD_DESC"]
    else:
        return "VERY UNHEALTHY", "[VU]", "Dangerous pollution levels"

def get_iqair_city_data(city_info):
    """Get air quality data for a specific city from IQAir"""
    try:
        api_key = CONFIG["api_keys"]["iqair"]
        city = city_info["city"]
        state = city_info["state"]
        country = city_info["country"]

        url = "http://api.airvisual.com/v2/city"
        params = {
            'city': city,
            'state': state,
            'country': country,
            'key': api_key
        }

        logger.info(f"Fetching air quality data for {city}, {country}")
        response = requests.get(url, params=params, timeout=15)

        if response.status_code == 200:
            data = response.json()
            return process_iqair_response(data, city_info)
        else:
            logger.warning(f"API returned status {response.status_code} for {city}")
            return []

    except requests.exceptions.RequestException as e:
        logger.error(f"Network error for {city_info['city']}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error for {city_info['city']}: {e}")
        return []

def process_iqair_response(data, city_info):
    """Process IQAir API response"""
    results = []

    try:
        if 'data' in data and 'current' in data['data']:
            current = data['data']['current']
            pollution = current.get('pollution', {})

            city_name = f"{city_info['city']}, {city_info['country']}"

            # Process AQI and PM2.5
            aqius = pollution.get('aqius', 0)
            if aqius > 0:
                pm25 = aqi_to_pm25(aqius)
                rating, indicator, description = get_health_rating("PM2_5", pm25)

                results.append({
                    'pollutant': 'PM2_5',
                    'value': pm25,
                    'units': 'μg/m³',
                    'source': f'IQAir - {city_name}',
                    'rating': rating,
                    'indicator': indicator,
                    'description': description,
                    'aqi': aqius,
                    'city': city_info['city'],
                    'country': city_info['country'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            # Process O3 if available
            if pollution.get('o3'):
                o3_value = pollution['o3']
                rating, indicator, description = get_health_rating("O3", o3_value)
                results.append({
                    'pollutant': 'O3',
                    'value': o3_value,
                    'units': 'ppb',
                    'source': f'IQAir - {city_name}',
                    'rating': rating,
                    'indicator': indicator,
                    'description': description,
                    'city': city_info['city'],
                    'country': city_info['country'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

            # Process NO2 if available
            if pollution.get('no2'):
                no2_value = pollution['no2']
                rating, indicator, description = get_health_rating("NO2", no2_value)
                results.append({
                    'pollutant': 'NO2',
                    'value': no2_value,
                    'units': 'ppb',
                    'source': f'IQAir - {city_name}',
                    'rating': rating,
                    'indicator': indicator,
                    'description': description,
                    'city': city_info['city'],
                    'country': city_info['country'],
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })

    except Exception as e:
        logger.error(f"Error processing IQAir data: {e}")

    return results

def get_co2_estimation(city_info):
    """Get estimated CO2 levels for a city"""
    try:
        # Base CO2 level with city adjustments
        base_co2 = 420
        city_adjustments = {
            "New York": 25, "Los Angeles": 30, "Chicago": 20,
            "Toronto": 15, "Vancouver": 10, "Mexico City": 35,
            "Montreal": 18, "Houston": 22
        }

        adjustment = city_adjustments.get(city_info["city"], 20)
        current_hour = datetime.now().hour

        # Rush hour adjustment
        if 7 <= current_hour <= 9 or 16 <= current_hour <= 18:
            adjustment += 15

        estimated_co2 = base_co2 + adjustment

        # Get CO2 rating
        if estimated_co2 <= 450:
            rating, indicator, desc = "EXCELLENT", "[E]", "Fresh outdoor air"
        elif estimated_co2 <= 600:
            rating, indicator, desc = "GOOD", "[G]", "Typical urban air"
        elif estimated_co2 <= 1000:
            rating, indicator, desc = "MODERATE", "[M]", "Elevated CO2 levels"
        else:
            rating, indicator, desc = "POOR", "[P]", "High CO2 concentration"

        return {
            'pollutant': 'CO2',
            'value': estimated_co2,
            'units': 'ppm',
            'source': f'CO2 Estimate - {city_info["city"]}',
            'rating': rating,
            'indicator': indicator,
            'description': desc,
            'city': city_info['city'],
            'country': city_info['country'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'Estimated based on location and time'
        }

    except Exception as e:
        logger.error(f"CO2 estimation error: {e}")
        return None

def aqi_to_pm25(aqi):
    """Convert AQI to PM2.5 concentration"""
    if aqi <= 50:
        return (aqi * 12.0 / 50)
    elif aqi <= 100:
        return (12.1 + (aqi - 51) * (35.4 - 12.1) / 49)
    elif aqi <= 150:
        return (35.5 + (aqi - 101) * (55.4 - 35.5) / 49)
    else:
        return (55.5 + (aqi - 151) * (150.4 - 55.5) / 49)

# ---------------------------
# DATA COLLECTION
# ---------------------------
def collect_all_data():
    """Collect both air quality and weather data"""
    logger.info("Starting comprehensive data collection...")
    air_quality_data = []
    global weather_data

    weather_data = {}  # Reset weather data

    # Get data for each city
    for city in CONFIG["north_america_cities"]:
        try:
            # Get air quality data
            aq_data = get_iqair_city_data(city)
            if aq_data:
                air_quality_data.extend(aq_data)
                logger.info(f"Air quality data collected for {city['city']}")

            # Get CO2 estimation
            co2_data = get_co2_estimation(city)
            if co2_data:
                air_quality_data.append(co2_data)

            # Get weather data
            city_weather = get_weather_data(city)
            if city_weather:
                weather_key = f"{city['city']}_{city['country']}"
                weather_data[weather_key] = city_weather
                logger.info(f"Weather data collected for {city['city']}")

            time.sleep(1)  # Rate limiting

        except Exception as e:
            logger.error(f"Error processing city {city['city']}: {e}")
            continue

    logger.info(f"Collection complete. AQ measurements: {len(air_quality_data)}, Weather: {len(weather_data)}")
    return air_quality_data

# ---------------------------
# DISPLAY FUNCTIONS
# ---------------------------
def display_weather_impact(aqi_impact):
    """Display weather impact on air quality"""
    impact_descriptions = {
        "HIGH_NEGATIVE": "❌ Poor dispersion - pollutants may accumulate",
        "MODERATE_NEGATIVE": "⚠️ Fair dispersion - monitor conditions",
        "LOW_NEGATIVE": "🔶 Good dispersion - favorable conditions",
        "POSITIVE": "✅ Excellent dispersion - pollutants will disperse well",
        "NEUTRAL": "➖ Neutral conditions - typical dispersion",
        "UNKNOWN": "❓ Unknown impact - insufficient data"
    }
    return impact_descriptions.get(aqi_impact, "Unknown impact")

def display_results(air_quality_data, run_number):
    """Display the monitoring results with weather data"""
    global current_data
    current_data = air_quality_data

    print("\n" + "=" * 80)
    print(f"🛡️ SKYSHIELD - NORTH AMERICA AIR QUALITY & WEATHER")
    print(f"Update #{run_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    if not air_quality_data and not weather_data:
        print("❌ No data available. Please check:")
        print("   • Internet connection")
        print("   • API key validity")
        return

    # Display data by country
    countries = sorted(set([city['country'] for city in CONFIG['north_america_cities']]))

    for country in countries:
        print(f"\n🇺🇸 {country.upper()}:" if country == 'USA' else f"\n🇨🇦 {country.upper()}:" if country == 'Canada' else f"\n🇲🇽 {country.upper()}:")
        print("-" * 40)

        country_cities = [city for city in CONFIG['north_america_cities'] if city['country'] == country]

        for city_info in country_cities:
            city_key = f"{city_info['city']}_{city_info['country']}"

            # Display weather data
            if city_key in weather_data:
                weather = weather_data[city_key]
                print(f"\n📍 {city_info['city']}:")
                print(f"   🌡️  Temp: {weather['temperature']:.1f}°C")
                print(f"   💧 Humidity: {weather['humidity']}%")
                print(f"   💨 Wind: {weather['wind_speed']} m/s")
                print(f"   ☁️  Conditions: {weather['weather_description']}")
                print(f"   📊 AQI Impact: {display_weather_impact(weather['aqi_impact'])}")
                print(f"   📍 Source: {weather['source']}")

            # Display air quality data for this city
            city_aq_data = [d for d in air_quality_data if d['city'] == city_info['city'] and d['country'] == country]

            if city_aq_data:
                print(f"   🏭 Air Quality:")
                for aq in city_aq_data:
                    if aq['pollutant'] == 'CO2':
                        print(f"      CO₂: {aq['value']:.0f} ppm {aq['indicator']} ({aq['rating']})")
                    else:
                        print(f"      {aq['pollutant']}: {aq['value']:.1f} {aq['units']} {aq['indicator']} ({aq['rating']})")
            else:
                print(f"   🏭 Air Quality: No data available")

    # Summary
    print(f"\n📊 REGIONAL SUMMARY:")
    print(f"   Countries monitored: {len(countries)}")
    print(f"   Cities with weather data: {len(weather_data)}")
    print(f"   Total AQ measurements: {len(air_quality_data)}")

    # Weather impact analysis
    negative_impact = sum(1 for w in weather_data.values() if 'NEGATIVE' in w.get('aqi_impact', ''))
    if negative_impact > 0:
        print(f"   ⚠️  Poor dispersion conditions in {negative_impact} cities")
    else:
        print(f"   ✅ Good dispersion conditions across region")

    # Air quality analysis
    unhealthy_aq = [item for item in air_quality_data if item['rating'] in ['UNHEALTHY', 'VERY UNHEALTHY', 'POOR']]
    if unhealthy_aq:
        print(f"   🚨 Unhealthy air quality: {len(unhealthy_aq)} measurements")
    else:
        print(f"   ✅ Air quality: Generally acceptable")

    print("=" * 80)

# ---------------------------
# MONITORING SYSTEM
# ---------------------------
def perform_update():
    """Perform a single update cycle"""
    global run_count
    run_count += 1

    logger.info(f"Performing update #{run_count}")
    try:
        data = collect_all_data()
        display_results(data, run_count)

        # Save data
        if data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Save air quality data
            aq_filename = f"sky_shield_aq_{timestamp}.csv"
            df_aq = pd.DataFrame(data)
            df_aq.to_csv(aq_filename, index=False)

            # Save weather data
            if weather_data:
                weather_filename = f"sky_shield_weather_{timestamp}.csv"
                df_weather = pd.DataFrame(weather_data.values())
                df_weather.to_csv(weather_filename, index=False)
                print(f"💾 Data saved to: {aq_filename} and {weather_filename}")
            else:
                print(f"💾 Air quality data saved to: {aq_filename}")

    except Exception as e:
        logger.error(f"Update error: {e}")
        print(f"❌ Update failed: {e}")

def start_monitoring():
    """Start the continuous monitoring"""
    global monitoring_active

    print("\n" + "=" * 80)
    print("🛡️ STARTING SKYSHIELD COMPREHENSIVE MONITORING")
    print("=" * 80)
    print("NASA Space Apps Challenge 2024 - Team BlueForce")
    print("Creator: Ahmed Wael")
    print("\nMonitoring Configuration:")
    print(f"   • Region: North America")
    print(f"   • Countries: USA, Canada, Mexico")
    print(f"   • Cities: {len(CONFIG['north_america_cities'])}")
    print(f"   • Data: Air Quality + Weather")
    print(f"   • Update Interval: {CONFIG['update_interval_minutes']} minutes")
    print("\nPress Ctrl+C to stop monitoring")
    print("=" * 80)

    # Initial update
    perform_update()

    # Start auto-updates
    def auto_update():
        while monitoring_active:
            time.sleep(CONFIG['update_interval_minutes'] * 60)
            if monitoring_active:
                perform_update()

    update_thread = threading.Thread(target=auto_update, daemon=True)
    update_thread.start()

    # Keep main thread alive
    try:
        while monitoring_active:
            time.sleep(1)
    except KeyboardInterrupt:
        monitoring_active = False
        print("\n\n🛑 Monitoring stopped by user")
        print("Thank you for using SkyShield!")

# ---------------------------
# MAIN EXECUTION
# ---------------------------
def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("🛡️ SKYSHIELD - NASA SPACE APPS CHALLENGE 2024")
    print("North America Air Quality & Weather Monitoring System")
    print("=" * 80)

    # Test connectivity
    print("🔍 Testing system connectivity...")
    try:
        # Test basic internet
        response = requests.get("http://api.airvisual.com/v2/nearest_city?key=demo", timeout=10)
        if response.status_code == 200:
            print("✅ Internet connection: OK")
        else:
            print("❌ AirVisual API: Limited access")
    except:
        print("❌ Internet connection: Issues detected")

    # Start monitoring
    start_monitoring()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 SkyShield terminated by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        logger.error(f"Fatal error: {e}")
