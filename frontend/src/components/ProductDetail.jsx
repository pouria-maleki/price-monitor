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
        setHistory(h);
        setShops(s);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="py-10 text-center text-sm text-gray-500">در حال بارگذاری...</div>;
  if (error)
    return (
      <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
        خطا: {error}
      </div>
    );
  if (!product) return null;

  return (
    <div>
      <Link to="/" className="mb-4 inline-block text-sm text-sky-400 hover:underline">
        ← بازگشت به لیست محصولات
      </Link>

      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-white">{product.name}</h2>
          <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-400">
            {product.warehouse_title && <span>کد انبار: {product.warehouse_title}</span>}
            {product.quantity !== null && <span>موجودی: {product.quantity}</span>}
            <span>دسته: {product.category === "new" ? "نو" : "استوک"}</span>
          </div>
        </div>
        <div className="flex gap-2">
          {product.digikala_url && (
            <a
              href={product.digikala_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg bg-red-500/10 px-3 py-2 text-xs font-medium text-red-300 hover:bg-red-500/20"
            >
              مشاهده در دیجی‌کالا
            </a>
          )}
          {product.torob_url && (
            <a
              href={product.torob_url}
              target="_blank"
              rel="noreferrer"
              className="rounded-lg bg-sky-500/10 px-3 py-2 text-xs font-medium text-sky-300 hover:bg-sky-500/20"
            >
              مشاهده در ترب
            </a>
          )}
        </div>
      </div>

      <h3 className="mb-2 text-sm font-semibold text-gray-300">روند قیمت</h3>
      <div className="mb-6">
        <PriceChart history={history} />
      </div>

      <h3 className="mb-2 text-sm font-semibold text-gray-300">فروشندگان</h3>
      <div className="overflow-hidden rounded-xl border border-white/10 bg-bg-panel">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/10 text-right text-gray-400">
              <th className="px-4 py-3 font-medium">فروشگاه</th>
              <th className="px-4 py-3 font-medium">قیمت</th>
              <th className="px-4 py-3 font-medium">وضعیت</th>
              <th className="px-4 py-3 font-medium">آخرین بررسی</th>
              <th className="px-4 py-3 font-medium"></th>
            </tr>
          </thead>
          <tbody>
            {shops.map((s) => (
              <tr key={s.id} className="border-b border-white/5 last:border-0">
                <td className="px-4 py-3 text-gray-200">{s.store.name.replace("torob:", "")}</td>
                <td className="px-4 py-3 font-medium text-white">{formatPrice(s.price)}</td>
                <td className="px-4 py-3">
                  {s.is_available ? (
                    <span className="text-emerald-400">موجود</span>
                  ) : (
                    <span className="text-gray-500">ناموجود</span>
                  )}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {new Date(s.checked_at).toLocaleString("fa-IR")}
                </td>
                <td className="px-4 py-3">
                  {s.url && (
                    <a href={s.url} target="_blank" rel="noreferrer" className="text-xs text-sky-400 hover:underline">
                      لینک
                    </a>
                  )}
                </td>
              </tr>
            ))}
            {shops.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-500">
                  هنوز اطلاعات فروشنده‌ای ثبت نشده است
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
