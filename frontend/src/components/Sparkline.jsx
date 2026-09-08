import React from "react";

export default function Sparkline({ points = [], isUp, isDown, width = 90, height = 28 }) {
  if (!points || points.length < 2) {
    return <span className="text-gray-600 text-[10px]">—</span>;
  }

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min;

  const strokeColor = isUp
    ? "#f87171" // red for price increase (cost increased)
    : isDown
    ? "#34d399" // emerald for price decrease (discount/drop)
    : "#38bdf8"; // sky blue for stable

  const gradientId = `spark-${Math.random().toString(36).substr(2, 9)}`;

  // Calculate coordinates
  const coords = points.map((p, idx) => {
    const x = (idx / (points.length - 1)) * (width - 8) + 4;
    const y = range === 0 ? height / 2 : height - 4 - ((p - min) / range) * (height - 8);
    return { x, y, val: p };
  });

  const pathD = coords.reduce((acc, pt, idx) => {
    return idx === 0 ? `M ${pt.x} ${pt.y}` : `${acc} L ${pt.x} ${pt.y}`;
  }, "");

  const areaD = `${pathD} L ${coords[coords.length - 1].x} ${height} L ${coords[0].x} ${height} Z`;

  const lastPt = coords[coords.length - 1];

  return (
    <div className="relative group inline-flex items-center" title={`روند: ${points[0]?.toLocaleString("fa-IR")} ← ${points[points.length - 1]?.toLocaleString("fa-IR")} تومان`}>
      <svg width={width} height={height} className="overflow-visible">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={strokeColor} stopOpacity="0.25" />
            <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Shaded Area under line */}
        <path d={areaD} fill={`url(#${gradientId})`} />

        {/* The line itself */}
        <path
          d={pathD}
          fill="none"
          stroke={strokeColor}
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Pulse dot at the latest price */}
        <circle cx={lastPt.x} cy={lastPt.y} r="2.5" fill={strokeColor} />
      </svg>
    </div>
  );
}
