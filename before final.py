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
    file_handler = logging.FileHandler('indonesia_air_quality.log', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Initialize logging
logger = setup_logging()

# ---------------------------
# CONFIGURATION FOR INDONESIA
# ---------------------------
CONFIG = {
    "location": {
        "name": "Jakarta, Indonesia",
        "lat": -6.2088,
        "lon": 106.8456,
        "city": "Jakarta"
    },
    "update_interval_minutes": 30,
    "data_sources": {
        "tempo_iku": "https://iku.tempo.co",
        "iqair": "https://api.airvisual.com/v2/",
        "open_aq": "https://api.openaq.org/v2/",
        "bmkg": "https://data.bmkg.go.id/",
        "klhk": "http://iku.menlhk.go.id/"
    },
    "api_keys": {
        "iqair": "f60e848b-f405-4bfe-a096-c9935e595165"
    }
}

# ---------------------------
# HEALTH THRESHOLDS (Based on Indonesian KLHK standards)
# ---------------------------
HEALTH_THRESHOLDS = {
    "PM2_5": {
        "GOOD": 15, "MODERATE": 35, "BAD": 55, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - healthy air quality",
        "MODERATE_DESC": "Moderate - acceptable air quality",
        "BAD_DESC": "Unhealthy - sensitive groups affected"
    },
    "PM10": {
        "GOOD": 50, "MODERATE": 100, "BAD": 250, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - healthy air quality",
        "MODERATE_DESC": "Moderate - acceptable air quality",
        "BAD_DESC": "Unhealthy - sensitive groups affected"
    },
    "NO2": {
        "GOOD": 80, "MODERATE": 150, "BAD": 400, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - low vehicle pollution",
        "MODERATE_DESC": "Moderate - medium vehicle pollution",
        "BAD_DESC": "Unhealthy - high vehicle pollution"
    },
    "O3": {
        "GOOD": 80, "MODERATE": 120, "BAD": 180, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - low ozone levels",
        "MODERATE_DESC": "Moderate - increased ozone",
        "BAD_DESC": "Unhealthy - high ozone levels"
    },
    "SO2": {
        "GOOD": 50, "MODERATE": 100, "BAD": 300, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - low industrial pollution",
        "MODERATE_DESC": "Moderate - medium industrial pollution",
        "BAD_DESC": "Unhealthy - high industrial pollution"
    },
    "CO": {
        "GOOD": 2, "MODERATE": 5, "BAD": 10, "UNITS": "mg/m³",
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
# INDONESIA DATA SOURCES
# ---------------------------
def get_tempo_iku_data():
    """Get air quality data from Tempo.co IKU"""
    try:
        # Try to access Tempo IKU API or scrape data
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Try direct API endpoint (if available)
        url = "https://iku.tempo.co/api/station"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return process_tempo_data(data)
        else:
            # Fallback to web scraping
            return scrape_tempo_website()

    except Exception as e:
        logger.error("Tempo IKU error: %s", e)
        return []


def scrape_tempo_website():
    """Scrape Tempo IKU website for air quality data"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(CONFIG["data_sources"]["tempo_iku"], headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        results = []

        # Look for air quality data elements
        aqi_elements = soup.find_all(class_=['aqi-value', 'pollutant-value', 'number'])

        for element in aqi_elements[:5]:
            text = element.get_text().strip()
            # Extract numeric values
            try:
                value = float(''.join(filter(str.isdigit, text.split('.')[0])))
                if 0 < value < 500:  # Reasonable AQI range
                    pollutant = "PM2_5"  # Default assumption for Tempo

                    rating, indicator, description = get_health_rating(pollutant, value)

                    results.append({
                        'pollutant': pollutant,
                        'value': value,
                        'units': HEALTH_THRESHOLDS[pollutant]["UNITS"],
                        'source': "Tempo.co IKU",
                        'rating': rating,
                        'indicator': indicator,
                        'description': description,
                        'type': 'GROUND'
                    })
            except ValueError:
                continue

        return results

    except Exception as e:
        logger.error("Tempo scraping error: %s", e)
        return []


def process_tempo_data(data):
    """Process Tempo IKU API data"""
    results = []

    try:
        # Process based on Tempo's API structure
        if isinstance(data, list):
            for station in data[:3]:
                if 'pollutants' in station:
                    for pollutant_data in station['pollutants']:
                        poll_name = pollutant_data.get('name', '').upper()
                        value = pollutant_data.get('value', 0)

                        # Map to our pollutant types
                        poll_map = {
                            'PM2.5': 'PM2_5', 'PM25': 'PM2_5',
                            'PM10': 'PM10',
                            'NO2': 'NO2', 'NITROGEN DIOXIDE': 'NO2',
                            'O3': 'O3', 'OZONE': 'O3',
                            'SO2': 'SO2', 'SULFUR DIOXIDE': 'SO2',
                            'CO': 'CO', 'CARBON MONOXIDE': 'CO'
                        }

                        if poll_name in poll_map:
                            mapped_poll = poll_map[poll_name]
                            rating, indicator, description = get_health_rating(mapped_poll, value)

                            results.append({
                                'pollutant': mapped_poll,
                                'value': value,
                                'units': HEALTH_THRESHOLDS[mapped_poll]["UNITS"],
                                'source': f"Tempo IKU: {station.get('name', 'Unknown')}",
                                'rating': rating,
                                'indicator': indicator,
                                'description': description,
                                'type': 'GROUND'
                            })

        return results

    except Exception as e:
        logger.error("Tempo data processing error: %s", e)
        return []


def get_iqair_data():
    """Get comprehensive data from IQAir/airvisual API"""
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
    """Convert AQI to PM2.5 concentration (μg/m³)"""
    # Based on US EPA conversion formula
    if aqi <= 50:
        return (aqi * 0.5)
    elif aqi <= 100:
        return (25 + (aqi - 50) * 0.5)
    elif aqi <= 150:
        return (50 + (aqi - 100) * 0.5)
    elif aqi <= 200:
        return (75 + (aqi - 150) * 0.5)
    elif aqi <= 300:
        return (100 + (aqi - 200) * 1.0)
    else:
        return (200 + (aqi - 300) * 1.0)


def get_openaq_data():
    """Get data from OpenAQ platform"""
    try:
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]

        # Get latest measurements
        url = f"https://api.openaq.org/v2/latest?coordinates={lat},{lon}&radius=50000&limit=10"

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
    """Process OpenAQ data"""
    results = []

    try:
        if 'results' in data:
            for station in data['results'][:5]:  # First 5 stations
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

                        # Convert units if necessary
                        if mapped_poll == 'CO' and unit == 'ppm':
                            value = value * 1.15  # Convert ppm to mg/m³
                            unit = 'mg/m³'

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


def get_weather_data():
    """Get weather data from BMKG or alternative"""
    try:
        # Using OpenMeteo as BMKG alternative
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,cloud_cover,visibility&temperature_unit=celsius&wind_speed_unit=ms"

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
                'visibility': current['visibility'] / 1000,
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


def get_health_advice(pollutant_type, rating):
    """Get health advice based on rating"""
    advice = {
        "GOOD": "No precautions needed",
        "MODERATE": "Generally acceptable for most people",
        "UNHEALTHY": "Sensitive groups should reduce outdoor activity",
        "VERY UNHEALTHY": "Everyone should reduce outdoor exertion"
    }
    return advice.get(rating, "Check local air quality advisories")


def calculate_aqi_from_weather(weather):
    """Estimate AQI from weather conditions"""
    score = 0

    # Low wind = poor dispersion
    if weather['wind_speed_10m'] < 2:
        score += 30
    elif weather['wind_speed_10m'] < 5:
        score += 15

    # High humidity can trap pollutants
    if weather['relative_humidity_2m'] > 80:
        score += 20

    # Low visibility indicates pollution
    if weather['visibility'] < 5000:
        score += 40
    elif weather['visibility'] < 10000:
        score += 20

    return min(100, score)


# ---------------------------
# DATA COLLECTION MASTER FUNCTION
# ---------------------------
def collect_all_air_quality_data():
    """Collect data from all available sources"""
    logger.info("Collecting Indonesia air quality data...")

    all_data = []

    # Try IQAir first (most reliable with API key)
    logger.info("Accessing IQAir data...")
    iqair_data = get_iqair_data()
    all_data.extend(iqair_data)

    # Try OpenAQ as secondary source
    logger.info("Accessing OpenAQ data...")
    openaq_data = get_openaq_data()
    all_data.extend(openaq_data)

    # Try Tempo.co IKU as tertiary source
    if len(all_data) < 2:  # If we don't have much data
        logger.info("Accessing Tempo.co IKU data...")
        tempo_data = get_tempo_iku_data()
        all_data.extend(tempo_data)

    logger.info("Total %s pollution measurements found", len(all_data))
    return all_data


# ---------------------------
# DISPLAY RESULTS IN ENGLISH
# ---------------------------
def display_results(air_quality_data, weather_data, run_number=0):
    """Display comprehensive results in English"""
    global current_data

    # Update current data
    current_data = air_quality_data

    print("\n" + "=" * 80)
    print(f"INDONESIA AIR QUALITY MONITORING - UPDATE #{run_number}")
    print("=" * 80)
    print(f"Location: {CONFIG['location']['name']}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Next update in: {CONFIG['update_interval_minutes']} minutes")
    print(f"Data Sources: IQAir, OpenAQ, Tempo.co IKU")

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
        print(f"Temperature: {weather_data['temperature']:.1f}°C")
        print(f"Humidity: {weather_data['humidity']}%")
        print(f"Wind: {weather_data['wind_speed']:.1f} m/s from {weather_data['wind_direction']}°")
        print(f"Pressure: {weather_data['pressure']:.1f} hPa")
        print(f"Clouds: {weather_data['clouds']}%")
        print(f"Visibility: {weather_data['visibility']:.1f} km")
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
            filename = f"indonesia_air_quality_{timestamp}.csv"
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
    print("   • Tempo.co IKU (Tertiary)")
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
        print(" Thank you for using Indonesia Air Quality Monitoring!")
        print(f"Total updates performed: {run_count}")
        print(" Data saved in timestamped CSV files")
        print("=" * 80)


# ---------------------------
# MAIN EXECUTION
# ---------------------------
def main():
    """Main execution function"""
    logger.info("STARTING INDONESIA AIR QUALITY MONITORING SYSTEM")

    print("\n" + "=" * 80)
    print("🇮🇩 INDONESIA AIR QUALITY MONITORING SYSTEM")
    print("=" * 80)
    print("System Configuration:")
    print(f"   • Location: {CONFIG['location']['name']}")
    print(f"   • Coordinates: {CONFIG['location']['lat']}, {CONFIG['location']['lon']}")
    print(f"   • Update Interval: {CONFIG['update_interval_minutes']} minutes")
    print("Integrated Data Sources:")
    print("   IQAir API (Active)")
    print("   OpenAQ Platform")
    print("   Tempo.co IKU")
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