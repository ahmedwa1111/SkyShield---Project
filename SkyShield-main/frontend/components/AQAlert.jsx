"use client";
import { useEffect, useState } from "react";
import { fetchAlerts } from "../lib/api";

export default function AQAlert() {
  const [alert, setAlert] = useState(null);

  useEffect(() => {
    fetchAlerts().then(res => {
      setAlert(res.alert);
    });
    const id = setInterval(() => {
      fetchAlerts().then(res => setAlert(res.alert));
    }, 60000); // refresh every 1 min
    return () => clearInterval(id);
  }, []);

  if (!alert) return null;

  const colorMap = {
    GOOD: "bg-green-100 border-green-500 text-green-800",
    MODERATE: "bg-yellow-100 border-yellow-500 text-yellow-800",
    UNHEALTHY: "bg-red-100 border-red-500 text-red-800",
    VERY_UNHEALTHY: "bg-purple-100 border-purple-500 text-purple-800",
    HAZARDOUS: "bg-black border-black text-white"
  };

  return (
    <div className={`p-4 rounded-lg border-2 shadow-md mb-6 ${colorMap[alert.level] || "bg-gray-100"}`}>
      <div className="font-bold text-lg">⚠ Air Quality Alert</div>
      <div className="mt-1">{alert.message}</div>
    </div>
  );
}
