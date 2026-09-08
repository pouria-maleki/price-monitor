import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

function formatDate(iso) {
  return new Date(iso).toLocaleDateString("fa-IR", { month: "short", day: "numeric" });
}

export default function PriceChart({ history }) {
  const data = history
    .filter((h) => h.new_price !== null && h.new_price !== undefined)
    .map((h) => ({
      date: formatDate(h.created_at),
      timestamp: h.created_at,
      price: h.new_price,
    }));

  if (data.length === 0) {
    return (
      <div className="flex h-64 items-center justify-center rounded-xl border border-white/10 bg-bg-panel text-sm text-gray-500">
        هنوز تغییر قیمتی برای رسم نمودار ثبت نشده است
      </div>
    );
  }

  return (
    <div className="h-72 rounded-xl border border-white/10 bg-bg-panel p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" stroke="#6b7280" fontSize={12} />
          <YAxis
            stroke="#6b7280"
            fontSize={12}
            tickFormatter={(v) => `${(v / 1000).toLocaleString("fa-IR")}k`}
            width={55}
          />
          <Tooltip
            contentStyle={{ background: "#161f31", border: "1px solid #2a3548", borderRadius: 8 }}
            labelStyle={{ color: "#9ca3af" }}
            formatter={(value) => [`${value.toLocaleString("fa-IR")} تومان`, "قیمت"]}
          />
          <Line type="monotone" dataKey="price" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
