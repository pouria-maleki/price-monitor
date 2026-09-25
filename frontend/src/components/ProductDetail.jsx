import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchProduct, fetchHistory, fetchShops } from "../api";
import PriceChart from "./PriceChart";

function formatPrice(v) {
  if (v === null || v === undefined || v === 0) {
    return <span className="text-gray-500 font-medium">ناموجود</span>;
  }
  return <span>{v.toLocaleString("fa-IR")} ت</span>;
}

export default function ProductDetail() {
  const { id } = useParams();
  const [product, setProduct] = useState(null);
  const [history, setHistory] = useState([]);
  const [shops, setShops] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchProduct(id), fetchHistory(id), fetchShops(id)])
      .then(([p, h, s]) => {
        setProduct(p);
        setHistory(h || []);
        setShops(s || []);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="py-16 text-center text-sm text-gray-500">در حال بارگذاری اطلاعات محصول...</div>;
  if (error || !product)
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-sm text-red-300">
        محصول مورد نظر یافت نشد.
        <div className="mt-3">
          <Link to="/" className="text-sky-400 hover:underline">← بازگشت به داشبورد محصولات</Link>
        </div>
      </div>
    );

  const isNew = product.item_type === "New";
  const royalPrice = product.royaldigi_price;
  const t1 = product.torob_1;
  const t2 = product.torob_2;
  const t3 = product.torob_3;
  const dkPrice = product.digikala_price;

  let royalBoxClass = "bg-slate-950/60 border-white/5";
  let royalTextClass = "text-gray-200";
  let royalSubtitle = null;

  if (product.top3_status === "higher_than_top_3") {
    royalBoxClass = "bg-red-950/30 border-red-500/30";
    royalTextClass = "text-red-300";
    royalSubtitle = <div className="text-[11px] text-red-400 mt-1 font-bold">❌ گران‌تر از ۳ تای اول ترب ({product.top3_rank_label})</div>;
  } else if (product.top3_status === "lower_than_top_1") {
    royalBoxClass = "bg-amber-950/30 border-amber-500/30";
    royalTextClass = "text-amber-300";
    royalSubtitle = <div className="text-[11px] text-amber-400 mt-1 font-bold">⚠️ ارزان‌تر از رتبه ۱ ترب ({product.top3_rank_label})</div>;
  } else if (product.top3_status === "in_top_3") {
    royalBoxClass = "bg-emerald-950/30 border-emerald-500/30";
    royalTextClass = "text-emerald-300";
    royalSubtitle = <div className="text-[11px] text-emerald-400 mt-1 font-bold">✓ رقابتی: {product.top3_badge}</div>;
  }

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300 transition-colors">
        ← بازگشت به لیست محصولات
      </Link>

      {/* Product Hero Card */}
      <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-xl backdrop-blur">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-xs text-sky-400">
                ردیف #{product.file_order} {product.woo_id ? `(Woo ID: ${product.woo_id})` : ""}
              </span>
              <span className={`text-xs rounded-full px-2.5 py-0.5 font-bold ${isNew ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-purple-500/15 text-purple-300 border border-purple-500/30'}`}>
                {isNew ? "🟢 کالای نو" : "🟣 کالای استوک"}
              </span>
              {product.quantity !== null && product.quantity !== undefined && (
                <span className="rounded-lg bg-slate-800 px-2.5 py-0.5 text-xs text-gray-200 font-bold">
                  موجودی انبار: {product.quantity} عدد
                </span>
              )}
            </div>

            <h2 className="text-xl font-bold text-white leading-relaxed">{product.name}</h2>
            {product.warranty && <p className="text-xs text-gray-400">گارانتی: {product.warranty}</p>}
            {product.notes && <p className="text-xs text-amber-300/80 bg-amber-500/10 p-2 rounded-lg inline-block">{product.notes}</p>}
            {product.top3_explanation && (
              <p className="text-xs text-sky-300 bg-sky-950/40 border border-sky-500/20 p-2.5 rounded-xl">
                💡 وضعیت رقابت ترب: {product.top3_explanation}
              </p>
            )}
          </div>

          <div className="flex flex-wrap gap-2">
            {product.royaldigi_url && (
              <a
                href={product.royaldigi_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-sky-500/15 border border-sky-500/30 px-3.5 py-2 text-xs font-bold text-sky-300 hover:bg-sky-500/25 transition-colors"
              >
                👑 رویال‌دیجی ↗
              </a>
            )}
            {product.torob_url && (
              <a
                href={product.torob_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-red-500/10 border border-red-500/20 px-3.5 py-2 text-xs font-bold text-red-300 hover:bg-red-500/20 transition-colors"
              >
                🧅 ترب اصلی ↗
              </a>
            )}
            {product.digikala_url && (
              <a
                href={product.digikala_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-pink-500/10 border border-pink-500/20 px-3.5 py-2 text-xs font-bold text-pink-300 hover:bg-pink-500/20 transition-colors"
              >
                🔴 دیجی‌کالا ↗
              </a>
            )}
          </div>
        </div>

        {/* Pricing Comparison Grid (Royal + Torob 1, 2, 3 + Digikala) */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-5 border-t border-white/5 pt-5">
          <div className={`rounded-xl p-3.5 border ${royalBoxClass}`}>
            <div className="text-[11px] text-gray-400">قیمت رویال‌دیجی</div>
            <div className={`mt-1 font-mono text-base font-bold ${royalTextClass}`}>
              {formatPrice(royalPrice)}
            </div>
            {royalSubtitle}
          </div>

          <div className="rounded-xl bg-sky-950/20 border border-sky-500/20 p-3.5">
            <div className="text-[11px] text-sky-300">ترب ۱ (فروشنده اول)</div>
            <div className="mt-1 font-mono text-base font-bold text-sky-200">
              {formatPrice(t1)}
            </div>
            <div className="text-[10px] text-sky-400/80 mt-1">کف قیمت بازار</div>
          </div>

          <div className="rounded-xl bg-slate-950/60 border border-white/5 p-3.5">
            <div className="text-[11px] text-gray-400">ترب ۲ (فروشنده دوم)</div>
            <div className="mt-1 font-mono text-base font-semibold text-gray-200">
              {formatPrice(t2)}
            </div>
            <div className="text-[10px] text-gray-500 mt-1">رتبه دوم</div>
          </div>

          <div className="rounded-xl bg-slate-950/60 border border-white/5 p-3.5">
            <div className="text-[11px] text-gray-400">ترب ۳ (فروشنده سوم)</div>
            <div className="mt-1 font-mono text-base font-semibold text-gray-200">
              {formatPrice(t3)}
            </div>
            <div className="text-[10px] text-gray-500 mt-1">سقف رتبه ۳ ترب</div>
          </div>

          <div className="rounded-xl bg-slate-950/60 border border-white/5 p-3.5">
            <div className="text-[11px] text-gray-400">دیجی‌کالا</div>
            <div className="mt-1 font-mono text-base font-semibold text-pink-300">
              {formatPrice(dkPrice)}
            </div>
            <div className="text-[10px] text-gray-500 mt-1">قیمت دیجی‌کالا</div>
          </div>
        </div>
      </div>

      {/* History Chart */}
      <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-xl backdrop-blur">
        <h3 className="mb-4 text-base font-semibold text-white">روند تغییرات قیمت</h3>
        <PriceChart history={history} />
      </div>

      {/* Platform Price Table */}
      <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-xl backdrop-blur space-y-4">
        <h3 className="text-base font-semibold text-white">فروشگاه‌های رصد شده</h3>
        <div className="overflow-hidden rounded-xl border border-white/10">
          <table className="w-full text-right text-xs">
            <thead>
              <tr className="border-b border-white/10 bg-slate-950/60 text-gray-400 font-medium">
                <th className="px-4 py-3">منبع قیمت</th>
                <th className="px-4 py-3 text-left">قیمت</th>
                <th className="px-4 py-3 text-center">وضعیت موجودی</th>
                <th className="px-4 py-3 text-center">لینک</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {shops.map((s, idx) => (
                <tr key={idx} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3 font-medium text-gray-200">{s.shop_name}</td>
                  <td className="px-4 py-3 text-left font-mono font-semibold text-white">{formatPrice(s.price)}</td>
                  <td className="px-4 py-3 text-center">
                    {s.is_available ? (
                      <span className="inline-flex rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                        موجود
                      </span>
                    ) : (
                      <span className="inline-flex rounded-full bg-slate-800 px-2 py-0.5 text-xs text-gray-500">
                        ناموجود
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {s.url ? (
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">
                        مشاهده ↗
                      </a>
                    ) : (
                      <span className="text-gray-600">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
