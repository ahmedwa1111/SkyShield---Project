"use client";
import { useState, useEffect } from "react";
import {
  Calendar,
  MapPin,
  Wind,
  Thermometer,
  Droplets,
  Gauge,
  Cloud,
  Activity,
  Info,
} from "lucide-react";
import { fetchForecast, fetchHistory } from "../lib/api";

// AQI color mapping
function getAqiColor(aqi) {
  if (aqi <= 50) return "bg-green-400 text-black"; // Good
  if (aqi <= 100) return "bg-yellow-400 text-black"; // Moderate
  if (aqi <= 150) return "bg-orange-400 text-white"; // Unhealthy (Sensitive)
  if (aqi <= 200) return "bg-red-500 text-white"; // Unhealthy
  if (aqi <= 300) return "bg-purple-600 text-white"; // Very Unhealthy
  return "bg-gray-700 text-white"; // Hazardous / Unknown
}

export default function AQInfoPanel({ location = {} }) {
  const [forecast, setForecast] = useState([]);
  const [history, setHistory] = useState([]);

  useEffect(() => {
    fetchForecast(72).then((d) => setForecast(d.forecast || []));
    fetchHistory(168).then((d) => setHistory(d.history || []));
  }, []);

  const aqiClass = getAqiColor(location?.aqi ?? 40);

  return (
    <aside className="w-full md:w-96 rounded-xl shadow-2xl text-white space-y-4 font-sans">
      {/* Header */}
      <div className="bg-zinc-900 rounded-xl p-5">
        <div className="text-xs uppercase tracking-widest text-gray-400 mb-3">
          Air Quality Information
        </div>
        <div className="flex items-center gap-2 mb-2">
          <MapPin className="w-4 h-4 text-gray-300" />
          <span className="text-2xl font-bold">{location?.name ?? "Unknown"}</span>
        </div>
        <div className="text-sm text-gray-400">
          {location?.lat}, {location?.lon}
        </div>
        <div className="flex items-center gap-1 mt-2 text-xs text-gray-400">
          <Calendar className="w-4 h-4" />
          {location?.timestamp ?? "No timestamp"}
        </div>
      </div>

      {/* AQI + Weather Snapshot */}
      <div className="bg-zinc-900 rounded-xl p-5 flex items-center justify-between">
        <div className={`px-5 py-4 rounded-xl font-bold text-center ${aqiClass}`}>
          <div className="text-2xl">{location?.aqi ?? "N/A"}</div>
          <div className="text-xs">AQI</div>
        </div>
        <div className="flex flex-col items-center">
          <Cloud className="w-10 h-10 text-gray-200" />
          <div className="text-lg font-semibold">
            {location?.weather?.temperature ?? "N/A"}°C
          </div>
          <div className="text-xs text-gray-400">{location?.condition ?? "Unknown"}</div>
        </div>
      </div>

      {/* Condition Details */}
      <div className="bg-zinc-900 rounded-xl p-5 space-y-3">
        <div className="text-sm font-semibold mb-1 flex items-center gap-2 text-gray-200">
          <Activity className="w-4 h-4" /> Condition
        </div>
        <div className="flex justify-between text-sm">
          <span className="flex items-center gap-2 text-gray-300">
            <Droplets className="w-4 h-4" /> Humidity
          </span>
          <span>{location?.weather?.humidity ?? "N/A"}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="flex items-center gap-2 text-gray-300">
            <Gauge className="w-4 h-4" /> Pressure
          </span>
          <span>{location?.weather?.pressure ?? "N/A"} mbar</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="flex items-center gap-2 text-gray-300">
            <Wind className="w-4 h-4" /> Wind
          </span>
          <span>{location?.weather?.wind_speed ?? "N/A"} m/s</span>
        </div>
      </div>

      {/* Pollutants */}
      <div className="bg-zinc-900 rounded-xl p-5">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2 text-gray-200">
          <Thermometer className="w-4 h-4" /> Pollutants
        </div>
        {Array.isArray(location?.pollutants) && location.pollutants.length ? (
          <div className="space-y-3">
            {location.pollutants.map((p, i) => (
              <div
                key={i}
                className="flex justify-between items-center text-sm border-b border-gray-800 pb-2"
              >
                <div>
                  <div className="font-medium text-gray-100">{p.name}</div>
                  <div className="text-xs text-gray-400">{p.rating}</div>
                </div>
                <div className="font-semibold">{p.value} {p.unit}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-sm text-gray-500">No pollutant data available</div>
        )}
      </div>

      {/* Daily Forecast */}
      <div className="bg-zinc-900 rounded-xl p-5">
        <div className="text-sm font-semibold mb-3 flex items-center gap-2 text-gray-200">
          <Calendar className="w-4 h-4" /> Daily Forecast
        </div>
        <div className="space-y-2">
          {forecast.length ? (
            forecast.slice(0, 5).map((f, i) => {
              const color = getAqiColor(f.aqi);
              return (
                <div
                  key={i}
                  className="flex justify-between items-center text-sm"
                >
                  <span className="text-gray-300">{f.date}</span>
                  <span
                    className={`px-3 py-1 rounded-md text-xs font-semibold ${color}`}
                  >
                    {f.aqi} AQI
                  </span>
                </div>
              );
            })
          ) : (
            <div className="text-xs text-gray-500">No forecast data</div>
          )}
        </div>
      </div>

      {/* Notes + Meta */}
      <div className="bg-zinc-900 rounded-xl p-5 text-xs text-gray-400 space-y-1">
        <div className="flex items-center gap-1">
          <Info className="w-4 h-4" /> Timestamp: {location?.timestamp ?? "N/A"}
        </div>
        {location?.weather?.note && (
          <div>Note: {location.weather.note}</div>
        )}
        {location?.weather?.source && (
          <div>Source: {location.weather.source}</div>
        )}
      </div>
    </aside>
  );
}
