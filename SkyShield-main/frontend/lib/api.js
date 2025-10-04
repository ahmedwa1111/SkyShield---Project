import axios from "axios";
const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:5000";

export async function fetchAirQuality() {
  const res = await axios.get(`${API_BASE}/airquality`);
  return res.data;
}
export async function fetchForecast(hours=72) {
  const res = await axios.get(`${API_BASE}/forecast?hours=${hours}`);
  return res.data;
}
export async function fetchHistory(n=168) {
  const res = await axios.get(`${API_BASE}/history?n=${n}`);
  return res.data;
}
export async function fetchAlerts() {
  const res = await axios.get(`${API_BASE}/alerts`);
  return res.data;
}
