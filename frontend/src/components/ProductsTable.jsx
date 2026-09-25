import { useEffect, useState } from "react";
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

function TypeBadge({ type }) {
  if (type === "New") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2.5 py-0.5 text-xs font-bold text-emerald-300">
        🟢 نو
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-2.5 py-0.5 text-xs font-bold text-purple-300">
      🟣 استوک
    </span>
  );
}

function DiffBadge({ item }) {
  if (!item.market_avg_price || !item.royaldigi_price) {
    return <span className="text-gray-500 text-xs">بدون قیمت بازار</span>;
  }
  if (!item.is_discrepant) {
    return (
      <span className="inline-flex items-center gap-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 text-xs font-semibold text-emerald-400">
        ✓ هم‌قیمت بازار
      </span>
    );
  }
  const isHigher = item.diff_amount > 0;
  const color = isHigher
    ? "bg-red-500/15 border-red-500/30 text-red-300"
    : "bg-sky-500/15 border-sky-500/30 text-sky-300";
  const sign = isHigher ? "▲ +" : "▼ ";
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className={`inline-flex items-center gap-1 rounded-lg border px-2 py-0.5 text-xs font-bold ${color}`}>
        {sign}{Math.abs(item.diff_percent || 0).toFixed(1)}%
      </span>
      <span className="text-[10px] text-gray-400 font-mono">
        {Math.abs(item.diff_amount || 0).toLocaleString("fa-IR")} ت
      </span>
    </div>
  );
}

export default function ProductsTable() {
  const [data, setData] = useState({ items: [], total: 0, metadata: {} });
  const [q, setQ] = useState("");
  const [itemType, setItemType] = useState("all");
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("file_order");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpdateModal, setShowUpdateModal] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchProducts({ q, itemType, filterType, sortBy })
      .then((res) => {
        setData(res);
        setError(null);
      })
      .catch((err) => setError("خطا در بارگذاری داده‌ها"))
      .finally(() => setLoading(false));
  }, [q, itemType, filterType, sortBy]);

  const meta = data.metadata || {};
  const items = data.items || [];

  return (
    <div className="space-y-6">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-gradient-to-r from-slate-900 to-slate-800 p-4 rounded-2xl border border-white/10 shadow-lg">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <span>👑 سامانه مانیتورینگ قیمت رویال‌دیجی</span>
            <span className="text-xs bg-sky-500/20 text-sky-300 border border-sky-500/30 px-2.5 py-0.5 rounded-full">نسخه هوشمند</span>
          </h2>
          <p className="text-xs text-gray-400 mt-1">
            مقایسه لحظه‌ای قیمت رویال‌دیجی با ترب (لینک اصلی) و دیجی‌کالا | زمان‌بندی: {meta.schedule_info || "هر روز ساعت ۱۰:۰۰ صبح"}
          </p>
        </div>
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowUpdateModal(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-4 py-2.5 text-xs sm:text-sm font-bold text-white hover:from-sky-400 hover:to-blue-500 shadow-lg shadow-sky-500/25 transition active:scale-95"
          >
            🔄 شروع آپدیت قیمت‌ها
          </button>
          <a
            href="گزارش_انبار_قیمت_به_روز.xlsx"
            download
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-500/20 border border-emerald-500/30 px-3.5 py-2.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/30 transition"
          >
            📥 دانلود اکسل مغایرت‌ها
          </a>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
          <span className="text-xs font-medium text-gray-400">تعداد کل کالاها</span>
          <div className="text-xl font-bold text-white mt-1">
            {(meta.total_products || items.length).toLocaleString("fa-IR")}
          </div>
          <span className="text-[11px] text-gray-500">کالای ثبت شده</span>
        </div>

        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
          <span className="text-xs font-medium text-gray-400">موجودی فیزیکی کل</span>
          <div className="text-xl font-bold text-sky-400 mt-1">
            {(meta.total_inventory_quantity || 0).toLocaleString("fa-IR")}
          </div>
          <span className="text-[11px] text-gray-500">عدد در انبار</span>
        </div>

        <div className="rounded-2xl border border-red-500/20 bg-red-950/20 p-4 shadow-sm backdrop-blur">
          <span className="text-xs font-medium text-red-300">مغایرت با بازار (قرمز)</span>
          <div className="text-xl font-bold text-red-400 mt-1">
            {(meta.discrepant_count || 0).toLocaleString("fa-IR")}
          </div>
          <span className="text-[11px] text-red-400/70">کالای نیازمند بررسی</span>
        </div>

        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
          <span className="text-xs font-medium text-gray-400">نو / استوک</span>
          <div className="text-xl font-bold text-white mt-1 flex items-center gap-1.5">
            <span className="text-emerald-400 text-base">{meta.new_count || 0} نو</span>
            <span className="text-gray-600">/</span>
            <span className="text-purple-400 text-base">{meta.stock_count || 0} استوک</span>
          </div>
          <span className="text-[11px] text-gray-500">تفکیک نوع کالا</span>
        </div>

        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
          <span className="text-xs font-medium text-gray-400">ارزش کل رویال‌دیجی</span>
          <div className="text-sm sm:text-base font-bold text-white mt-1.5 font-mono">
            {formatBillions(meta.total_inventory_royal_value)}
          </div>
          <span className="text-[11px] text-gray-500">موجودی انبار</span>
        </div>

        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
          <span className="text-xs font-medium text-gray-400">ارزش کل بازار</span>
          <div className="text-sm sm:text-base font-bold text-emerald-400 mt-1.5 font-mono">
            {formatBillions(meta.total_inventory_market_value)}
          </div>
          <span className="text-[11px] text-gray-500">میانگین ترب و دیجی‌کالا</span>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/40 p-4 rounded-2xl border border-white/5">
        {/* Tabs */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => { setFilterType("all"); setItemType("all"); }}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition ${
              filterType === "all" && itemType === "all"
                ? "bg-sky-500 text-white shadow-md shadow-sky-500/20"
                : "bg-white/5 text-gray-300 hover:bg-white/10"
            }`}
          >
            همه محصولات (۱۶۶)
          </button>

          <button
            onClick={() => setFilterType(filterType === "discrepant" ? "all" : "discrepant")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition flex items-center gap-1.5 ${
              filterType === "discrepant"
                ? "bg-red-500 text-white shadow-md shadow-red-500/20"
                : "bg-red-500/10 text-red-300 border border-red-500/20 hover:bg-red-500/20"
            }`}
          >
            <span>⚠️ فقط مغایرت‌های بازار (قرمز)</span>
            <span className="bg-red-950/60 px-1.5 py-0.2 rounded text-[10px]">{meta.discrepant_count || 117}</span>
          </button>

          <button
            onClick={() => setItemType(itemType === "New" ? "all" : "New")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition flex items-center gap-1.5 ${
              itemType === "New"
                ? "bg-emerald-500 text-white shadow-md shadow-emerald-500/20"
                : "bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20"
            }`}
          >
            <span>🟢 کالاهای نو</span>
            <span className="bg-emerald-950/60 px-1.5 py-0.2 rounded text-[10px]">{meta.new_count || 89}</span>
          </button>

          <button
            onClick={() => setItemType(itemType === "Stock" ? "all" : "Stock")}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-bold transition flex items-center gap-1.5 ${
              itemType === "Stock"
                ? "bg-purple-500 text-white shadow-md shadow-purple-500/20"
                : "bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/20"
            }`}
          >
            <span>🟣 کالاهای استوک</span>
            <span className="bg-purple-950/60 px-1.5 py-0.2 rounded text-[10px]">{meta.stock_count || 77}</span>
          </button>
        </div>

        {/* Search & Sort */}
        <div className="flex flex-col sm:flex-row items-center gap-2.5">
          <div className="relative w-full sm:w-64">
            <input
              type="text"
              placeholder="جستجو نام کالا، کد یا یادداشت..."
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-slate-950/60 px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none transition"
            />
            {q && (
              <button
                onClick={() => setQ("")}
                className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white text-xs"
              >
                ✕
              </button>
            )}
          </div>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full sm:w-auto rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-white focus:border-sky-500 focus:outline-none transition"
          >
            <option value="file_order">ترتیب فایل اکسل (پیش‌فرض)</option>
            <option value="quantity_desc">بیشترین موجودی انبار</option>
            <option value="quantity_asc">کمترین موجودی انبار</option>
            <option value="diff_desc">بیشترین اختلاف با بازار</option>
            <option value="royal_price_desc">گران‌ترین قیمت رویال</option>
            <option value="royal_price_asc">ارزان‌ترین قیمت رویال</option>
          </select>
        </div>
      </div>

      {/* Main Table */}
      <div className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 shadow-xl backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-right text-xs">
            <thead>
              <tr className="border-b border-white/10 bg-slate-950/70 text-gray-400 font-semibold select-none">
                <th className="px-3 py-3.5 text-center w-12">ردیف</th>
                <th className="px-3 py-3.5 text-center w-24">نوع</th>
                <th className="px-4 py-3.5">نام محصول و مشخصات</th>
                <th className="px-3 py-3.5 text-center w-20">موجودی</th>
                <th className="px-4 py-3.5 text-center w-36 bg-red-950/30 text-red-300 border-x border-red-500/20">
                  قیمت رویال‌دیجی (تومان)
                </th>
                <th className="px-4 py-3.5 text-center w-36">قیمت ترب (تومان)</th>
                <th className="px-4 py-3.5 text-center w-36">قیمت دیجی‌کالا (تومان)</th>
                <th className="px-4 py-3.5 text-center w-36">میانگین بازار</th>
                <th className="px-3 py-3.5 text-center w-28">وضعیت مغایرت</th>
                <th className="px-3 py-3.5 text-center w-28">روند</th>
                <th className="px-3 py-3.5 text-center w-24">لینک‌ها</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr>
                  <td colSpan="11" className="py-16 text-center text-gray-400">
                    <div className="flex flex-col items-center gap-2">
                      <div className="h-6 w-6 animate-spin rounded-full border-2 border-sky-400 border-t-transparent" />
                      <span>در حال دریافت اطلاعات محصولات...</span>
                    </div>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan="11" className="py-16 text-center text-gray-400">
                    هیچ کالایی با فیلترهای انتخابی یافت نشد.
                  </td>
                </tr>
              ) : (
                items.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-white/[0.02] transition-colors"
                  >
                    <td className="px-3 py-3.5 text-center font-mono text-gray-500">
                      {item.file_order}
                    </td>

                    <td className="px-3 py-3.5 text-center">
                      <TypeBadge type={item.item_type} />
                    </td>

                    <td className="px-4 py-3.5">
                      <div className="font-semibold text-gray-100 max-w-sm sm:max-w-md line-clamp-2">
                        {item.name}
                      </div>
                      <div className="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-gray-400">
                        {item.woo_id && (
                          <span className="font-mono bg-white/5 px-1.5 py-0.5 rounded text-gray-300">
                            ID: {item.woo_id}
                          </span>
                        )}
                        {item.warranty && (
                          <span className="text-gray-500 line-clamp-1">
                            {item.warranty}
                          </span>
                        )}
                        {item.notes && (
                          <span className="text-amber-400/80 bg-amber-500/10 px-1.5 py-0.5 rounded text-[10px]">
                            {item.notes}
                          </span>
                        )}
                      </div>
                    </td>

                    <td className="px-3 py-3.5 text-center">
                      <span className="inline-flex rounded-lg bg-slate-800 px-2.5 py-1 font-mono font-bold text-gray-200">
                        {item.quantity} عدد
                      </span>
                    </td>

                    {/* RoyalDigi Price Column (Red when discrepant) */}
                    <td
                      className={`px-4 py-3.5 text-center font-mono font-bold border-x ${
                        item.is_discrepant
                          ? "bg-red-500/15 border-red-500/30 text-red-300"
                          : "border-white/5 text-emerald-400"
                      }`}
                    >
                      <div className="text-sm">
                        {formatPrice(item.royaldigi_price)}
                      </div>
                      {item.is_discrepant ? (
                        <div className="text-[10px] text-red-400 flex items-center justify-center gap-1 mt-0.5">
                          <span>⚠️</span>
                          <span>مغایرت با بازار</span>
                        </div>
                      ) : (
                        <div className="text-[10px] text-emerald-500 mt-0.5">
                          ✓ برابر با بازار
                        </div>
                      )}
                    </td>

                    {/* Torob Price Column (from main link) */}
                    <td className="px-4 py-3.5 text-center font-mono text-gray-200">
                      <div className="text-xs">
                        {formatPrice(item.torob_price)}
                      </div>
                      {item.torob_offers && item.torob_offers.length > 1 && (
                        <span className="text-[10px] text-gray-500">
                          {item.torob_offers.length} فروشنده
                        </span>
                      )}
                    </td>

                    {/* Digikala Price Column */}
                    <td className="px-4 py-3.5 text-center font-mono text-gray-200">
                      <div className="text-xs">
                        {formatPrice(item.digikala_price)}
                      </div>
                    </td>

                    {/* Market Average Column */}
                    <td className="px-4 py-3.5 text-center font-mono font-bold text-gray-300 bg-white/[0.01]">
                      <div className="text-xs">
                        {formatPrice(item.market_avg_price)}
                      </div>
                    </td>

                    {/* Discrepancy Status */}
                    <td className="px-3 py-3.5 text-center">
                      <DiffBadge item={item} />
                    </td>

                    {/* Sparkline chart */}
                    <td className="px-3 py-3.5 text-center">
                      <div className="w-20 mx-auto">
                        <Sparkline
                          points={item.sparkline || [1, 1, 1]}
                          width={75}
                          height={24}
                          color={item.is_discrepant ? "#ef4444" : "#10b981"}
                        />
                      </div>
                    </td>

                    {/* External Links */}
                    <td className="px-3 py-3.5 text-center">
                      <div className="flex items-center justify-center gap-2">
                        {item.royaldigi_url && (
                          <a
                            href={item.royaldigi_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="مشاهده در سایت رویال‌دیجی"
                            className="p-1.5 rounded-lg bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 transition"
                          >
                            👑
                          </a>
                        )}
                        {item.torob_url && (
                          <a
                            href={item.torob_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="مشاهده لینک اصلی ترب"
                            className="p-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 transition"
                          >
                            🧅
                          </a>
                        )}
                        {item.digikala_url && (
                          <a
                            href={item.digikala_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="مشاهده در دیجی‌کالا"
                            className="p-1.5 rounded-lg bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 transition"
                          >
                            🔴
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Update Modal */}
      {showUpdateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <span>🔄 وضعیت و اجرای به‌روزرسانی قیمت‌ها</span>
              </h3>
              <button
                onClick={() => setShowUpdateModal(false)}
                className="text-gray-400 hover:text-white"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-gray-300 leading-relaxed">
              <div className="rounded-xl bg-slate-950/60 p-3 border border-white/5 space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-gray-400">آخرین زمان استخراج:</span>
                  <span className="text-white font-mono">{meta.last_updated_fa || "ثبت نشده"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">زمان‌بندی خودکار:</span>
                  <span className="text-emerald-400 font-bold">هر روز ساعت ۱۰:۰۰ صبح (تهران)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">تکنیک ضد بن:</span>
                  <span className="text-sky-300">تاخیر تصادفی انسانی (۲.۵ تا ۴.۵ ثانیه)</span>
                </div>
              </div>

              <div className="rounded-xl bg-sky-950/20 border border-sky-500/20 p-3">
                <p className="font-semibold text-sky-200">🚀 نحوه اجرای دستی و آنی در گیت‌هاب:</p>
                <p className="text-gray-400 mt-1">
                  می‌توانید همین حالا بدون صبر کردن برای ساعت ۱۰ صبح، با یک کلیک در گیت‌هاب، ورک‌فلو را اجرا کنید تا قیمت‌های جدید در سایت اعمال شوند.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                onClick={() => setShowUpdateModal(false)}
                className="rounded-xl px-4 py-2 text-xs font-medium text-gray-400 hover:text-white bg-white/5 transition"
              >
                بستن
              </button>
              <a
                href="https://github.com/pouria-maleki/price-monitor/actions"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-xl bg-sky-500 px-4 py-2 text-xs font-bold text-white hover:bg-sky-400 transition shadow-lg shadow-sky-500/20"
              >
                <span>ورود به تب Actions گیت‌هاب و Run Workflow</span>
                <span>↗</span>
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
