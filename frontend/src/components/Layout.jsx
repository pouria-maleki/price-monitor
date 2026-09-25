import { Link } from "react-router-dom";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen bg-bg">
      <header className="sticky top-0 z-20 border-b border-white/5 bg-slate-950/80 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 via-sky-500 to-indigo-600 text-lg font-bold shadow-md shadow-sky-500/20">
              👑
            </div>
            <div>
              <h1 className="text-base font-bold text-white sm:text-lg">مانیتورینگ قیمت رویال‌دیجی</h1>
              <p className="text-[11px] text-gray-400">پایش روزانه قیمت‌های رویال‌دیجی · ترب · دیجی‌کالا</p>
            </div>
          </Link>

          <div className="flex items-center gap-2">
            <span className="hidden sm:inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 text-xs text-emerald-400 font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>آپدیت روزانه ۱۰:۰۰ صبح</span>
            </span>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}
