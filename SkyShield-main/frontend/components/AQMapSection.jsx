"use client";
import { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import { fetchAirQuality } from "../lib/api";
import LegendControl from "./LegendControl";
import "leaflet/dist/leaflet.css";

const MapContainer = dynamic(() => import("react-leaflet").then(m => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then(m => m.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then(m => m.Marker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then(m => m.Popup), { ssr: false });

const getColor = (aqi) => {
  if (aqi <= 50) return "green";
  if (aqi <= 100) return "yellow";
  if (aqi <= 150) return "orange";
  if (aqi <= 200) return "red";
  if (aqi <= 300) return "purple";
  return "maroon";
};

export default function AQMapSection({ onSelect }) {
  const [locations, setLocations] = useState([]);
  const [map, setMap] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [miniCenter, setMiniCenter] = useState(null);
  const [miniZoom, setMiniZoom] = useState(3);
  const mainMapRef = useRef(null);
  const miniMapRef = useRef(null);
  const [L, setL] = useState(null);

  useEffect(() => {
    import("leaflet").then(leaflet => {
      setL(leaflet);
    });
  }, []);

  useEffect(() => {
    if (!map) return;
    const setCenter = () => {
      const center = map.getCenter();
      setMiniCenter([center.lat, center.lng]);
      setMiniZoom(Math.max(1, Math.min(7, map.getZoom() - 2)));
      if (miniMapRef.current && miniMapRef.current.setView) {
        miniMapRef.current.setView([center.lat, center.lng], Math.max(1, Math.min(7, map.getZoom() - 2)), { animate: false });
      }
    };
    setCenter();
    map.on("move", setCenter);
    map.on("zoomend", setCenter);
    return () => {
      map.off("move", setCenter);
      map.off("zoomend", setCenter);
    };
  }, [map]);

  useEffect(() => {
    fetchAirQuality()
      .then(data => {
        setLocations(data.locations || []);
      })
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-white">Loading map...</div>;
  if (!locations.length) return <div className="p-6 text-white">No data available.</div>;

  const center = [locations[0].lat, locations[0].lon];

  const handleSearch = () => {
    const qRaw = (search || "").trim();
    if (!qRaw) return;
    const q = qRaw.toLowerCase();
    const found = locations.find(l => (l.name || "").toLowerCase().includes(q));
    if (found && map) {
      map.flyTo([found.lat, found.lon], 8, { animate: true });
      onSelect && onSelect(found);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div className="w-screen h-screen relative rounded-lg overflow-hidden shadow-xl">
      <div className="absolute inset-0">
        {/* Search Bar (styled like screenshot) */}
        <div className="absolute top-4 right-4 z-30">
          <div className="bg-black/80 text-white rounded-full px-4 py-2 flex items-center gap-3 shadow-lg">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onKeyDown={handleKey}
              aria-label="Search"
              placeholder="Search City/Country"
              className="bg-transparent outline-none placeholder-gray-400 text-sm w-52"
            />
            <button
              onClick={handleSearch}
              className="bg-white/10 hover:bg-white/20 rounded-full p-2 transition"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-4.35-4.35" />
                <circle cx="11" cy="11" r="6" strokeWidth={2} />
              </svg>
            </button>
          </div>
        </div>

        {/* Main Map */}
        <MapContainer
          center={center}
          zoom={6}
          style={{ height: "100%", width: "100%" }}
          whenCreated={(m) => { setMap(m); mainMapRef.current = m; }}
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
          />
          {L && locations.map((loc, i) => {
            const iconHtml = `
              <div style="
                background:${getColor(loc.aqi)};
                color:white;
                font-size:14px;
                font-weight:700;
                text-align:center;
                border-radius:50%;
                width:40px;
                height:40px;
                line-height:40px;
                border:2px solid white;
                box-shadow:0 0 8px rgba(0,0,0,0.5);
              ">${loc.aqi}</div>`;
            const icon = L.divIcon({ html: iconHtml, className: "" });
            return (
              <Marker key={i} position={[loc.lat, loc.lon]} icon={icon} eventHandlers={{ click: () => onSelect && onSelect(loc) }}>
                <Popup>
                  <b>{loc.name}</b><br />
                  AQI: {loc.aqi} ({loc.condition})
                </Popup>
              </Marker>
            );
          })}
          {map && <LegendControl map={map} />}
        </MapContainer>

        {/* Mini Map (bottom-right) */}
        <div className="absolute bottom-4 right-4 w-40 h-28 rounded-md overflow-hidden shadow-lg border border-gray-700 z-40">
          {miniCenter ? (
            <MapContainer
              center={miniCenter}
              zoom={miniZoom}
              style={{ height: "100%", width: "100%" }}
              whenCreated={(m) => { miniMapRef.current = m; }}
            >
              <TileLayer attribution='&copy; CARTO' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png" />
            </MapContainer>
          ) : (
            <div className="w-full h-full bg-black/50 flex items-center justify-center text-xs text-gray-300">
              Mini Map
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
