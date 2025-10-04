"""
SkyShield - North America Air Quality Monitoring
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
        datefmt='%Y-%m-%d %H:%M:%S'
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
    "update_interval_minutes": 5,  # Reduced for testing
    "data_sources": {
        "iqair": "https://api.airvisual.com/v2/",
        "open_aq": "https://api.openaq.org/v2/",
        "weather_gov": "https://api.weather.gov/"
    },
    "api_keys": {
        "iqair": "f60e848b-f405-4bfe-a096-c9935e595165"
    },
    "north_america_cities": [
        {"city": "New York", "state": "New York", "country": "USA"},
        {"city": "Los Angeles", "state": "California", "country": "USA"},
        {"city": "Chicago", "state": "Illinois", "country": "USA"},
        {"city": "Toronto", "state": "Ontario", "country": "Canada"},
        {"city": "Mexico City", "state": "Mexico City", "country": "Mexico"}
    ]
}

# ---------------------------
# HEALTH THRESHOLDS (Based on US EPA standards)
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

# Global variables for monitoring
current_data = []
monitoring_active = True
run_count = 0

# ---------------------------
# CORE DATA FUNCTIONS
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

        logger.info(f"Fetching data for {city}, {country}")
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
            weather = current.get('weather', {})

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

            # Process other pollutants if available
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
            "Toronto": 15, "Mexico City": 35
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
def collect_air_quality_data():
    """Collect air quality data from all sources"""
    logger.info("Starting data collection...")
    all_data = []

    # Get data for each city
    for city in CONFIG["north_america_cities"]:
        try:
            # Get IQAir data
            iqair_data = get_iqair_city_data(city)
            if iqair_data:
                all_data.extend(iqair_data)
                logger.info(f"Successfully collected IQAir data for {city['city']}")
            else:
                logger.warning(f"No IQAir data for {city['city']}")

            # Add CO2 estimation
            co2_data = get_co2_estimation(city)
            if co2_data:
                all_data.append(co2_data)

            time.sleep(1)  # Rate limiting

        except Exception as e:
            logger.error(f"Error processing city {city['city']}: {e}")
            continue

    logger.info(f"Collection complete. Total measurements: {len(all_data)}")
    return all_data

# ---------------------------
# DISPLAY FUNCTIONS
# ---------------------------
def display_results(air_quality_data, run_number):
    """Display the monitoring results"""
    global current_data
    current_data = air_quality_data

    print("\n" + "=" * 80)
    print(f"🛡️ SKYSHIELD - NORTH AMERICA AIR QUALITY")
    print(f"Update #{run_number} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    if not air_quality_data:
        print("❌ No data available. Please check:")
        print("   • Internet connection")
        print("   • API key validity")
        print("   • Firewall settings")
        return

    # Group data by city
    cities_data = {}
    for item in air_quality_data:
        city_key = f"{item['city']}, {item['country']}"
        if city_key not in cities_data:
            cities_data[city_key] = []
        cities_data[city_key].append(item)

    # Display data by city
    for city, measurements in cities_data.items():
        print(f"\n📍 {city}:")

        # Display CO2 first
        co2_measurements = [m for m in measurements if m['pollutant'] == 'CO2']
        for co2 in co2_measurements:
            print(f"   CO2: {co2['value']:.0f} ppm {co2['indicator']} ({co2['rating']})")
            print(f"        {co2['description']}")

        # Display other pollutants
        other_pollutants = [m for m in measurements if m['pollutant'] != 'CO2']
        for poll in other_pollutants:
            print(f"   {poll['pollutant']}: {poll['value']:.1f} {poll['units']} {poll['indicator']} ({poll['rating']})")

    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"   Cities monitored: {len(cities_data)}")
    print(f"   Total measurements: {len(air_quality_data)}")

    # Check for unhealthy conditions
    unhealthy = [item for item in air_quality_data if item['rating'] in ['UNHEALTHY', 'VERY UNHEALTHY', 'POOR']]
    if unhealthy:
        print(f"   ⚠️  Unhealthy conditions: {len(unhealthy)} measurements")
    else:
        print(f"   ✅ All readings within acceptable ranges")

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
        data = collect_air_quality_data()
        display_results(data, run_count)

        # Save data
        if data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sky_shield_data_{timestamp}.csv"
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False)
            print(f"💾 Data saved to: {filename}")

    except Exception as e:
        logger.error(f"Update error: {e}")
        print(f"❌ Update failed: {e}")

def start_monitoring():
    """Start the continuous monitoring"""
    global monitoring_active

    print("\n" + "=" * 80)
    print("🛡️ STARTING SKYSHIELD MONITORING SYSTEM")
    print("=" * 80)
    print("NASA Space Apps Challenge 2024 - Team BlueForce")
    print("Creator: Ahmed Wael")
    print("\nMonitoring Configuration:")
    print(f"   • Region: North America")
    print(f"   • Cities: {len(CONFIG['north_america_cities'])}")
    print(f"   • Pollutants: PM2.5, O3, NO2, CO2")
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
    print("North America Air Quality Monitoring System")
    print("=" * 80)

    # Test basic connectivity
    print("🔍 Testing system...")
    try:
        response = requests.get("http://api.airvisual.com/v2/nearest_city?key=demo", timeout=10)
        if response.status_code == 200:
            print("✅ Internet connection: OK")
        else:
            print("❌ Internet connection: Issues detected")
    except:
        print("❌ Internet connection: Failed")

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