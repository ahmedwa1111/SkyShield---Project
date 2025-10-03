
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
from bs4 import BeautifulSoup


# ---------------------------
# Setup logging with Windows compatibility
# ---------------------------
def setup_logging():
    """Setup logging with proper encoding handling for Windows"""
    # Remove all handlers associated with the root logger
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create formatter without emojis for Windows compatibility
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler with encoding fix
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler('newyork_air_quality.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Initialize logging
logger = setup_logging()

# ---------------------------
# CONFIGURATION FOR NEW YORK
# ---------------------------
CONFIG = {
    "location": {
        "name": "New York, USA",
        "lat": 40.7128,
        "lon": -74.0060,
        "city": "New York"
    },
    "update_interval_minutes": 30,
    "data_sources": {
        "iqair": "https://api.airvisual.com/v2/",
        "open_aq": "https://api.openaq.org/v2/",
        "epa": "https://www.airnow.gov/",
        "weather_gov": "https://api.weather.gov/"
    },
    "api_keys": {
        "iqair": "f60e848b-f405-4bfe-a096-c9935e595165"
    }
}

# ---------------------------
# HEALTH THRESHOLDS (Based on US EPA standards)
# ---------------------------
HEALTH_THRESHOLDS = {
    "PM2_5": {
        "GOOD": 12, "MODERATE": 35, "BAD": 55, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - healthy air quality",
        "MODERATE_DESC": "Moderate - acceptable air quality",
        "BAD_DESC": "Unhealthy - sensitive groups affected"
    },
    "PM10": {
        "GOOD": 54, "MODERATE": 154, "BAD": 254, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - healthy air quality",
        "MODERATE_DESC": "Moderate - acceptable air quality",
        "BAD_DESC": "Unhealthy - sensitive groups affected"
    },
    "NO2": {
        "GOOD": 53, "MODERATE": 100, "BAD": 360, "UNITS": "ppb",
        "GOOD_DESC": "Good - low vehicle pollution",
        "MODERATE_DESC": "Moderate - medium vehicle pollution",
        "BAD_DESC": "Unhealthy - high vehicle pollution"
    },
    "O3": {
        "GOOD": 54, "MODERATE": 70, "BAD": 85, "UNITS": "ppb",
        "GOOD_DESC": "Good - low ozone levels",
        "MODERATE_DESC": "Moderate - increased ozone",
        "BAD_DESC": "Unhealthy - high ozone levels"
    },
    "SO2": {
        "GOOD": 35, "MODERATE": 75, "BAD": 185, "UNITS": "ppb",
        "GOOD_DESC": "Good - low industrial pollution",
        "MODERATE_DESC": "Moderate - medium industrial pollution",
        "BAD_DESC": "Unhealthy - high industrial pollution"
    },
    "CO": {
        "GOOD": 4.4, "MODERATE": 9.4, "BAD": 12.4, "UNITS": "ppm",
        "GOOD_DESC": "Good - clean combustion",
        "MODERATE_DESC": "Moderate - incomplete combustion",
        "BAD_DESC": "Unhealthy - poor combustion"
    }
}

# Global variables for monitoring
current_data = []
monitoring_active = True
run_count = 0


# ---------------------------
# NEW YORK DATA SOURCES
# ---------------------------
def get_iqair_data():
    """Get comprehensive data from IQAir/airvisual API for New York"""
    try:
        api_key = CONFIG["api_keys"]["iqair"]
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]

        # Get nearest city data
        url = f"http://api.airvisual.com/v2/nearest_city?lat={lat}&lon={lon}&key={api_key}"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return process_iqair_data(data)
        else:
            logger.warning("IQAir API returned status: %s", response.status_code)
            return []

    except Exception as e:
        logger.error("IQAir error: %s", e)
        return []


def process_iqair_data(data):
    """Process IQAir API data with comprehensive pollutant information"""
    results = []

    try:
        if 'data' in data and 'current' in data['data']:
            current = data['data']['current']
            pollution = current.get('pollution', {})
            weather = current.get('weather', {})

            # Process PM2.5 from AQI
            pm25_aqi = pollution.get('aqius', 0)
            if pm25_aqi > 0:
                pm25_conc = aqi_to_pm25(pm25_aqi)
                rating, indicator, description = get_health_rating("PM2_5", pm25_conc)

                results.append({
                    'pollutant': "PM2_5",
                    'value': pm25_conc,
                    'units': HEALTH_THRESHOLDS["PM2_5"]["UNITS"],
                    'source': f"IQAir - {data['data']['city']}",
                    'rating': rating,
                    'indicator': indicator,
                    'description': description,
                    'aqi': pm25_aqi,
                    'type': 'GROUND'
                })

            # Process other pollutants if available
            other_pollutants = {
                'no2': ('NO2', pollution.get('no2')),
                'o3': ('O3', pollution.get('o3')),
                'so2': ('SO2', pollution.get('so2')),
                'co': ('CO', pollution.get('co'))
            }

            for poll_key, (poll_name, value) in other_pollutants.items():
                if value and value > 0:
                    # Convert units for US standards if needed
                    if poll_name == 'CO' and value < 10:  # Likely in mg/m³, convert to ppm
                        value = value * 0.87  # Approximate conversion

                    rating, indicator, description = get_health_rating(poll_name, value)

                    results.append({
                        'pollutant': poll_name,
                        'value': value,
                        'units': HEALTH_THRESHOLDS[poll_name]["UNITS"],
                        'source': f"IQAir - {data['data']['city']}",
                        'rating': rating,
                        'indicator': indicator,
                        'description': description,
                        'type': 'GROUND'
                    })

            logger.info("IQAir data processed successfully - %s pollutants found", len(results))

        return results

    except Exception as e:
        logger.error("IQAir processing error: %s", e)
        return []


def aqi_to_pm25(aqi):
    """Convert AQI to PM2.5 concentration (μg/m³) - US EPA standard"""
    # Based on US EPA conversion formula
    if aqi <= 50:
        return (aqi * 12.0 / 50)
    elif aqi <= 100:
        return (12.1 + (aqi - 51) * (35.4 - 12.1) / 49)
    elif aqi <= 150:
        return (35.5 + (aqi - 101) * (55.4 - 35.5) / 49)
    elif aqi <= 200:
        return (55.5 + (aqi - 151) * (150.4 - 55.5) / 49)
    elif aqi <= 300:
        return (150.5 + (aqi - 201) * (250.4 - 150.5) / 99)
    elif aqi <= 400:
        return (250.5 + (aqi - 301) * (350.4 - 250.5) / 99)
    else:
        return (350.5 + (aqi - 401) * (500.4 - 350.5) / 99)


def get_openaq_data():
    """Get data from OpenAQ platform for New York"""
    try:
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]

        # Get latest measurements for New York area
        url = f"https://api.openaq.org/v2/latest?coordinates={lat},{lon}&radius=25000&limit=15"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return process_openaq_data(data)
        else:
            logger.warning("OpenAQ API returned status: %s", response.status_code)
            return []

    except Exception as e:
        logger.error("OpenAQ error: %s", e)
        return []


def process_openaq_data(data):
    """Process OpenAQ data for US standards"""
    results = []

    try:
        if 'results' in data:
            for station in data['results'][:8]:  # First 8 stations
                location_name = station.get('location', 'Unknown')
                measurements = station.get('measurements', [])

                for measurement in measurements:
                    param = measurement['parameter'].upper()
                    value = measurement['value']
                    unit = measurement.get('unit', 'unknown')

                    # Map to our pollutant types
                    poll_map = {
                        'PM25': 'PM2_5', 'PM10': 'PM10',
                        'NO2': 'NO2', 'O3': 'O3',
                        'SO2': 'SO2', 'CO': 'CO'
                    }

                    if param in poll_map:
                        mapped_poll = poll_map[param]

                        # Convert units to US standards if necessary
                        if mapped_poll == 'CO' and unit == 'µg/m³':
                            value = value * 0.00087  # Convert µg/m³ to ppm
                            unit = 'ppm'
                        elif mapped_poll in ['NO2', 'O3', 'SO2'] and unit == 'µg/m³':
                            # Convert to ppb for gases (approximate)
                            if mapped_poll == 'NO2':
                                value = value * 0.53  # µg/m³ to ppb
                            elif mapped_poll == 'O3':
                                value = value * 0.50  # µg/m³ to ppb
                            elif mapped_poll == 'SO2':
                                value = value * 0.38  # µg/m³ to ppb
                            unit = 'ppb'

                        rating, indicator, description = get_health_rating(mapped_poll, value)

                        results.append({
                            'pollutant': mapped_poll,
                            'value': value,
                            'units': unit,
                            'source': f"OpenAQ: {location_name}",
                            'rating': rating,
                            'indicator': indicator,
                            'description': description,
                            'type': 'GROUND'
                        })

        logger.info("OpenAQ data processed - %s measurements found", len(results))
        return results

    except Exception as e:
        logger.error("OpenAQ processing error: %s", e)
        return []


def get_epa_data():
    """Get data from EPA AirNow API (when available)"""
    try:
        # EPA AirNow API requires registration, so we'll use as backup
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]

        # This is a placeholder for EPA API integration
        # In production, you would add proper EPA API calls here

        return []
    except Exception as e:
        logger.debug("EPA data not available: %s", e)
        return []


def get_weather_data():
    """Get weather data for New York"""
    try:
        # Using OpenMeteo for reliable weather data
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,cloud_cover,visibility&temperature_unit=fahrenheit&wind_speed_unit=mph"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data['current']

            # Calculate air quality index based on weather
            aqi = calculate_aqi_from_weather(current)

            return {
                'temperature': current['temperature_2m'],
                'humidity': current['relative_humidity_2m'],
                'pressure': current['pressure_msl'],
                'wind_speed': current['wind_speed_10m'],
                'wind_direction': current['wind_direction_10m'],
                'clouds': current['cloud_cover'],
                'visibility': current['visibility'] / 1609.34,  # Convert to miles
                'aqi_estimate': aqi,
                'source': 'Open-Meteo'
            }
    except Exception as e:
        logger.error("Weather error: %s", e)
        return None


# ---------------------------
# HEALTH RATING FUNCTIONS
# ---------------------------
def get_health_rating(pollutant_type, value):
    """Get health rating for a pollutant value using US standards"""
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


def get_health_advice(pollutant_type, rating):
    """Get health advice based on rating"""
    advice = {
        "GOOD": "No precautions needed - ideal for outdoor activities",
        "MODERATE": "Generally acceptable for most people",
        "UNHEALTHY": "Sensitive groups should reduce outdoor activity",
        "VERY UNHEALTHY": "Everyone should reduce outdoor exertion"
    }
    return advice.get(rating, "Check local air quality advisories")


def calculate_aqi_from_weather(weather):
    """Estimate AQI from weather conditions"""
    score = 0

    # Low wind = poor dispersion
    if weather['wind_speed_10m'] < 5:  # mph
        score += 30
    elif weather['wind_speed_10m'] < 10:
        score += 15

    # High humidity can trap pollutants
    if weather['relative_humidity_2m'] > 80:
        score += 20

    # Low visibility indicates pollution
    if weather['visibility'] < 3:  # miles
        score += 40
    elif weather['visibility'] < 6:
        score += 20

    return min(100, score)


# ---------------------------
# DATA COLLECTION MASTER FUNCTION
# ---------------------------
def collect_all_air_quality_data():
    """Collect data from all available sources for New York"""
    logger.info("Collecting New York air quality data...")

    all_data = []

    # Try IQAir first (most reliable with API key)
    logger.info("Accessing IQAir data...")
    iqair_data = get_iqair_data()
    all_data.extend(iqair_data)

    # Try OpenAQ as secondary source
    logger.info("Accessing OpenAQ data...")
    openaq_data = get_openaq_data()
    all_data.extend(openaq_data)

    # Try EPA as tertiary source
    if len(all_data) < 2:  # If we don't have much data
        logger.info("Accessing EPA data...")
        epa_data = get_epa_data()
        all_data.extend(epa_data)

    logger.info("Total %s pollution measurements found", len(all_data))
    return all_data


# ---------------------------
# DISPLAY RESULTS
# ---------------------------
def display_results(air_quality_data, weather_data, run_number=0):
    """Display comprehensive results"""
    global current_data

    # Update current data
    current_data = air_quality_data

    print("\n" + "=" * 80)
    print(f"NEW YORK AIR QUALITY MONITORING - UPDATE #{run_number}")
    print("=" * 80)
    print(f"Location: {CONFIG['location']['name']}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Next update in: {CONFIG['update_interval_minutes']} minutes")
    print(f"Data Sources: IQAir, OpenAQ, EPA")

    print(f"\n--- POLLUTION LEVELS ({len(current_data)} measurements) ---")

    if current_data:
        # Group by pollutant
        pollutants = {}
        for data in current_data:
            if data['pollutant'] not in pollutants:
                pollutants[data['pollutant']] = []
            pollutants[data['pollutant']].append(data)

        for poll, measurements in pollutants.items():
            print(f"\n{poll}:")
            for data in measurements:
                value_str = f"{data['value']:.1f}" if data['value'] < 1000 else f"{data['value']:.2e}"

                print(f"  {data['indicator']} {value_str} {data['units']} - {data['rating']}")
                print(f"     Source: {data['source']}")
                print(f"     Description: {data['description']}")

                advice = get_health_advice(data['pollutant'], data['rating'])
                print(f"     Advice: {advice}")

                # Show AQI if available
                if 'aqi' in data:
                    print(f"     AQI: {data['aqi']}")
    else:
        print("   No air quality data available")
        print("   This is normal - try again in a few minutes")
        print("   Data sources might be temporarily unavailable")

    print(f"\n--- WEATHER CONDITIONS ---")
    if weather_data:
        print(f"Temperature: {weather_data['temperature']:.1f}°F")
        print(f"Humidity: {weather_data['humidity']}%")
        print(f"Wind: {weather_data['wind_speed']:.1f} mph from {weather_data['wind_direction']}°")
        print(f"Pressure: {weather_data['pressure']:.1f} hPa")
        print(f"Clouds: {weather_data['clouds']}%")
        print(f"Visibility: {weather_data['visibility']:.1f} miles")
        print(f"Estimated AQI: {weather_data['aqi_estimate']}/100")
        print(f"Source: {weather_data.get('source', 'Unknown')}")

        if weather_data['aqi_estimate'] > 50:
            print("   WARNING: Weather conditions may trap pollutants")
        else:
            print("   Favorable conditions for pollution dispersion")

    print(f"\n--- OVERALL HEALTH ASSESSMENT ---")
    if current_data:
        ratings = [data['rating'] for data in current_data]
        if any(r in ["UNHEALTHY", "VERY UNHEALTHY"] for r in ratings):
            print("POOR AIR QUALITY - Take precautions")
            print("   • Sensitive groups should avoid outdoor activity")
            print("   • Consider wearing a mask outdoors")
            print("   • Close windows during high pollution hours")
        elif any(r == "MODERATE" for r in ratings):
            print("MODERATE AIR QUALITY - Generally acceptable")
            print("   • Unusually sensitive people should take care")
            print("   • OK for most outdoor activities")
        else:
            print("GOOD AIR QUALITY - Healthy conditions")
            print("   • No precautions needed")
            print("   • Enjoy outdoor activities")
    else:
        print("INSUFFICIENT DATA - Check local air quality indexes")
        print("   • Try running the script again in 1-2 hours")
        print("   • Check internet connection")

    print("=" * 80)


# ---------------------------
# AUTO-UPDATE FUNCTIONALITY
# ---------------------------
def perform_update():
    """Perform a single update cycle"""
    global run_count

    run_count += 1
    logger.info("=" * 60)
    logger.info("PERFORMING AUTOMATIC UPDATE #%s", run_count)
    logger.info("=" * 60)

    try:
        # Collect air quality data
        air_quality_data = collect_all_air_quality_data()

        # Get weather data
        weather_data = get_weather_data()

        # Display results
        display_results(air_quality_data, weather_data, run_count)

        # Save data
        if air_quality_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            df = pd.DataFrame(air_quality_data)
            filename = f"newyork_air_quality_{timestamp}.csv"
            df.to_csv(filename, index=False, encoding='utf-8')
            logger.info("Data saved: %s", filename)
            print(f"\nDetailed data saved to: {filename}")

        logger.info("Update #%s completed successfully", run_count)

    except Exception as e:
        logger.error("Error during update #%s: %s", run_count, e)


def auto_update_worker():
    """Worker function for automatic updates"""
    interval_seconds = CONFIG['update_interval_minutes'] * 60

    logger.info("Auto-update worker started. Interval: %s seconds", interval_seconds)

    while monitoring_active:
        try:
            # Wait for the specified interval
            time.sleep(interval_seconds)

            if monitoring_active:
                perform_update()

        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error("Error in auto-update worker: %s", e)
            # Wait a bit before retrying
            time.sleep(60)


def start_monitoring():
    """Start the continuous monitoring"""
    global monitoring_active

    print("\n" + "=" * 80)
    print("STARTING CONTINUOUS AIR QUALITY MONITORING")
    print("=" * 80)
    print(f"Location: {CONFIG['location']['name']}")
    print(f"Update Interval: Every {CONFIG['update_interval_minutes']} minutes")
    print(f"API Key: IQAir Active")
    print("Data Sources:")
    print("   • IQAir (Primary)")
    print("   • OpenAQ (Secondary)")
    print("   • EPA (Tertiary)")
    print("   • Real-time Weather Data")
    print("=" * 80)
    print("Monitoring will run continuously until stopped (Ctrl+C)")
    print("=" * 80)

    # Perform initial update immediately
    perform_update()

    # Start auto-update in a separate thread
    update_thread = threading.Thread(target=auto_update_worker, daemon=True)
    update_thread.start()

    # Keep main thread alive and responsive to Ctrl+C
    try:
        while monitoring_active:
            time.sleep(1)
    except KeyboardInterrupt:
        monitoring_active = False
        logger.info("Stopping monitoring system...")
        print("\n" + "=" * 80)
        print("MONITORING STOPPED")
        print("=" * 80)
        print(" Thank you for using New York Air Quality Monitoring!")
        print(f"Total updates performed: {run_count}")
        print(" Data saved in timestamped CSV files")
        print("=" * 80)


# ---------------------------
# MAIN EXECUTION
# ---------------------------
def main():
    """Main execution function"""
    logger.info("STARTING NEW YORK AIR QUALITY MONITORING SYSTEM")

    print("\n" + "=" * 80)
    print("🗽 NEW YORK AIR QUALITY MONITORING SYSTEM")
    print("=" * 80)
    print("System Configuration:")
    print(f"   • Location: {CONFIG['location']['name']}")
    print(f"   • Coordinates: {CONFIG['location']['lat']}, {CONFIG['location']['lon']}")
    print(f"   • Update Interval: {CONFIG['update_interval_minutes']} minutes")
    print("Integrated Data Sources:")
    print("   IQAir API (Active)")
    print("   OpenAQ Platform")
    print("   EPA AirNow")
    print("   Real-time Weather Data")
    print("=" * 80)

    # Test IQAir API connection
    print("Testing IQAir API connection...")
    try:
        test_data = get_iqair_data()
        if test_data:
            print(" IQAir API connected successfully!")
            print(f"   Found {len(test_data)} pollution measurements")
        else:
            print("IQAir connected but no data received")
    except Exception as e:
        print(f"IQAir connection failed: {e}")

    # Start continuous monitoring
    start_monitoring()


if __name__ == "__main__":
    # Install required packages if needed
    try:
        import requests
        import pandas as pd
        from bs4 import BeautifulSoup
    except ImportError as e:
        print(f"Package missing: {e}")
        print("Installing required packages...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "pandas", "beautifulsoup4"])
        import requests
        import pandas as pd
        from bs4 import BeautifulSoup

    main()
