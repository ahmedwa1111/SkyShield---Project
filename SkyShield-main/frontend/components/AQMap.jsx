"use client";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";

export default function AQMap({ city }) {
  if (!city || !city.lat || !city.lon) return null;

  return (
    <div className="h-[500px] w-full rounded-xl overflow-hidden shadow">
      <MapContainer center={[city.lat, city.lon]} zoom={10} style={{ height: "100%", width: "100%" }}>
        {/* Dark basemap: CartoDB Dark Matter */}
        <TileLayer
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> contributors'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
        />
        <Marker position={[city.lat, city.lon]}>
          <Popup>{city.name}</Popup>
        </Marker>
      </MapContainer>
    </div>
  );
}
