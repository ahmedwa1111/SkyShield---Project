# 🛡️ SkyShield – North America Air Quality & Weather Monitoring

Web link: https://sky-shield-puce.vercel.app/
SkyShield is a real-time **air quality and weather monitoring system** developed for the **NASA Space Apps Challenge**.  
It integrates **satellite data, ground sensors, and weather APIs** to provide users with accurate AQI forecasts, personalized health risk alerts, and interactive visualizations across major North American cities.

---

## 🌍 Features
- **Real-Time Air Quality Monitoring** – View AQI, PM2.5, NO₂, O₃, and CO₂ levels across cities.  
- **Weather Insights** – Temperature, humidity, wind, and cloud conditions.  
- **Interactive Map** – Explore live conditions by city.  
- **Health Alerts** – Color-coded warnings (Good, Moderate, Unhealthy, Hazardous).  
- **Forecasting** – AI-assisted AQI predictions for upcoming days.  
- **History** – Track past AQI and weather trends.  

---

## 🤖 Use of AI
AI tools were used in the **development process** to accelerate and refine the project:
- Generating boilerplate **FastAPI and Next.js code**.  
- Assisting with **data processing & debugging**.  
- Improving **UI/UX design** (dashboards, hero section text).  
- Structuring documentation and deployment guides.  

---

## ⚙️ Tech Stack
**Backend**  
- Python 3.11, FastAPI, Uvicorn  
- Requests, Pandas, NumPy  
- Logging & CSV storage  

**Frontend**  
- Next.js (React)  
- TailwindCSS (styling)  
- Leaflet.js (interactive maps)  
- Recharts (data visualization)  
- Axios (API calls)  

**Data Sources**  
- [IQAir API](https://www.iqair.com/) – AQI & pollutants  
- [OpenWeather API](https://openweathermap.org/api) – weather data
- (Tempo)API satellite https://ladsweb.modaps.eosdis.nasa.gov/search/
- Custom pollutant estimations (CO₂, PM2.5 → AQI conversion)  
- (Future) NASA TEMPO satellite data integration  

---

## 🚀 Deployment
Backend and frontend can be deployed separately.  

### Backend
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
uvicorn api_server:app --reload --port 5000


