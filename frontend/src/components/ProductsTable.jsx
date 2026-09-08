import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts } from "../api";

function formatPrice(v) {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("fa-IR") + " تومان";
}

function ChangeBadge({ percent }) {
  if (percent === null || percent === undefined) {
    return <span className="text-gray-500 text-xs">—</span>;
  }
  const up = percent > 0;
  const down = percent < 0;
  const color = up ? "text-red-400 bg-red-500/10" : down ? "text-emerald-400 bg-emerald-500/10" : "text-gray-400 bg-white/5";
  const arrow = up ? "▲" : down ? "▼" : "—";
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${color}`}>
      {arrow} {Math.abs(percent).toFixed(1)}%
    </span>
  );
}

function timeAgo(iso) {
  if (!iso) return "—";
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "همین الان";
  if (mins < 60) return `${mins} دقیقه پیش`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} ساعت پیش`;
  return `${Math.floor(hours / 24)} روز پیش`;
}

export default function ProductsTable() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    const timeout = setTimeout(() => {
      fetchProducts({ q: q || undefined, category: category || undefined })
        .then((data) => {
          if (!active) return;
          setItems(data.items);
          setTotal(data.total);
          setError(null);
        })
        .catch((err) => active && setError(err.message))
        .finally(() => active && setLoading(false));
    }, 250);
    return () => {
      active = false;
      clearTimeout(timeout);
    };
  }, [q, category]);

  return (
    <div>
      <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white">محصولات ({total})</h2>
          <p className="text-sm text-gray-400">قیمت‌ها به صورت خودکار هر چند ساعت به‌روزرسانی می‌شوند</p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="جستجوی محصول..."
            className="w-full rounded-lg border border-white/10 bg-bg-card px-3 py-2 text-sm text-white placeholder-gray-500 outline-none focus:border-sky-500 sm:w-64"
          />
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="rounded-lg border border-white/10 bg-bg-card px-3 py-2 text-sm text-white outline-none focus:border-sky-500"
          >
            <option value="">همه دسته‌ها</option>
            <option value="new">نو</option>
            <option value="stock">استوک</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-300">
          خطا در دریافت اطلاعات: {error}
        </div>
      )}

      {/* Desktop table */}
      <div className="hidden overflow-hidden rounded-xl border border-white/10 bg-bg-panel md:block">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-right text-gray-400">
              <th className="px-4 py-3 font-medium">نام محصول</th>
              <th className="px-4 py-3 font-medium">قیمت ترب</th>
              <th className="px-4 py-3 font-medium">قیمت دیجی‌کالا</th>
              <th className="px-4 py-3 font-medium">ارزان‌ترین فروشنده</th>
              <th className="px-4 py-3 font-medium">تغییر قیمت</th>
              <th className="px-4 py-3 font-medium">آخرین بررسی</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr
                key={p.id}
                className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors"
              >
                <td className="px-4 py-3">
                  <Link to={`/products/${p.id}`} className="font-medium text-white hover:text-sky-400">
                    {p.name}
                  </Link>
                  {p.warehouse_title && (
                    <div className="text-xs text-gray-500">کد انبار: {p.warehouse_title}</div>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-300">{formatPrice(p.torob_min_price)}</td>
                <td className="px-4 py-3 text-gray-300">
                  {p.digikala_available === false ? (
                    <span className="text-gray-500">ناموجود</span>
                  ) : (
                    formatPrice(p.digikala_price)
                  )}
                </td>
                <td className="px-4 py-3 text-gray-300">
                  {p.cheapest_store ? p.cheapest_store.replace("torob:", "") : "—"}
                </td>
                <td className="px-4 py-3">
                  <ChangeBadge percent={p.change_percent} />
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">{timeAgo(p.last_checked_at)}</td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-gray-500">
                  محصولی پیدا نشد
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile cards */}
      <div className="grid grid-cols-1 gap-3 md:hidden">
        {items.map((p) => (
          <Link
            to={`/products/${p.id}`}
            key={p.id}
            className="block rounded-xl border border-white/10 bg-bg-panel p-4 active:bg-white/5"
          >
            <div className="mb-2 flex items-start justify-between gap-2">
              <span className="font-medium text-white">{p.name}</span>
              <ChangeBadge percent={p.change_percent} />
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs text-gray-400">
              <div>
                ترب: <span className="text-gray-200">{formatPrice(p.torob_min_price)}</span>
              </div>
              <div>
                دیجی‌کالا: <span className="text-gray-200">{formatPrice(p.digikala_price)}</span>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-500">آخرین بررسی: {timeAgo(p.last_checked_at)}</div>
          </Link>
        ))}
        {!loading && items.length === 0 && (
          <div className="rounded-xl border border-white/10 bg-bg-panel p-8 text-center text-gray-500">
            محصولی پیدا نشد
          </div>
        )}
      </div>

      {loading && <div className="py-10 text-center text-sm text-gray-500">در حال بارگذاری...</div>}
    </div>
  );
}
