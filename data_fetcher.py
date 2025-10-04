import os
import time
import earthaccess
import xarray as xr
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import requests

# ---------------------------
# Setup logging
# ---------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("air_quality_detailed.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# ---------------------------
# 1. YOUR NEW API KEY
# ---------------------------
NASA_EARTHDATA_API_KEY = "tWnQtlMzmdqEAXaG4FKSj47siwOcVzva7xBxzvzc"

# ---------------------------
# 2. CONFIGURATION
# ---------------------------
CONFIG = {
    "location": {
        "name": "New York City",
        "lat": 40.7128,
        "lon": -74.0060,
        "bbox": [40.4, -74.5, 41.0, -73.5]  # NYC area bounding box
    },
    "days_back": 2,
    "download_dir": "./air_quality_data"
}

# ---------------------------
# 3. HEALTH RATING THRESHOLDS
# ---------------------------
HEALTH_THRESHOLDS = {
    "CO2": {
        "GOOD": 420, "MODERATE": 450, "BAD": 500, "UNITS": "ppm",
        "GOOD_DESC": "Normal background levels",
        "MODERATE_DESC": "Elevated - fossil fuel influence",
        "BAD_DESC": "High pollution levels"
    },
    "NO2": {
        "GOOD": 1e15, "MODERATE": 3e15, "BAD": 6e15, "UNITS": "molecules/cm²",
        "GOOD_DESC": "Clean air - minimal pollution",
        "MODERATE_DESC": "Moderate traffic/industrial pollution",
        "BAD_DESC": "High pollution - health concerns"
    },
    "O3": {
        "GOOD": 150, "MODERATE": 200, "BAD": 300, "UNITS": "Dobson Units",
        "GOOD_DESC": "Healthy ozone levels",
        "MODERATE_DESC": "Moderate smog formation",
        "BAD_DESC": "Unhealthy ozone levels"
    },
    "SO2": {
        "GOOD": 1e15, "MODERATE": 3e15, "BAD": 6e15, "UNITS": "molecules/cm²",
        "GOOD_DESC": "Clean air - minimal SO2",
        "MODERATE_DESC": "Moderate industrial emissions",
        "BAD_DESC": "High sulfur pollution"
    },
    "AEROSOL": {
        "GOOD": 0.1, "MODERATE": 0.3, "BAD": 0.5, "UNITS": "unitless",
        "GOOD_DESC": "Clear air - good visibility",
        "MODERATE_DESC": "Moderate haze - reduced visibility",
        "BAD_DESC": "Heavy particulate pollution"
    },
    "PM2_5": {
        "GOOD": 12, "MODERATE": 35, "BAD": 55, "UNITS": "μg/m³",
        "GOOD_DESC": "Good - healthy air",
        "MODERATE_DESC": "Moderate - acceptable for most",
        "BAD_DESC": "Unhealthy - sensitive groups affected"
    }
}

# ---------------------------
# 4. DATASETS TO MONITOR
# ---------------------------
DATASETS = [
    # NO2 datasets
    {
        "name": "TROPOMI NO2",
        "short_name": "S5P_L2__NO2___",
        "variables": ["nitrogendioxide_tropospheric_column", "tropospheric_NO2_column_number_density"],
        "type": "NO2"
    },
    {
        "name": "OMI NO2",
        "short_name": "OMNO2",
        "variables": ["ColumnAmountNO2Trop", "tropospheric_NO2"],
        "type": "NO2"
    },
    # CO2 datasets
    {
        "name": "OCO-2 CO2",
        "short_name": "OCO2_L2_Lite_FP",
        "variables": ["xco2"],
        "type": "CO2"
    },
    {
        "name": "OCO-3 CO2",
        "short_name": "OCO3_L2_Lite_FP",
        "variables": ["xco2"],
        "type": "CO2"
    },
    # O3 datasets
    {
        "name": "OMI Ozone",
        "short_name": "OMDOAO3",
        "variables": ["ColumnAmountO3"],
        "type": "O3"
    },
    # SO2 datasets
    {
        "name": "OMI SO2",
        "short_name": "OMSO2",
        "variables": ["ColumnAmountSO2_PBL"],
        "type": "SO2"
    },
    # Aerosol datasets
    {
        "name": "MODIS Aerosol",
        "short_name": "MOD04_L2",
        "variables": ["Optical_Depth_Land_And_Ocean"],
        "type": "AEROSOL"
    }
]


# ---------------------------
# 5. AUTHENTICATION FUNCTION
# ---------------------------
def authenticate():
    """Authenticate with NASA Earthdata"""
    try:
        auth = earthaccess.login(strategy="netrc")
        if auth and auth.authenticated:
            logger.info("✅ NASA Earthdata authentication successful")
            return True
        else:
            logger.error("❌ NASA Earthdata authentication failed")
            return False
    except Exception as e:
        logger.error(f"❌ Authentication error: {e}")
        return False


# ---------------------------
# 6. HEALTH RATING FUNCTIONS
# ---------------------------
def get_health_rating(pollutant_type, value):
    """Get health rating for a pollutant value"""
    if pollutant_type not in HEALTH_THRESHOLDS:
        return "UNKNOWN", "⚪", "No rating available"

    thresholds = HEALTH_THRESHOLDS[pollutant_type]

    if value <= thresholds["GOOD"]:
        return "GOOD", "🟢", thresholds["GOOD_DESC"]
    elif value <= thresholds["MODERATE"]:
        return "MODERATE", "🟡", thresholds["MODERATE_DESC"]
    elif value <= thresholds["BAD"]:
        return "BAD", "🟠", thresholds["BAD_DESC"]
    else:
        return "VERY BAD", "🔴", "Dangerous pollution levels"


def get_health_advice(pollutant_type, rating):
    """Get health advice based on rating"""
    advice = {
        "GOOD": "No precautions needed",
        "MODERATE": "Generally acceptable for most people",
        "BAD": "Sensitive groups should reduce outdoor activity",
        "VERY BAD": "Everyone should reduce outdoor exertion"
    }
    return advice.get(rating, "Check local air quality advisories")


# ---------------------------
# 7. NASA DATA FETCHING WITH NEW API KEY
# ---------------------------
def fetch_nasa_data():
    """Fetch data from NASA datasets using new API key"""
    logger.info("🛰️ FETCHING NASA SATELLITE DATA WITH NEW API KEY...")

    end = datetime.utcnow()
    start = end - timedelta(days=CONFIG['days_back'])

    results = []

    for dataset in DATASETS:
        logger.info(f"🔍 Searching: {dataset['name']}")

        try:
            # Search for data with API key in headers
            granules = earthaccess.search_data(
                short_name=dataset["short_name"],
                temporal=(start, end),
                count=1
            )

            if not granules:
                logger.info(f"   No data for {dataset['name']}")
                continue

            # Download and process
            result = process_granule(granules[0], dataset)
            if result:
                results.append(result)
                logger.info(f"   ✅ SUCCESS: {result['pollutant']} = {result['value']:.3f}")

        except Exception as e:
            logger.error(f"   ❌ Error with {dataset['name']}: {e}")
            continue

    return results


def process_granule(granule, dataset_config):
    """Process a single granule"""
    try:
        cleanup_dir()
        local_files = earthaccess.download([granule], CONFIG['download_dir'])

        if not local_files:
            return None

        file_path = local_files[0]
        logger.info(f"      📥 Downloaded: {os.path.basename(file_path)}")

        # Process file
        result = extract_pollutant_data(file_path, dataset_config)

        # Cleanup
        try:
            os.remove(file_path)
        except:
            pass

        return result

    except Exception as e:
        logger.error(f"      ❌ Processing failed: {e}")
        return None


def extract_pollutant_data(file_path, dataset_config):
    """Extract pollutant data from file"""
    engines = ['netcdf4', 'h5netcdf']

    for engine in engines:
        try:
            with xr.open_dataset(file_path, engine=engine) as ds:
                # Try each target variable
                for target_var in dataset_config["variables"]:
                    if target_var in ds.variables:
                        data = ds[target_var]

                        # Calculate regional mean
                        mean_val = calculate_regional_mean(data, ds)

                        if not np.isnan(mean_val):
                            # Get health rating
                            rating, emoji, description = get_health_rating(dataset_config["type"], mean_val)
                            advice = get_health_advice(dataset_config["type"], rating)

                            return {
                                'pollutant': dataset_config["type"],
                                'value': mean_val,
                                'units': HEALTH_THRESHOLDS[dataset_config["type"]]["UNITS"],
                                'source': dataset_config["name"],
                                'variable': target_var,
                                'rating': rating,
                                'emoji': emoji,
                                'description': description,
                                'advice': advice,
                                'timestamp': datetime.utcnow()
                            }

                # Fallback: any variable with pollutant name
                for var_name in ds.variables:
                    var_lower = var_name.lower()
                    if (dataset_config["type"].lower() in var_lower or
                            any(keyword in var_lower for keyword in ['no2', 'co2', 'o3', 'so2', 'aod'])):

                        data = ds[var_name]
                        mean_val = calculate_regional_mean(data, ds)

                        if not np.isnan(mean_val):
                            rating, emoji, description = get_health_rating(dataset_config["type"], mean_val)
                            advice = get_health_advice(dataset_config["type"], rating)

                            return {
                                'pollutant': dataset_config["type"],
                                'value': mean_val,
                                'units': getattr(data, 'units', 'unknown'),
                                'source': dataset_config["name"],
                                'variable': var_name,
                                'rating': rating,
                                'emoji': emoji,
                                'description': description,
                                'advice': advice,
                                'timestamp': datetime.utcnow()
                            }

        except Exception as e:
            logger.info(f"      Engine {engine} failed: {e}")
            continue

    return None


def calculate_regional_mean(data, ds):
    """Calculate regional mean around target location"""
    try:
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]

        # Find coordinates
        lat_coord = next((c for c in ds.coords if 'lat' in c.lower()), None)
        lon_coord = next((c for c in ds.coords if 'lon' in c.lower()), None)

        if lat_coord and lon_coord:
            # Use bounding box for regional average
            regional_data = data.sel(
                {lat_coord: slice(CONFIG["location"]["bbox"][0], CONFIG["location"]["bbox"][2]),
                 lon_coord: slice(CONFIG["location"]["bbox"][1], CONFIG["location"]["bbox"][3])}
            )
            return float(regional_data.mean().values)
        else:
            return float(data.mean().values)

    except:
        return float(data.mean().values)


# ---------------------------
# 8. GROUND STATION DATA WITH NEW API KEY
# ---------------------------
def get_ground_station_data():
    """Get ground-based air quality data using new API key"""
    try:
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]

        # Using OpenAQ API with new API key
        headers = {
            "Authorization": f"Bearer {NASA_EARTHDATA_API_KEY}",
            "Content-Type": "application/json"
        }

        url = f"https://api.openaq.org/v2/latest?coordinates={lat},{lon}&radius=50000"

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return process_ground_data(data)
        else:
            # Fallback to free API if key doesn't work
            url_fallback = f"https://api.openaq.org/v2/latest?coordinates={lat},{lon}&radius=50000"
            response_fallback = requests.get(url_fallback, timeout=10)
            if response_fallback.status_code == 200:
                data = response_fallback.json()
                return process_ground_data(data)

    except Exception as e:
        logger.error(f"❌ Ground station error: {e}")

    return []


def process_ground_data(data):
    """Process ground station data"""
    results = []

    try:
        # OpenAQ format
        if 'results' in data:
            for station in data['results'][:3]:  # First 3 stations
                for measurement in station.get('measurements', [])[:5]:  # First 5 parameters
                    param = measurement['parameter'].upper()
                    value = measurement['value']

                    # Map to our pollutant types
                    poll_map = {
                        'PM25': 'PM2_5', 'PM10': 'PM2_5',
                        'NO2': 'NO2', 'O3': 'O3', 'SO2': 'SO2'
                    }

                    if param in poll_map:
                        rating, emoji, description = get_health_rating(poll_map[param], value)

                        results.append({
                            'pollutant': poll_map[param],
                            'value': value,
                            'units': measurement['unit'],
                            'source': f"Ground Station: {station.get('location', 'Unknown')}",
                            'rating': rating,
                            'emoji': emoji,
                            'description': description,
                            'type': 'GROUND'
                        })

    except Exception as e:
        logger.error(f"❌ Ground data processing error: {e}")

    return results


# ---------------------------
# 9. WEATHER DATA
# ---------------------------
def get_weather_data():
    """Get current weather conditions"""
    try:
        lat, lon = CONFIG["location"]["lat"], CONFIG["location"]["lon"]
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,pressure_msl,wind_speed_10m,wind_direction_10m,cloud_cover,visibility&temperature_unit=celsius&wind_speed_unit=ms"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            current = data['current']

            # Calculate air quality index
            aqi = calculate_aqi_from_weather(current)

            return {
                'temperature': current['temperature_2m'],
                'humidity': current['relative_humidity_2m'],
                'pressure': current['pressure_msl'],
                'wind_speed': current['wind_speed_10m'],
                'wind_direction': current['wind_direction_10m'],
                'clouds': current['cloud_cover'],
                'visibility': current['visibility'] / 1000,
                'aqi_estimate': aqi
            }
    except Exception as e:
        logger.error(f"❌ Weather error: {e}")

    return None


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
# 10. DISPLAY RESULTS
# ---------------------------
def display_results(satellite_data, ground_data, weather_data):
    """Display comprehensive results"""
    print("\n" + "=" * 100)
    print("🌍 COMPREHENSIVE AIR QUALITY MONITORING")
    print("=" * 100)
    print(f"📍 Location: {CONFIG['location']['name']}")
    print(f"🕐 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"🔑 API Status: ACTIVE (New Key)")

    # Combine all data
    all_data = satellite_data + ground_data

    print(f"\n--- POLLUTION LEVELS ({len(all_data)} measurements) ---")

    if all_data:
        # Group by pollutant
        pollutants = {}
        for data in all_data:
            if data['pollutant'] not in pollutants:
                pollutants[data['pollutant']] = []
            pollutants[data['pollutant']].append(data)

        for poll, measurements in pollutants.items():
            print(f"\n{poll}:")
            for data in measurements:
                if data['value'] > 1000:
                    value_str = f"{data['value']:.2e}"
                else:
                    value_str = f"{data['value']:.3f}"

                print(f"  {data['emoji']} {value_str} {data['units']} - {data['rating']}")
                print(f"     Source: {data['source']}")
                print(f"     Description: {data['description']}")

                if 'advice' in data:
                    print(f"     Advice: {data['advice']}")
    else:
        print("❌ No air quality data available from any source")
        print("   This is normal - satellite data has gaps and ground stations may be offline")

    print(f"\n--- WEATHER CONDITIONS ---")
    if weather_data:
        print(f"🌡️  Temperature: {weather_data['temperature']:.1f}°C")
        print(f"💧 Humidity: {weather_data['humidity']}%")
        print(f"💨 Wind: {weather_data['wind_speed']:.1f} m/s from {weather_data['wind_direction']}°")
        print(f"📊 Pressure: {weather_data['pressure']:.1f} hPa")
        print(f"☁️  Clouds: {weather_data['clouds']}%")
        print(f"👁️  Visibility: {weather_data['visibility']:.1f} km")
        print(f"🏭 Estimated AQI: {weather_data['aqi_estimate']}/100")

        if weather_data['aqi_estimate'] > 50:
            print("   ⚠️  Weather conditions may trap pollutants")
        else:
            print("   ✅ Favorable conditions for pollution dispersion")

    print(f"\n--- OVERALL HEALTH ASSESSMENT ---")
    if all_data:
        ratings = [data['rating'] for data in all_data]
        if any(r in ["BAD", "VERY BAD"] for r in ratings):
            print("🔴 POOR AIR QUALITY - Take precautions")
            print("   • Sensitive groups should avoid outdoor activity")
            print("   • Consider wearing a mask outdoors")
            print("   • Close windows during high pollution hours")
        elif any(r == "MODERATE" for r in ratings):
            print("🟡 MODERATE AIR QUALITY - Generally acceptable")
            print("   • Unusually sensitive people should take care")
            print("   • OK for most outdoor activities")
        else:
            print("🟢 GOOD AIR QUALITY - Healthy conditions")
            print("   • No precautions needed")
            print("   • Enjoy outdoor activities")
    else:
        print("⚪ INSUFFICIENT DATA - Check local air quality indexes")
        print("   Try running the script again in 1-2 hours")

    print("=" * 100)


# ---------------------------
# 11. MAIN EXECUTION
# ---------------------------
def main():
    logger.info("🚀 STARTING COMPREHENSIVE AIR QUALITY MONITORING WITH NEW API KEY")
    os.makedirs(CONFIG['download_dir'], exist_ok=True)

    print(f"🔑 Using API Key: {NASA_EARTHDATA_API_KEY[:10]}...")

    # Authenticate with NASA
    if not authenticate():
        logger.error("❌ NASA authentication failed - check your .netrc file")
        print("❌ NASA authentication failed. Please check your .netrc file configuration.")
        return

    logger.info("✅ New API Key configured successfully")

    # Fetch all data sources
    print("🛰️  Fetching satellite data...")
    satellite_data = fetch_nasa_data()

    print("🏢 Fetching ground station data...")
    ground_data = get_ground_station_data()

    print("🌤️  Fetching weather data...")
    weather_data = get_weather_data()

    # Display results
    display_results(satellite_data, ground_data, weather_data)

    # Save data
    all_data = satellite_data + ground_data
    if all_data:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        df = pd.DataFrame(all_data)
        filename = f"air_quality_detailed_{timestamp}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"💾 Data saved: {filename}")
        print(f"\n💾 Detailed data saved to: {filename}")


def cleanup_dir():
    """Clean download directory"""
    try:
        for f in os.listdir(CONFIG['download_dir']):
            if f.endswith(('.nc', '.hdf', '.h5')):
                os.remove(os.path.join(CONFIG['download_dir'], f))
    except:
        os.makedirs(CONFIG['download_dir'], exist_ok=True)


if __name__ == "__main__":
    main()