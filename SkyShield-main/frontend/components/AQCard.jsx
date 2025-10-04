export default function AQCard({ pollutant, value, units, rating }) {
  const color =
    rating === "GOOD" ? "bg-green-100 border-green-400" :
    rating === "MODERATE" ? "bg-yellow-100 border-yellow-400" :
    "bg-red-100 border-red-400";

  return (
    <div className={`p-4 border rounded-xl shadow ${color}`}>
      <h3 className="font-bold text-lg">{pollutant}</h3>
      <p className="text-2xl font-semibold">{value} {units}</p>
      <p className="text-sm mt-1">Condition: {rating}</p>
    </div>
  );
}
