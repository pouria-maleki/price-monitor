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
  if (error)
    return (
      <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6 text-sm text-red-300">
        خطا: {error}
        <div className="mt-3">
          <Link to="/" className="text-sky-400 hover:underline">← بازگشت به لیست محصولات</Link>
        </div>
      </div>
    );
  if (!product) return null;

  const basePrice = product.initial_digikala_price || product.initial_torob_price;
  const currentPrice = product.current_digikala_price || product.current_torob_price;
  const percent = product.price_change_percent;

  return (
    <div className="space-y-6">
      <Link to="/" className="inline-flex items-center gap-1 text-sm text-sky-400 hover:text-sky-300 transition-colors">
        ← بازگشت به داشبورد محصولات
      </Link>

      {/* Product Hero Card */}
      <div className="rounded-2xl border border-white/10 bg-bg-panel p-6 shadow-xl">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded bg-white/10 px-2 py-0.5 font-mono text-xs text-sky-400">
                کد انبار: {product.warehouse_title || `#${product.row_index}`}
              </span>
              <span className={`text-xs rounded px-2 py-0.5 ${product.category === 'new' ? 'bg-sky-500/10 text-sky-400' : 'bg-purple-500/10 text-purple-400'}`}>
                {product.category_fa || (product.category === 'new' ? 'محصولات نو' : 'محصولات استوک')}
              </span>
              {product.quantity !== null && product.quantity !== undefined && (
                <span className="rounded bg-white/5 px-2 py-0.5 text-xs text-gray-400">
                  موجودی انبار: {product.quantity} عدد
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-white leading-relaxed">{product.name}</h2>
          </div>

          <div className="flex flex-wrap gap-2">
            {product.digikala_url && (
              <a
                href={product.digikala_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-red-500/10 border border-red-500/20 px-3.5 py-2 text-xs font-medium text-red-300 hover:bg-red-500/20 transition-colors"
              >
                مشاهده در دیجی‌کالا ↗
              </a>
            )}
            {product.torob_url && (
              <a
                href={product.torob_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 rounded-xl bg-sky-500/10 border border-sky-500/20 px-3.5 py-2 text-xs font-medium text-sky-300 hover:bg-sky-500/20 transition-colors"
              >
                مشاهده در ترب ↗
              </a>
            )}
          </div>
        </div>

        {/* Pricing Comparison Grid */}
        <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-4 border-t border-white/5 pt-5">
          <div className="rounded-xl bg-bg p-3.5">
            <div className="text-[11px] text-gray-500">قیمت اولیه اکسل</div>
            <div className="mt-1 font-mono text-base font-semibold text-gray-300">{formatPrice(basePrice)}</div>
          </div>
          <div className="rounded-xl bg-bg p-3.5">
            <div className="text-[11px] text-gray-500">قیمت روز دیجی‌کالا</div>
            <div className="mt-1 font-mono text-base font-semibold text-emerald-400">
              {formatPrice(product.current_digikala_price)}
            </div>
            {product.digikala_seller && (
              <div className="text-[10px] text-gray-500 mt-0.5">{product.digikala_seller}</div>
            )}
          </div>
          <div className="rounded-xl bg-bg p-3.5">
            <div className="text-[11px] text-gray-500">قیمت کف ترب</div>
            <div className="mt-1 font-mono text-base font-semibold text-sky-400">
              {formatPrice(product.current_torob_price || product.initial_torob_price)}
            </div>
          </div>
          <div className="rounded-xl bg-bg p-3.5">
            <div className="text-[11px] text-gray-500">تغییر نسبت به انبار</div>
            <div className={`mt-1 font-mono text-base font-semibold ${percent > 0 ? 'text-red-400' : percent < 0 ? 'text-emerald-400' : 'text-gray-400'}`}>
              {percent !== null && percent !== undefined ? `${percent > 0 ? '▲ +' : '▼ '}${Math.abs(percent)}%` : 'بدون تغییر'}
            </div>
          </div>
        </div>
      </div>

      {/* History Chart */}
      <div className="rounded-2xl border border-white/10 bg-bg-panel p-6 shadow-xl">
        <h3 className="mb-4 text-base font-semibold text-white">روند تغییرات قیمت</h3>
        <PriceChart history={history} />
      </div>

      {/* Seller Breakdown */}
      <div className="rounded-2xl border border-white/10 bg-bg-panel p-6 shadow-xl space-y-4">
        <h3 className="text-base font-semibold text-white">فروشندگان شناخته‌شده در بازار</h3>
        <div className="overflow-hidden rounded-xl border border-white/10">
          <table className="w-full text-right text-xs">
            <thead>
              <tr className="border-b border-white/10 bg-white/[0.02] text-gray-400 font-medium">
                <th className="px-4 py-3">فروشگاه / فروشنده</th>
                <th className="px-4 py-3 text-left">قیمت</th>
                <th className="px-4 py-3 text-center">وضعیت موجودی</th>
                <th className="px-4 py-3 text-center">لینک</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {shops.map((s) => {
                const storeName = (s.store?.name || s.name || "فروشگاه").replace("torob:", "");
                return (
                  <tr key={s.id} className="hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-200">{storeName}</td>
                    <td className="px-4 py-3 text-left font-mono font-semibold text-white">{formatPrice(s.price)}</td>
                    <td className="px-4 py-3 text-center">
                      {s.is_available ? (
                        <span className="inline-block rounded bg-emerald-500/10 px-2 py-0.5 text-[11px] text-emerald-400">
                          موجود
                        </span>
                      ) : (
                        <span className="inline-block rounded bg-red-500/10 px-2 py-0.5 text-[11px] text-red-400">
                          ناموجود
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {s.url ? (
                        <a
                          href={s.url}
                          target="_blank"
                          rel="noreferrer"
                          className="rounded bg-white/5 px-2.5 py-1 text-[11px] text-sky-400 hover:bg-white/10"
                        >
                          خرید / مشاهده ↗
                        </a>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                );
              })}
              {shops.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-500">
                    اطلاعات فروشنده مجزایی برای این محصول ثبت نشده است.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
