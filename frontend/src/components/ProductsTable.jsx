import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { fetchProducts } from "../api";
import Sparkline from "./Sparkline";

function formatPrice(v) {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("fa-IR") + " تومان";
}

function formatBillions(num) {
  if (!num) return "۰";
  const b = num / 1000000000;
  if (b >= 1) {
    return `${b.toFixed(2)} میلیارد تومان`;
  }
  const m = num / 1000000;
  return `${m.toFixed(1)} میلیون تومان`;
}

function ChangeBadge({ percent, amount }) {
  if (percent === null || percent === undefined) {
    return <span className="text-gray-500 text-xs">بدون تغییر</span>;
  }
  if (Math.abs(percent) < 0.1) {
    return <span className="inline-flex rounded-full bg-white/5 px-2 py-1 text-xs text-gray-400">ثابت</span>;
  }
  const isUp = percent > 0;
  const color = isUp
    ? "text-red-400 bg-red-500/10 border-red-500/20"
    : "text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
  const arrow = isUp ? "▲ +" : "▼ ";
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${color}`}>
        {arrow}{Math.abs(percent).toFixed(1)}%
      </span>
      {amount ? (
        <span className="text-[10px] text-gray-500 font-mono">
          {Math.abs(amount).toLocaleString("fa-IR")} ت
        </span>
      ) : null}
    </div>
  );
}

function QuantityBadge({ qty }) {
  if (qty === null || qty === undefined) {
    return <span className="text-gray-600 font-mono text-xs">—</span>;
  }
  if (qty >= 7) {
    return (
      <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-500/15 border border-emerald-500/25 px-2.5 py-1 text-xs font-semibold text-emerald-300">
        {qty} عدد
      </span>
    );
  }
  if (qty >= 3) {
    return (
      <span className="inline-flex items-center gap-1 rounded-lg bg-sky-500/15 border border-sky-500/25 px-2.5 py-1 text-xs font-semibold text-sky-300">
        {qty} عدد
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-lg bg-amber-500/15 border border-amber-500/25 px-2.5 py-1 text-xs font-semibold text-amber-300">
      {qty} عدد (محدود)
    </span>
  );
}

export default function ProductsTable() {
  const [data, setData] = useState({ items: [], total: 0, metadata: {} });
  const [q, setQ] = useState("");
  const [category, setCategory] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [sortBy, setSortBy] = useState("quantity_desc");
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
  const profitLoss = meta.total_inventory_profit_loss || 0;
  const isProfit = profitLoss > 0;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">سیستم جامع مانیتورینگ قیمت انبار</h2>
          <p className="text-sm text-gray-400 mt-1">
            مقایسه لحظه‌ای قیمت انبار با دیجی‌کالا و ترب همراه با ارزیابی ارزش موجودی
            {meta.last_updated_fa && (
              <span className="mr-2 inline-flex items-center gap-1 rounded-md bg-white/5 px-2.5 py-0.5 text-xs text-sky-400 font-mono">
                🕒 آخرین پایش: {meta.last_updated_fa}
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
            📥 دانلود اکسل کامل به‌روزرسانی‌شده
          </a>
        </div>
      </div>

      {/* Financial & Inventory Valuation Cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Market Value */}
        <div className="rounded-2xl border border-sky-500/20 bg-gradient-to-br from-sky-500/10 to-indigo-500/5 p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-sky-300">ارزش کل موجودی انبار (قیمت روز)</span>
            <span className="rounded-lg bg-sky-500/20 px-2 py-0.5 text-[10px] text-sky-300">ارزش بازار</span>
          </div>
          <div className="mt-2 text-xl font-bold text-white font-mono">
            {formatPrice(meta.total_inventory_current_value)}
          </div>
          <div className="mt-1 text-[11px] text-gray-400">
            معادل تقریباً {formatBillions(meta.total_inventory_current_value)}
          </div>
        </div>

        {/* Total Gain / Loss on Warehouse */}
        <div className={`rounded-2xl border p-4 shadow-lg ${
          isProfit
            ? "border-emerald-500/25 bg-gradient-to-br from-emerald-500/10 to-teal-500/5"
            : "border-red-500/25 bg-gradient-to-br from-red-500/10 to-rose-500/5"
        }`}>
          <div className="flex items-center justify-between">
            <span className={`text-xs font-medium ${isProfit ? "text-emerald-300" : "text-red-300"}`}>
              {isProfit ? "سود ارزش انبار نسبت به خرید 🔺" : "افت ارزش انبار نسبت به خرید 🔻"}
            </span>
            <span className={`rounded-lg px-2 py-0.5 text-[10px] font-bold ${
              isProfit ? "bg-emerald-500/20 text-emerald-300" : "bg-red-500/20 text-red-300"
            }`}>
              {isProfit ? "+" : ""}{meta.total_inventory_profit_loss_percent}%
            </span>
          </div>
          <div className={`mt-2 text-xl font-bold font-mono ${isProfit ? "text-emerald-400" : "text-red-400"}`}>
            {isProfit ? "+" : ""}{formatPrice(profitLoss)}
          </div>
          <div className="mt-1 text-[11px] text-gray-400">
            قیمت اولیه انبار: {formatPrice(meta.total_inventory_base_value)}
          </div>
        </div>

        {/* Total Warehouse Quantity */}
        <div className="rounded-2xl border border-purple-500/20 bg-gradient-to-br from-purple-500/10 to-fuchsia-500/5 p-4 shadow-lg">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-purple-300">مجموع کل قطعات در انبار</span>
            <span className="rounded-lg bg-purple-500/20 px-2 py-0.5 text-[10px] text-purple-300">موجودی فیزیکی</span>
          </div>
          <div className="mt-2 text-xl font-bold text-white font-mono">
            {(meta.total_inventory_quantity || 0).toLocaleString("fa-IR")} عدد کالا
          </div>
          <div className="mt-1 text-[11px] text-gray-400">
            در ۱۰۰ ردیف محصول نو و استوک
          </div>
        </div>

        {/* Price Changes Breakdown */}
        <div className="rounded-2xl border border-white/5 bg-bg-panel p-4 shadow-lg flex flex-col justify-between">
          <div className="text-xs font-medium text-gray-300">وضعیت نوسان قیمت اقلام</div>
          <div className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
            <div className="rounded-xl bg-red-500/10 p-2 border border-red-500/20">
              <span className="text-red-400 font-bold block text-sm">{meta.increased_count || 0}</span>
              <span className="text-[10px] text-red-400/80">گران‌تر 🔺</span>
            </div>
            <div className="rounded-xl bg-emerald-500/10 p-2 border border-emerald-500/20">
              <span className="text-emerald-400 font-bold block text-sm">{meta.decreased_count || 0}</span>
              <span className="text-[10px] text-emerald-400/80">ارزان‌تر 🔻</span>
            </div>
            <div className="rounded-xl bg-amber-500/10 p-2 border border-amber-500/20">
              <span className="text-amber-400 font-bold block text-sm">{meta.out_of_stock_count || 0}</span>
              <span className="text-[10px] text-amber-400/80">ناموجود</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="rounded-2xl border border-white/5 bg-bg-panel p-4 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        {/* Tabs */}
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => { setCategory("all"); setStatusFilter("all"); }}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-medium transition-all ${
              category === "all" && statusFilter === "all"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
            }`}
          >
            همه اقلام ({meta.total_products || 100})
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
                ? "bg-purple-500 text-white shadow-md shadow-purple-500/20"
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
              placeholder="جستجوی نام یا کد انبار (C80, L02)..."
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
            <option value="quantity_desc">📦 بیشترین موجودی در انبار</option>
            <option value="quantity_asc">کمترین موجودی در انبار</option>
            <option value="profit_desc">💰 بیشترین سود ارزش موجودی انبار (🔺)</option>
            <option value="profit_asc">بیشترین افت ارزش موجودی انبار (🔻)</option>
            <option value="change_desc">بیشترین درصد افزایش قیمت (🔺)</option>
            <option value="change_asc">بیشترین درصد کاهش قیمت (🔻)</option>
            <option value="price_desc">گران‌ترین قیمت روز</option>
            <option value="price_asc">ارزان‌ترین قیمت روز</option>
            <option value="row_index">شماره ردیف انبار (پیش‌فرض)</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          خطا در بارگذاری داده‌ها: {error}
        </div>
      )}

      {/* Desktop Table View */}
      <div className="hidden lg:block overflow-hidden rounded-2xl border border-white/10 bg-bg-panel shadow-2xl">
        <table className="w-full text-right text-xs">
          <thead>
            <tr className="border-b border-white/10 bg-white/[0.02] text-gray-400 font-medium">
              <th className="px-3.5 py-3.5 w-12 text-center">ردیف</th>
              <th className="px-3.5 py-3.5 w-24">کد انبار</th>
              <th className="px-3.5 py-3.5 w-1/4">نام محصول</th>
              <th className="px-3.5 py-3.5 text-center w-28">موجودی انبار</th>
              <th className="px-3.5 py-3.5 text-center w-28">نمودار روند قیمت</th>
              <th className="px-3.5 py-3.5 text-left">قیمت قبلی انبار (پایه)</th>
              <th className="px-3.5 py-3.5 text-left">قیمت روز دیجی‌کالا</th>
              <th className="px-3.5 py-3.5 text-center">تغییر نسبت به پایه</th>
              <th className="px-3.5 py-3.5 text-left">اثر بر ارزش کل انبار</th>
              <th className="px-3.5 py-3.5 text-left">قیمت ترب (کف)</th>
              <th className="px-3.5 py-3.5 text-center w-24">لینک</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {data.items.map((p) => {
              const basePrice = p.base_price || p.initial_digikala_price || p.initial_torob_price;
              const isProfitRow = (p.inventory_profit_loss || 0) > 0;
              const isLossRow = (p.inventory_profit_loss || 0) < 0;

              return (
                <tr key={p.id} className="hover:bg-white/[0.03] transition-colors group">
                  <td className="px-3.5 py-3.5 text-center text-gray-500 font-mono text-[11px]">
                    {p.row_index}
                  </td>
                  <td className="px-3.5 py-3.5 font-mono">
                    <span className="rounded bg-white/5 px-2 py-1 text-[11px] font-semibold text-sky-400 border border-white/5">
                      {p.warehouse_title || "—"}
                    </span>
                  </td>
                  <td className="px-3.5 py-3.5">
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
                  <td className="px-3.5 py-3.5 text-center font-mono">
                    <QuantityBadge qty={p.quantity} />
                  </td>
                  <td className="px-3.5 py-3.5 text-center">
                    <Sparkline
                      points={p.sparkline}
                      isUp={p.status === "increased"}
                      isDown={p.status === "decreased"}
                      width={85}
                      height={26}
                    />
                  </td>
                  <td className="px-3.5 py-3.5 text-left font-mono text-gray-400 font-medium">
                    {formatPrice(basePrice)}
                  </td>
                  <td className="px-3.5 py-3.5 text-left font-mono">
                    {p.current_digikala_price ? (
                      <div>
                        <div className="font-semibold text-white">
                          {formatPrice(p.current_digikala_price)}
                        </div>
                        {p.digikala_available && (
                          <span className="inline-block rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] text-emerald-400">
                            موجود آنلاین
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
                  <td className="px-3.5 py-3.5 text-center">
                    <ChangeBadge percent={p.price_change_percent} amount={p.price_change_amount} />
                  </td>
                  <td className="px-3.5 py-3.5 text-left font-mono">
                    {p.quantity && p.inventory_profit_loss ? (
                      <div className="flex flex-col items-start">
                        <span className={`text-xs font-semibold ${isProfitRow ? 'text-emerald-400' : isLossRow ? 'text-red-400' : 'text-gray-400'}`}>
                          {isProfitRow ? "+" : ""}{formatPrice(p.inventory_profit_loss)}
                        </span>
                        <span className="text-[10px] text-gray-500">
                          ارزش: {formatPrice(p.inventory_value_current)}
                        </span>
                      </div>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                  <td className="px-3.5 py-3.5 text-left font-mono">
                    {p.current_torob_price ? (
                      <span className="text-sky-300 font-semibold">{formatPrice(p.current_torob_price)}</span>
                    ) : p.initial_torob_price ? (
                      <span className="text-gray-400">{formatPrice(p.initial_torob_price)} <span className="text-[10px] text-gray-500">(اکسل)</span></span>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                  <td className="px-3.5 py-3.5 text-center">
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
                <td colSpan={11} className="px-4 py-16 text-center text-gray-500">
                  هیچ محصولی با معیارهای فیلتر یا جستجوی فعلی یافت نشد.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card List View */}
      <div className="grid grid-cols-1 gap-3 lg:hidden">
        {data.items.map((p) => {
          const basePrice = p.base_price || p.initial_digikala_price || p.initial_torob_price;
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
                    <QuantityBadge qty={p.quantity} />
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

              {/* Sparkline on Mobile */}
              <div className="flex items-center justify-between py-1 border-y border-white/5">
                <span className="text-[10px] text-gray-500">روند تغییر قیمت:</span>
                <Sparkline
                  points={p.sparkline}
                  isUp={p.status === "increased"}
                  isDown={p.status === "decreased"}
                  width={110}
                  height={24}
                />
              </div>

              <div className="grid grid-cols-2 gap-2 rounded-xl bg-bg p-3 text-xs">
                <div>
                  <span className="text-gray-500 block text-[10px]">قیمت قبلی انبار (پایه)</span>
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

              {p.quantity && p.inventory_profit_loss ? (
                <div className="flex items-center justify-between text-[11px] px-2">
                  <span className="text-gray-500">سود/زیان کل این کالا در انبار:</span>
                  <span className={`font-mono font-bold ${p.inventory_profit_loss > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {p.inventory_profit_loss > 0 ? "+" : ""}{formatPrice(p.inventory_profit_loss)}
                  </span>
                </div>
              ) : null}

              <div className="flex items-center justify-between pt-1">
                <Link
                  to={`/products/${p.id}`}
                  className="text-xs text-sky-400 hover:underline"
                >
                  مشاهده جزئیات و فروشندگان ←
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
            محصولی با این فیلتر یافت نشد.
          </div>
        )}
      </div>

      {loading && (
        <div className="py-12 text-center text-sm text-gray-500">
          در حال بارگذاری اطلاعات و نمودارها...
        </div>
      )}
    </div>
  );
}
