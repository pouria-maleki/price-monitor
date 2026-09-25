import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { fetchProduct, fetchHistory, fetchShops } from "../api";
import PriceChart from "./PriceChart";

function formatPrice(v) {
  if (v === null || v === undefined) return "—";
  return v.toLocaleString("fa-IR") + " تومان";
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
  const torobPrice = product.torob_price;
  const dkPrice = product.digikala_price;
  const marketAvg = product.market_avg_price;
  const isDiscrepant = product.is_discrepant;
  const diffPercent = product.diff_percent;
  const diffAmount = product.diff_amount;

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
          </div>

          <div className="flex flex-wrap gap-2">
            {product.royaldigi_url && (
              <a
                href={product.royaldigi_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-sky-500/15 border border-sky-500/30 px-3.5 py-2 text-xs font-bold text-sky-300 hover:bg-sky-500/25 transition-colors"
              >
                👑 مشاهده در رویال‌دیجی ↗
              </a>
            )}
            {product.torob_url && (
              <a
                href={product.torob_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-red-500/10 border border-red-500/20 px-3.5 py-2 text-xs font-bold text-red-300 hover:bg-red-500/20 transition-colors"
              >
                🧅 لینک اصلی ترب ↗
              </a>
            )}
            {product.digikala_url && (
              <a
                href={product.digikala_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-pink-500/10 border border-pink-500/20 px-3.5 py-2 text-xs font-bold text-pink-300 hover:bg-pink-500/20 transition-colors"
              >
                🔴 مشاهده در دیجی‌کالا ↗
              </a>
            )}
          </div>
        </div>

        {/* Pricing Comparison Grid */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 border-t border-white/5 pt-5">
          <div className={`rounded-xl p-3.5 border ${isDiscrepant ? 'bg-red-950/30 border-red-500/30' : 'bg-slate-950/60 border-white/5'}`}>
            <div className="text-[11px] text-gray-400">قیمت رویال‌دیجی</div>
            <div className={`mt-1 font-mono text-base font-bold ${isDiscrepant ? 'text-red-300' : 'text-emerald-400'}`}>
              {formatPrice(royalPrice)}
            </div>
            {isDiscrepant && <div className="text-[10px] text-red-400 mt-0.5">⚠️ مغایرت با بازار</div>}
          </div>

          <div className="rounded-xl bg-slate-950/60 border border-white/5 p-3.5">
            <div className="text-[11px] text-gray-400">قیمت ترب (لینک اصلی)</div>
            <div className="mt-1 font-mono text-base font-semibold text-gray-200">
              {formatPrice(torobPrice)}
            </div>
            {product.torob_offers && product.torob_offers.length > 1 && (
              <div className="text-[10px] text-gray-500 mt-0.5">{product.torob_offers.length} فروشنده</div>
            )}
          </div>

          <div className="rounded-xl bg-slate-950/60 border border-white/5 p-3.5">
            <div className="text-[11px] text-gray-400">قیمت دیجی‌کالا</div>
            <div className="mt-1 font-mono text-base font-semibold text-gray-200">
              {formatPrice(dkPrice)}
            </div>
          </div>

          <div className="rounded-xl bg-slate-950/60 border border-white/5 p-3.5">
            <div className="text-[11px] text-gray-400">میانگین بازار</div>
            <div className="mt-1 font-mono text-base font-bold text-gray-300">
              {formatPrice(marketAvg)}
            </div>
            {diffPercent !== null && diffPercent !== undefined && (
              <div className={`text-[10px] font-bold mt-0.5 ${diffAmount > 0 ? 'text-red-400' : 'text-sky-300'}`}>
                اختلاف: {diffPercent > 0 ? `+${diffPercent}% گران‌تر` : `${diffPercent}% ارزان‌تر`}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* History Chart */}
      <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-xl backdrop-blur">
        <h3 className="mb-4 text-base font-semibold text-white">روند تغییرات قیمت</h3>
        <PriceChart history={history} />
      </div>

      {/* Seller Breakdown */}
      <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 shadow-xl backdrop-blur space-y-4">
        <h3 className="text-base font-semibold text-white">مقایسه قیمت با پلتفرم‌ها</h3>
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
                    <span className="inline-flex rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                      موجود
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center">
                    {s.url ? (
                      <a href={s.url} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline">
                        مشاهده ↗
                      </a>
                    ) : (
                      "—"
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
