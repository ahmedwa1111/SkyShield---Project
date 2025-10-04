"use client";
import { useState } from "react";

export default function SearchBar({ onSearch }) {
  const [city, setCity] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (city) onSearch(city);
  };

  return (
    <form onSubmit={handleSubmit} className="flex justify-center space-x-2">
      <input
        type="text"
        value={city}
        onChange={(e) => setCity(e.target.value)}
        placeholder="Enter city name..."
        className="w-72 px-4 py-2 border rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
      />
      <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700">
        Search
      </button>
    </form>
  );
}
