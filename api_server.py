from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import os

# Import from your SkyShield script
from skyshield import collect_all_data, get_weather_data, CONFIG

app = FastAPI()

# Configure CORS from environment (comma-separated list) or default to allow localhost and Vercel origin
allowed = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,https://*.vercel.app")
allow_list = [o.strip() for o in allowed.split(',') if o.strip()]

# CORS setup so frontend (Next.js) can call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Format function to unify JSON
# -------------------------
def format_locations(aq_data, weather_data):
    cities = CONFIG["north_america_cities"]
    locations = []

    for city in cities:
        city_name = city["city"]
        country = city["country"]

        # Get AQ and weather for this city
        city_aq = [d for d in aq_data if d["city"] == city_name and d["country"] == country]
        city_weather = weather_data.get(f"{city_name}_{country}")

        if not city_aq and not city_weather:
            continue

        # --- FIX: Compute AQI ---
        # Prefer provided AQI if exists, else derive from PM2.5, O3, NO2
        aqi_value = None
        for aq in city_aq:
            if "aqi" in aq and aq["aqi"]:
                aqi_value = aq["aqi"]
                break

        if not aqi_value:
            # Try deriving from PM2.5
            pm25 = next((aq["value"] for aq in city_aq if aq["pollutant"] == "PM2_5"), None)
            if pm25:
                # EPA breakpoint conversion (simplified)
                if pm25 <= 12: aqi_value = int((pm25 / 12) * 50)
                elif pm25 <= 35.4: aqi_value = int(50 + (pm25 - 12.1) * (100 - 51) / (35.4 - 12.1))
                elif pm25 <= 55.4: aqi_value = int(101 + (pm25 - 35.5) * (150 - 101) / (55.4 - 35.5))
                else: aqi_value = int(151 + (pm25 - 55.5) * (200 - 151) / (150.4 - 55.5))

            # If still missing, fallback to NO2
            if not aqi_value:
                no2 = next((aq["value"] for aq in city_aq if aq["pollutant"] == "NO2"), None)
                if no2: 
                    aqi_value = min(200, int(no2 / 200 * 150))

            # If still missing, fallback to O3
            if not aqi_value:
                o3 = next((aq["value"] for aq in city_aq if aq["pollutant"] == "O3"), None)
                if o3:
                    aqi_value = min(200, int(o3 / 100 * 150))

        location = {
            "name": f"{city_name}, {country}",
            "lat": city["lat"],
            "lon": city["lon"],
            "aqi": aqi_value if aqi_value else None,
            "condition": city_aq[0]["description"] if city_aq else "Unknown",
            "pollutants": [
                {
                    "name": aq["pollutant"],
                    "value": aq["value"],
                    "unit": aq["units"],
                    "rating": aq["rating"],
                }
                for aq in city_aq
            ],
            "weather": city_weather if city_weather else {},
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        locations.append(location)

    return locations



# -------------------------
# API Routes
# -------------------------

@app.get("/")
def root():
    return {"message": "SkyShield API running 🚀"}

@app.get("/airquality")
def get_air_quality():
    aq_data = collect_all_data()
    from skyshield import weather_data  # grab global weather_data
    locations = format_locations(aq_data, weather_data)
    return {"locations": locations}

@app.get("/alerts")
def get_alerts():
    aq_data = collect_all_data()
    from skyshield import weather_data
    locations = format_locations(aq_data, weather_data)

    alerts = []
    for loc in locations:
        aqi = loc.get("aqi") or 0
        if aqi >= 300:
            alerts.append({"city": loc["name"], "level": "HAZARDOUS", "message": "Avoid all outdoor activity"})
        elif aqi >= 200:
            alerts.append({"city": loc["name"], "level": "VERY_UNHEALTHY", "message": "Stay indoors"})
        elif aqi >= 150:
            alerts.append({"city": loc["name"], "level": "UNHEALTHY", "message": "Sensitive groups avoid outdoor"})
        elif aqi >= 100:
            alerts.append({"city": loc["name"], "level": "MODERATE", "message": "Limit prolonged exertion"})
        else:
            alerts.append({"city": loc["name"], "level": "GOOD", "message": "Good air quality"})

    return {"alerts": alerts, "locations": locations}

@app.get("/history")
def get_history():
    # For now return last collected data (SkyShield saves CSV)
    # Later you can load from saved CSV files if needed
    aq_data = collect_all_data()
    from skyshield import weather_data
    locations = format_locations(aq_data, weather_data)
    return {"history": locations}


# -------------------------
# Run server
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # When deploying on Render, do not use reload and set workers appropriately
    uvicorn.run("api_server:app", host="0.0.0.0", port=port, reload=False)
