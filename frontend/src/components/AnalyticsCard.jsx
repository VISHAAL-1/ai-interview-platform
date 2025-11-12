import React from "react";

export default function AnalyticsCard({ title, value }) {
  return (
    <div className="analytics-card">
      <div className="analytics-title">{title}</div>
      <div className="analytics-value">{value}</div>
    </div>
  );
}
