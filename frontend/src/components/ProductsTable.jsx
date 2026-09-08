import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { fetchProducts } from "../api";

function formatPrice(v) {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("fa-IR") + " تومان";
}

function ChangeBadge({ percent, amount }) {
  if (percent === null || percent === undefined) {
    return <span className="text-gray-500 text-xs">بدون تغییر</span>;
  }
  if (Math.abs(percent) < 0.1) {
    return <span className="inline-flex rounded-full bg-white/5 px-2 py-1 text-xs text-gray-400">ثابت</span>;
  }
  const isUp = percent > 0;
  const color = isUp ? "text-red-400 bg-red-500/10 border-red-500/20" : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  const arrow = isUp ? "▲ +" : "▼ ";
  return (
    <div className="flex flex-col items-start gap-0.5">
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${color}`}>
        {arrow}{Math.abs(percent).toFixed(1)}%
      </span>
      {amount ? (
        <span className="text-[10px] text-gray-500">
          {Math.abs(amount).toLocaleString("fa-IR")} تومان
        </span>
      ) : null}
    </div>
  );
}

export default function ProductsTable() {
  const [data, setData] = useState({ items: [], total: 0, metadata: {} });
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("default");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchProducts({ q, category, status: statusFilter, sortBy })
      .then((res) => {
        if (!active) return;
        setData(res);
        setError(null);
      })
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, [q, category, statusFilter, sortBy]);

  const meta = data.metadata || {};

  return (
    <div className="space-y-6">
      {/* Top Header & Stat Cards */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">سامانه پایش قیمت محصولات</h2>
          <p className="text-sm text-gray-400 mt-1">
            مقایسه لحظه‌ای قیمت انبار با سایت‌های دیجی‌کالا و ترب
            {meta.last_updated_fa && (
              <span className="mr-2 inline-flex items-center gap-1 rounded-md bg-white/5 px-2 py-0.5 text-xs text-sky-400">
                🕒 آخرین بررسی: {meta.last_updated_fa}
              </span>
            )}
          </p>
        </div>

        {/* Download updated Excel button */}
        <div className="flex items-center gap-3">
          <a
            href="./data/گزارش_انبار_قیمت_به_روز.xlsx"
            download="گزارش_انبار_قیمت_به_روز.xlsx"
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600/20 border border-emerald-500/30 px-4 py-2.5 text-sm font-medium text-emerald-300 hover:bg-emerald-600/30 transition-all shadow-sm"
          >
            📥 دانلود اکسل آخرین قیمت‌ها
          </a>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div className="rounded-2xl border border-white/5 bg-bg-panel p-4">
          <div className="text-xs text-gray-400">کل محصولات</div>
          <div className="mt-2 text-2xl font-bold text-white">{meta.total_products || 100}</div>
          <div className="mt-1 text-[11px] text-gray-500">نو + استوک</div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-bg-panel p-4">
          <div className="text-xs text-sky-400">محصولات نو</div>
          <div className="mt-2 text-2xl font-bold text-sky-400">{meta.new_count || 32}</div>
          <div className="mt-1 text-[11px] text-gray-500">گارانتی‌دار</div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-bg-panel p-4">
          <div className="text-xs text-purple-400">محصولات استوک</div>
          <div className="mt-2 text-2xl font-bold text-purple-400">{meta.stock_count || 68}</div>
          <div className="mt-1 text-[11px] text-gray-500">کارکرده / اوپن باکس</div>
        </div>

        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-4">
          <div className="text-xs text-red-400">افزایش قیمت 🔺</div>
          <div className="mt-2 text-2xl font-bold text-red-400">{meta.increased_count || 0}</div>
          <div className="mt-1 text-[11px] text-red-400/60">گران‌تر از اکسل</div>
        </div>

        <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4">
          <div className="text-xs text-emerald-400">کاهش قیمت 🔻</div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">{meta.decreased_count || 0}</div>
          <div className="mt-1 text-[11px] text-emerald-400/60">ارزان‌تر از اکسل</div>
        </div>

        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-4">
          <div className="text-xs text-amber-400">ناموجود در بازار</div>
          <div className="mt-2 text-2xl font-bold text-amber-400">{meta.out_of_stock_count || 0}</div>
          <div className="mt-1 text-[11px] text-amber-400/60">فاقد موجودی آنلاین</div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rounded-2xl border border-white/5 bg-bg-panel p-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        {/* Category Tabs */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => { setCategory("all"); setStatusFilter("all"); }}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
              category === "all" && statusFilter === "all"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
            }`}
          >
            همه محصولات ({meta.total_products || 100})
          </button>
          <button
            onClick={() => setCategory("new")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
              category === "new"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
            }`}
          >
            محصولات نو ({meta.new_count || 32})
          </button>
          <button
            onClick={() => setCategory("stock")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
              category === "stock"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
            }`}
          >
            محصولات استوک ({meta.stock_count || 68})
          </button>
          <button
            onClick={() => setStatusFilter("changed")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
              statusFilter === "changed"
                ? "bg-amber-500 text-white shadow-md shadow-amber-500/20"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
            }`}
          >
            دارای تغییر قیمت ({(meta.increased_count || 0) + (meta.decreased_count || 0)})
          </button>
          <button
            onClick={() => setStatusFilter("out_of_stock")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
              statusFilter === "out_of_stock"
                ? "bg-gray-700 text-white shadow-md"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
            }`}
          >
            ناموجودها ({meta.out_of_stock_count || 0})
          </button>
        </div>

        {/* Search & Sort Controls */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="relative">
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="جستجوی نام یا کد انبار (مثلاً C80)..."
              className="w-full sm:w-64 rounded-xl border border-white/10 bg-bg px-3.5 py-2 text-xs text-white placeholder-gray-500 outline-none focus:border-sky-500 transition-colors"
            />
            {q && (
              <button
                onClick={() => setQ("")}
                className="absolute left-2.5 top-2 text-xs text-gray-500 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="rounded-xl border border-white/10 bg-bg px-3 py-2 text-xs text-white outline-none focus:border-sky-500 transition-colors"
          >
            <option value="default">مرتب‌سازی پیش‌فرض انبار</option>
            <option value="change_desc">بیشترین افزایش قیمت (🔺)</option>
            <option value="change_asc">بیشترین کاهش قیمت (🔻)</option>
            <option value="price_desc">گران‌ترین قیمت بازار</option>
            <option value="price_asc">ارزان‌ترین قیمت بازار</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          خطا در بارگذاری داده‌ها: {error}
        </div>
      )}

      {/* Desktop Table View */}
      <div className="hidden lg:block overflow-hidden rounded-2xl border border-white/10 bg-bg-panel shadow-xl">
        <table className="w-full text-right text-xs">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.02] text-gray-400 font-medium">
              <th className="px-4 py-3.5 w-14 text-center">ردیف</th>
              <th className="px-4 py-3.5">کد انبار</th>
              <th className="px-4 py-3.5 w-1/4">نام محصول</th>
              <th className="px-4 py-3.5 text-center">موجودی انبار</th>
              <th className="px-4 py-3.5 text-left">قیمت پایه اکسل</th>
              <th className="px-4 py-3.5 text-left">قیمت روز دیجی‌کالا</th>
              <th className="px-4 py-3.5 text-center">تغییر قیمت</th>
              <th className="px-4 py-3.5 text-left">قیمت ترب (کف)</th>
              <th className="px-4 py-3.5 text-center">لینک فروشگاه‌ها</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {data.items.map((p) => {
              const basePrice = p.initial_digikala_price || p.initial_torob_price;
              return (
                <tr key={p.id} className="hover:bg-white/[0.03] transition-colors group">
                  <td className="px-4 py-3.5 text-center text-gray-500 font-mono">
                    {p.row_index}
                  </td>
                  <td className="px-4 py-3.5 font-mono text-gray-300">
                    <span className="rounded bg-white/5 px-2 py-1 text-[11px] font-semibold text-sky-400">
                      {p.warehouse_title || "—"}
                    </span>
                  </td>
                  <td className="px-4 py-3.5">
                    <Link
                      to={`/products/${p.id}`}
                      className="font-medium text-white hover:text-sky-400 transition-colors line-clamp-2"
                      title={p.name}
                    >
                      {p.name}
                    </Link>
                    <div className="mt-1 flex items-center gap-2">
                      <span className={`text-[10px] rounded px-1.5 py-0.5 ${p.category === 'new' ? 'bg-sky-500/10 text-sky-400' : 'bg-purple-500/10 text-purple-400'}`}>
                        {p.category_fa}
                      </span>
                      {p.digikala_seller && (
                        <span className="text-[10px] text-gray-500">
                          فروشنده: {p.digikala_seller}
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3.5 text-center font-medium text-gray-300">
                    {p.quantity !== null && p.quantity !== undefined ? (
                      <span className="rounded-full bg-white/5 px-2.5 py-1 text-xs">
                        {p.quantity} عدد
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-left font-mono text-gray-400">
                    {formatPrice(basePrice)}
                  </td>
                  <td className="px-4 py-3.5 text-left font-mono">
                    {p.current_digikala_price ? (
                      <div>
                        <div className="font-semibold text-white">
                          {formatPrice(p.current_digikala_price)}
                        </div>
                        {p.digikala_available && (
                          <span className="inline-block rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] text-emerald-400">
                            موجود در دیجی‌کالا
                          </span>
                        )}
                      </div>
                    ) : p.digikala_url ? (
                      <span className="rounded bg-red-500/10 px-2 py-0.5 text-[11px] text-red-400">
                        ناموجود
                      </span>
                    ) : (
                      <span className="text-gray-600">بدون لینک</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <ChangeBadge percent={p.price_change_percent} amount={p.price_change_amount} />
                  </td>
                  <td className="px-4 py-3.5 text-left font-mono">
                    {p.current_torob_price ? (
                      <span className="text-sky-300 font-semibold">{formatPrice(p.current_torob_price)}</span>
                    ) : p.initial_torob_price ? (
                      <span className="text-gray-400">{formatPrice(p.initial_torob_price)} <span className="text-[10px] text-gray-500">(اکسل)</span></span>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 text-center">
                    <div className="flex items-center justify-center gap-1.5">
                      {p.digikala_url && (
                        <a
                          href={p.digikala_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-lg bg-red-500/10 hover:bg-red-500/25 border border-red-500/20 px-2 py-1 text-[11px] font-medium text-red-300 transition-colors"
                          title="مشاهده در دیجی‌کالا"
                        >
                          دیجی‌کالا ↗
                        </a>
                      )}
                      {p.torob_url && (
                        <a
                          href={p.torob_url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded-lg bg-sky-500/10 hover:bg-sky-500/25 border border-sky-500/20 px-2 py-1 text-[11px] font-medium text-sky-300 transition-colors"
                          title="مشاهده در ترب"
                        >
                          ترب ↗
                        </a>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
            {!loading && data.items.length === 0 && (
              <tr>
                <td colSpan={9} className="px-4 py-16 text-center text-gray-500">
                  هیچ محصولی با معیارهای جستجو یا فیلتر فعلی یافت نشد.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card List View */}
      <div className="grid grid-cols-1 gap-3 lg:hidden">
        {data.items.map((p) => {
          const basePrice = p.initial_digikala_price || p.initial_torob_price;
          return (
            <div
              key={p.id}
              className="rounded-2xl border border-white/10 bg-bg-panel p-4 space-y-3"
            >
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-mono text-sky-400">
                      {p.warehouse_title || `#${p.row_index}`}
                    </span>
                    <span className={`text-[10px] rounded px-1.5 py-0.5 ${p.category === 'new' ? 'bg-sky-500/10 text-sky-400' : 'bg-purple-500/10 text-purple-400'}`}>
                      {p.category_fa}
                    </span>
                    {p.quantity !== null && (
                      <span className="text-[10px] text-gray-500">موجودی: {p.quantity}</span>
                    )}
                  </div>
                  <Link
                    to={`/products/${p.id}`}
                    className="mt-1 block font-medium text-white hover:text-sky-400 line-clamp-2"
                  >
                    {p.name}
                  </Link>
                </div>
                <ChangeBadge percent={p.price_change_percent} amount={p.price_change_amount} />
              </div>

              <div className="grid grid-cols-2 gap-2 rounded-xl bg-bg p-3 text-xs">
                <div>
                  <span className="text-gray-500 block text-[10px]">قیمت پایه اکسل</span>
                  <span className="text-gray-300 font-mono">{formatPrice(basePrice)}</span>
                </div>
                <div>
                  <span className="text-gray-500 block text-[10px]">قیمت روز دیجی‌کالا</span>
                  {p.current_digikala_price ? (
                    <span className="text-emerald-400 font-mono font-semibold">
                      {formatPrice(p.current_digikala_price)}
                    </span>
                  ) : (
                    <span className="text-red-400 text-xs">ناموجود</span>
                  )}
                </div>
              </div>

              <div className="flex items-center justify-between pt-1">
                <Link
                  to={`/products/${p.id}`}
                  className="text-xs text-sky-400 hover:underline"
                >
                  مشاهده نمودار و جزئیات ←
                </Link>
                <div className="flex gap-1.5">
                  {p.digikala_url && (
                    <a
                      href={p.digikala_url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg bg-red-500/10 px-2.5 py-1 text-[11px] font-medium text-red-300"
                    >
                      دیجی‌کالا ↗
                    </a>
                  )}
                  {p.torob_url && (
                    <a
                      href={p.torob_url}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg bg-sky-500/10 px-2.5 py-1 text-[11px] font-medium text-sky-300"
                    >
                      ترب ↗
                    </a>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {!loading && data.items.length === 0 && (
          <div className="rounded-2xl border border-white/10 bg-bg-panel p-10 text-center text-gray-500">
            محصولی یافت نشد.
          </div>
        )}
      </div>

      {loading && (
        <div className="py-12 text-center text-sm text-gray-500">
          در حال بارگذاری اطلاعات محصولات...
        </div>
      )}
    </div>
  );
}
