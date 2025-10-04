
# ================================================================
# Project   : SkyShield
# Team      : BluraForce
# Creator   : Ahmed Wael
# Event     : NASA Space Apps Challenge
# Date      : 2025
#
# Copyright (c) 2025 BluraForce Team
# All rights reserved.
#
# This code is part of the SkyShield project.
# Unauthorized copying, modification, distribution, or use of this
# code, via any medium, is strictly prohibited without written consent
# from the BluraForce Team.
# ================================================================
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
Description: {challenge is to develop a web-based app that forecasts air quality by integrating real-time TEMPO data with ground-based air quality measurements and weather data}
Last Updated: {10/4/2025}

NASA Challenge: {Monitoring of Pollution (TEMPO) mission is revolutionizing air quality monitoring across North America by enabling better forecasts and reducing pollutant exposure}
"""

"""
SkyShield - North America Air Quality Monitoring with Weather Data
NASA Space Apps Challenge 2025 - Team BlueForce
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
        "iqair": os.environ.get("IQAIR_API_KEY", ""),
        "openweather": os.environ.get("OPENWEATHER_API_KEY", "")
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
# AQI HELPER FUNCTIONS
# ---------------------------
def get_aqi_description(aqi_value):
    """Get descriptive text for AQI values"""
    if aqi_value <= 50:
        return "(Good)"
    elif aqi_value <= 100:
        return "(Moderate)"
    elif aqi_value <= 150:
        return "(Unhealthy for Sensitive Groups)"
    elif aqi_value <= 200:
        return "(Unhealthy)"
    elif aqi_value <= 300:
        return "(Very Unhealthy)"
    else:
        return "(Hazardous)"

def get_aqi_rating(aqi):
    """Get rating for AQI value"""
    if aqi <= 50:
        return "GOOD"
    elif aqi <= 100:
        return "MODERATE"
    elif aqi <= 150:
        return "UNHEALTHY FOR SENSITIVE GROUPS"
    elif aqi <= 200:
        return "UNHEALTHY"
    elif aqi <= 300:
        return "VERY UNHEALTHY"
    else:
        return "HAZARDOUS"

def get_aqi_indicator(aqi):
    """Get indicator for AQI value"""
    if aqi <= 50:
        return "[G]"
    elif aqi <= 100:
        return "[M]"
    elif aqi <= 150:
        return "[USG]"
    elif aqi <= 200:
        return "[U]"
    elif aqi <= 300:
        return "[VU]"
    else:
        return "[H]"

def pm25_to_aqi(pm25):
    """Convert PM2.5 concentration to AQI value"""
    try:
        if pm25 <= 12.0:
            return int((pm25 * 50) / 12.0)
        elif pm25 <= 35.4:
            return int(51 + (pm25 - 12.1) * (100 - 51) / (35.4 - 12.1))
        elif pm25 <= 55.4:
            return int(101 + (pm25 - 35.5) * (150 - 101) / (55.4 - 35.5))
        elif pm25 <= 150.4:
            return int(151 + (pm25 - 55.5) * (200 - 151) / (150.4 - 55.5))
        elif pm25 <= 250.4:
            return int(201 + (pm25 - 150.5) * (300 - 201) / (250.4 - 150.5))
        else:
            return int(301 + (pm25 - 250.5) * (500 - 301) / (500.4 - 250.5))
    except Exception as e:
        logger.error(f"PM2.5 to AQI conversion error: {e}")
        return 0

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
            'units': 'metric'
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

        # Calculate air quality impact from weather - returns numeric score
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
            'aqi_impact': aqi_impact,  # Now numeric score
            'source': 'OpenWeatherMap',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        logger.info(f"Weather data collected for {city_info['city']}")
        return weather_data

    except Exception as e:
        logger.error(f"OpenWeather processing error: {e}")
        return None

def calculate_weather_aqi_impact(weather_data):
    """Calculate how weather conditions affect air quality - returns score 0-100"""
    try:
        score = 0
        max_possible_score = 75  # Maximum negative impact score

        # Wind speed - higher wind disperses pollutants (lower score is better)
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

        # Convert to 0-100 scale where 0 is best, 100 is worst
        impact_score = min(100, int((score / max_possible_score) * 100))

        return impact_score

    except Exception as e:
        logger.error(f"AQI impact calculation error: {e}")
        return 50  # Default neutral score

def display_weather_impact(impact_score):
    """Display weather impact as a numeric score with description"""
    if impact_score <= 20:
        return f"✅ {impact_score}/100 - Excellent dispersion"
    elif impact_score <= 40:
        return f"🟢 {impact_score}/100 - Good dispersion"
    elif impact_score <= 60:
        return f"🟡 {impact_score}/100 - Moderate dispersion"
    elif impact_score <= 80:
        return f"🟠 {impact_score}/100 - Poor dispersion"
    else:
        return f"🔴 {impact_score}/100 - Very poor dispersion"

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

        # Estimate impact score based on conditions
        if condition == "Clear" and estimated_temp > 20:
            impact_score = 25  # Good conditions
        elif condition == "Cloudy":
            impact_score = 65  # Poor conditions
        else:
            impact_score = 45  # Moderate conditions

        return {
            'city': city_info['city'],
            'country': city_info['country'],
            'temperature': estimated_temp,
            'humidity': 65,
            'pressure': 1013,
            'wind_speed': 3.5,
            'weather_main': condition,
            'weather_description': f'{condition} skies',
            'aqi_impact': impact_score,  # Changed from 'NEUTRAL' to numeric score
            'source': 'Estimated',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'Estimated weather data'
        }

    except Exception as e:
        logger.error(f"Weather estimation error: {e}")
        return None

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
    """Process IQAir API response with enhanced AQI and PM2.5 data"""
    results = []

    try:
        if 'data' in data and 'current' in data['data']:
            current = data['data']['current']
            pollution = current.get('pollution', {})

            city_name = f"{city_info['city']}, {city_info['country']}"

            # Process AQI and PM2.5 - ENHANCED DISPLAY
            aqius = pollution.get('aqius', 0)
            pm25_concentration = pollution.get('p2', 0)  # Try to get direct PM2.5 measurement

            # If we have AQI but no direct PM2.5, calculate it
            if aqius > 0 and pm25_concentration == 0:
                pm25_concentration = aqi_to_pm25(aqius)

            # If we have direct PM2.5 but no AQI, calculate AQI
            if pm25_concentration > 0 and aqius == 0:
                aqius = pm25_to_aqi(pm25_concentration)

            # Always create PM2.5 entry if we have data
            if pm25_concentration > 0:
                rating, indicator, description = get_health_rating("PM2_5", pm25_concentration)

                # Enhanced PM2.5 entry
                results.append({
                    'pollutant': 'PM2_5',
                    'value': pm25_concentration,
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

                # Also create a separate AQI entry for easy access
                if aqius > 0:
                    results.append({
                        'pollutant': 'US_AQI',
                        'value': aqius,
                        'units': 'AQI',
                        'source': f'IQAir - {city_name}',
                        'rating': get_aqi_rating(aqius),
                        'indicator': get_aqi_indicator(aqius),
                        'description': get_aqi_description(aqius),
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

def get_fallback_pm25(city_info):
    """Create fallback PM2.5 estimation when API fails"""
    try:
        # Base PM2.5 levels with city adjustments
        base_pm25 = 15.0
        city_adjustments = {
            "New York": 8.0, "Los Angeles": 12.0, "Chicago": 6.0,
            "Toronto": 5.0, "Vancouver": 3.0, "Mexico City": 18.0,
            "Montreal": 4.0, "Houston": 9.0
        }

        adjustment = city_adjustments.get(city_info["city"], 7.0)
        current_hour = datetime.now().hour

        # Rush hour adjustment
        if 7 <= current_hour <= 9 or 16 <= current_hour <= 18:
            adjustment += 5.0

        # Weather impact adjustment
        city_key = f"{city_info['city']}_{city_info['country']}"
        if city_key in weather_data:
            weather_impact = weather_data[city_key].get('aqi_impact', 50)
            # Higher impact score = worse dispersion = higher PM2.5
            if weather_impact > 70:
                adjustment += 8.0
            elif weather_impact > 50:
                adjustment += 4.0

        estimated_pm25 = base_pm25 + adjustment

        # Calculate AQI from PM2.5
        estimated_aqi = pm25_to_aqi(estimated_pm25)
        rating, indicator, description = get_health_rating("PM2_5", estimated_pm25)

        return {
            'pollutant': 'PM2_5',
            'value': estimated_pm25,
            'units': 'μg/m³',
            'source': f'Estimated - {city_info["city"]}',
            'rating': rating,
            'indicator': indicator,
            'description': description,
            'aqi': estimated_aqi,
            'city': city_info['city'],
            'country': city_info['country'],
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'note': 'Estimated PM2.5 based on location and conditions'
        }

    except Exception as e:
        logger.error(f"Fallback PM2.5 estimation error: {e}")
        return None

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
            else:
                # Fallback: Create estimated PM2.5 data if no API data
                pm25_fallback = get_fallback_pm25(city)
                if pm25_fallback:
                    air_quality_data.append(pm25_fallback)
                    logger.info(f"Fallback PM2.5 data created for {city['city']}")

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
def display_results(air_quality_data, run_number):
    """Display the monitoring results with enhanced AQI and PM2.5 visibility"""
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

            # Display air quality data for this city - PRIORITIZE AQI and PM2.5
            city_aq_data = [d for d in air_quality_data if d['city'] == city_info['city'] and d['country'] == country]

            if city_aq_data:
                print(f"   🏭 Air Quality:")

                # Show PM2.5 FIRST and most prominently
                pm25_data = [d for d in city_aq_data if d['pollutant'] == 'PM2_5']
                if pm25_data:
                    pm25 = pm25_data[0]
                    source_indicator = "📡" if "IQAir" in pm25['source'] else "📊"
                    print(f"      {source_indicator} PM2.5: {pm25['value']:.1f} μg/m³ {pm25['indicator']}")
                    print(f"         {pm25['description']}")
                    if 'note' in pm25:
                        print(f"         ⚠️  {pm25['note']}")

                # Show AQI if available
                aqi_data = [d for d in city_aq_data if 'aqi' in d]
                if aqi_data:
                    aqi = aqi_data[0]['aqi']
                    # Color code AQI
                    if aqi <= 50:
                        aqi_color = "🟢"  # Good
                    elif aqi <= 100:
                        aqi_color = "🟡"  # Moderate
                    elif aqi <= 150:
                        aqi_color = "🟠"  # Unhealthy for sensitive
                    elif aqi <= 200:
                        aqi_color = "🔴"  # Unhealthy
                    elif aqi <= 300:
                        aqi_color = "🟣"  # Very unhealthy
                    else:
                        aqi_color = "💀"  # Hazardous

                    print(f"      {aqi_color} US AQI: {aqi} {get_aqi_description(aqi)}")

                # Show other pollutants
                other_pollutants = [d for d in city_aq_data if d['pollutant'] not in ['PM2_5'] and 'aqi' not in d]
                for pollutant in other_pollutants:
                    if pollutant['pollutant'] == 'CO2':
                        print(f"      🌫️  CO₂: {pollutant['value']:.0f} ppm {pollutant['indicator']}")
                    elif pollutant['pollutant'] == 'O3':
                        print(f"      ⚡ O₃: {pollutant['value']:.1f} ppb {pollutant['indicator']}")
                    elif pollutant['pollutant'] == 'NO2':
                        print(f"      🚗 NO₂: {pollutant['value']:.1f} ppb {pollutant['indicator']}")
            else:
                print(f"   🏭 Air Quality: No data available")

    # Enhanced Summary Section
    print(f"\n📊 REGIONAL AIR QUALITY SUMMARY:")
    print(f"   Countries monitored: {len(countries)}")
    print(f"   Cities with weather data: {len(weather_data)}")
    print(f"   Total AQ measurements: {len(air_quality_data)}")

    # AQI Analysis
    aqi_values = [d['aqi'] for d in air_quality_data if 'aqi' in d]
    if aqi_values:
        avg_aqi = sum(aqi_values) / len(aqi_values)
        max_aqi = max(aqi_values)
        min_aqi = min(aqi_values)

        print(f"\n   📈 AQI Statistics:")
        print(f"      Average AQI: {avg_aqi:.1f} {get_aqi_description(avg_aqi)}")
        print(f"      Highest AQI: {max_aqi} {get_aqi_description(max_aqi)}")
        print(f"      Lowest AQI: {min_aqi} {get_aqi_description(min_aqi)}")

    # PM2.5 Analysis
    pm25_values = [d['value'] for d in air_quality_data if d['pollutant'] == 'PM2_5']
    if pm25_values:
        avg_pm25 = sum(pm25_values) / len(pm25_values)
        max_pm25 = max(pm25_values)

        print(f"\n   💨 PM2.5 Statistics:")
        print(f"      Average PM2.5: {avg_pm25:.1f} μg/m³")
        print(f"      Highest PM2.5: {max_pm25:.1f} μg/m³")

        # Health impact summary
        unhealthy_pm25 = len([v for v in pm25_values if v > HEALTH_THRESHOLDS['PM2_5']['MODERATE']])
        if unhealthy_pm25 > 0:
            print(f"      ⚠️  Unhealthy PM2.5 in {unhealthy_pm25} cities")

    # Weather impact analysis - UPDATED for numeric scores
    impact_scores = [w.get('aqi_impact', 50) for w in weather_data.values()]
    if impact_scores:
        avg_impact = sum(impact_scores) / len(impact_scores)
        poor_conditions = len([s for s in impact_scores if s > 60])

        print(f"\n   🌤️  Weather Impact Analysis:")
        print(f"      Average Dispersion Score: {avg_impact:.1f}/100")
        if avg_impact <= 40:
            print(f"      ✅ Generally favorable dispersion conditions")
        elif avg_impact <= 70:
            print(f"      ⚠️  Mixed dispersion conditions")
        else:
            print(f"      🚨 Poor dispersion conditions across region")

        if poor_conditions > 0:
            print(f"      ⚠️  Poor dispersion in {poor_conditions} cities")

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
    print("NASA Space Apps Challenge 2025 - Team BlueForce")
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
# TEST FUNCTION
# ---------------------------
def test_aqi_pm25_display():
    """Test function to verify AQI and PM2.5 display"""
    test_data = [
        {
            'pollutant': 'PM2_5',
            'value': 25.4,
            'units': 'μg/m³',
            'source': 'IQAir - New York, USA',
            'rating': 'MODERATE',
            'indicator': '[M]',
            'description': 'Moderate - acceptable air quality',
            'aqi': 78,
            'city': 'New York',
            'country': 'USA',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'pollutant': 'US_AQI',
            'value': 78,
            'units': 'AQI',
            'source': 'IQAir - New York, USA',
            'rating': 'MODERATE',
            'indicator': '[M]',
            'description': '(Moderate)',
            'city': 'New York',
            'country': 'USA',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    ]

    print("🧪 TESTING AQI & PM2.5 DISPLAY:")
    display_results(test_data, 999)


# ---------------------------
# MAIN EXECUTION
# ---------------------------
def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("🛡️ SKYSHIELD - NASA SPACE APPS CHALLENGE 2025")
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
