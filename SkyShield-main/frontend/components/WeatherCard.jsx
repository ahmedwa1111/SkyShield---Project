export default function WeatherCard({ weather }) {
  return (
    <div className="p-6 bg-white shadow rounded-xl">
      <h2 className="text-xl font-bold mb-2">🌤️ Weather Conditions</h2>
      <p>🌡️ Temp: {weather.temperature}°C</p>
      <p>💧 Humidity: {weather.humidity}%</p>
      <p>💨 Wind: {weather.wind_speed} m/s</p>
      <p>📊 Pressure: {weather.pressure} hPa</p>
      <p>☁️ Clouds: {weather.clouds}%</p>
      <p>👁️ Visibility: {weather.visibility} km</p>
    </div>
  );
}
