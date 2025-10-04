"use client";
import { useEffect } from "react";

export default function LegendControl({ map }) {
  useEffect(() => {
    if (!map) return;

    import("leaflet").then(L => {
      const legend = L.control({ position: "bottomright" });
      legend.onAdd = () => {
        const div = L.DomUtil.create("div", "legend p-2 rounded shadow text-xs");
        div.style.background = "linear-gradient(180deg, rgba(0,0,0,0.55), rgba(0,0,0,0.35))";
        div.style.color = "#e6eef8";
        div.style.padding = "8px";
        div.style.borderRadius = "8px";
        div.innerHTML = `
          <div style=\"display:flex;flex-direction:column;gap:6px;\"><div style=\"display:flex;align-items:center;gap:8px\"><span style=\"background:green;width:22px;height:12px;display:inline-block;border-radius:4px\"></span><span>Good (0-50)</span></div><div style=\"display:flex;align-items:center;gap:8px\"><span style=\"background:yellow;width:22px;height:12px;display:inline-block;border-radius:4px\"></span><span>Moderate (51-100)</span></div><div style=\"display:flex;align-items:center;gap:8px\"><span style=\"background:orange;width:22px;height:12px;display:inline-block;border-radius:4px\"></span><span>Unhealthy for Sensitive (101-150)</span></div><div style=\"display:flex;align-items:center;gap:8px\"><span style=\"background:red;width:22px;height:12px;display:inline-block;border-radius:4px\"></span><span>Unhealthy (151-200)</span></div><div style=\"display:flex;align-items:center;gap:8px\"><span style=\"background:purple;width:22px;height:12px;display:inline-block;border-radius:4px\"></span><span>Very Unhealthy (201-300)</span></div><div style=\"display:flex;align-items:center;gap:8px\"><span style=\"background:maroon;width:22px;height:12px;display:inline-block;border-radius:4px\"></span><span>Hazardous (301+)</span></div></div>
        `;
        return div;
      };
      legend.addTo(map);
      return () => legend.remove();
    });
  }, [map]);
  return null;
}
