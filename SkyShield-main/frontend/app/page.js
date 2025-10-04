"use client";

import dynamic from "next/dynamic";
import { useState, useEffect } from "react";

import Hero from "../components/Hero";
import AQAlert from "../components/AQAlert";
import AQCard from "../components/AQCard";
import WeatherCard from "../components/WeatherCard";
import AQInfoPanel from "../components/AQInfoPanel";

import { MapPin, Activity, ShoppingCart, Grid } from "lucide-react";

// ✅ Dynamically import map components to disable SSR
const AQMap = dynamic(() => import("../components/AQMap"), { ssr: false });
const AQMapSection = dynamic(() => import("../components/AQMapSection"), { ssr: false });

export default function HomePage() {
  const [cityData, setCityData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      setIsClient(true);
    }
  }, []);

  const handleSearch = async (city) => {
    const data = await getAirQuality(city); // make sure getAirQuality is imported from lib/api
    setCityData(data);
  };

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <Hero />

      {/* Alert Section */}
      <AQAlert />

      {/* Dashboard Layout */}
      <div id="dashboard" className="grid grid-cols-1 md:grid-cols-6 gap-6 items-start">
        {/* Center Info Panel */}
        <div className="md:col-span-2">
          {selected ? (
            <AQInfoPanel location={selected} />
          ) : (
            <div className="aq-info-strong rounded-xl shadow-xl p-6 text-white">
              <div className="text-sm text-gray-300">
                Select a location on the map to view details
              </div>
            </div>
          )}
        </div>

        {/* Right Map Section */}
        <div className="md:col-span-3">
          {isClient && <AQMapSection onSelect={(loc) => setSelected(loc)} />}
        </div>
      </div>

      {/* Weather + AQ Section */}
      <section id="weather">
        {cityData ? (
          <div className="grid gap-6">
            {/* Air Quality Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {cityData.ground?.map((d, i) => (
                <AQCard
                  key={i}
                  pollutant={d.pollutant}
                  value={d.value}
                  units={d.units}
                  rating={d.rating}
                />
              ))}
            </div>

            {/* Weather Info */}
            {cityData.weather && <WeatherCard weather={cityData.weather} />}

            {/* Interactive Map */}
            {isClient && <AQMap city={cityData.city} />}
          </div>
        ) : (
          <p className="text-center text-gray-600">
            Search for a city to view real-time air quality and weather data.
          </p>
        )}
      </section>

      {/* About Section */}
      <section id="about" className="py-6 text-center text-sm text-gray-600">
        <p>
          SkyShield provides interactive air quality visualizations and weather
          info across North America.
        </p>
      </section>
    </div>
  );
}
