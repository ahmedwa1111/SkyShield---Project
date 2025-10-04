import { LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip } from "recharts";

export default function AQChart({ data }) {
  if (!data) return null;

  return (
    <LineChart width={500} height={300} data={data}>
      <Line type="monotone" dataKey="value" stroke="#8884d8" />
      <CartesianGrid stroke="#ccc" />
      <XAxis dataKey="pollutant" />
      <YAxis />
      <Tooltip />
    </LineChart>
  );
}
