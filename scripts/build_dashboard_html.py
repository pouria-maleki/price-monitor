import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
data_path = BASE_DIR / "data" / "products_data.json"
with open(data_path, "r", encoding="utf-8") as f:
    products_json_str = f.read()

dashboard_template = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>سامانه مانیتورینگ قیمت رویال‌دیجی · پایش ۳ فروشنده اول ترب · دیجی‌کالا</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            bg: { DEFAULT: '#0b1120', panel: '#111827', card: '#161f31' }
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css');
    body { font-family: 'Vazirmatn', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0b1120; }
    ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #374151; }
  </style>
</head>
<body class="bg-bg text-gray-100 min-h-screen">

  <!-- Header -->
  <header class="sticky top-0 z-30 border-b border-white/10 bg-bg/85 backdrop-blur-md">
    <div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 via-sky-500 to-indigo-600 text-xl font-bold shadow-lg shadow-sky-500/20">
          👑
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-base sm:text-lg font-bold text-white">سامانه هوشمند مانیتورینگ قیمت رویال‌دیجی</h1>
            <span class="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[10px] font-bold text-emerald-400 hidden sm:inline-block">
              ● استراتژی رقابت ۳ رتبه اول ترب
            </span>
          </div>
          <p class="text-xs text-gray-400">مقایسه لحظه‌ای قیمت رویال با ۳ فروشنده اول ترب و دیجی‌کالا | زمان‌بندی: روزانه ساعت ۱۰:۰۰ صبح</p>
        </div>
      </div>
      <div class="flex items-center gap-2.5">
        <button onclick="openUpdateModal()" class="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-3.5 py-2 text-xs font-bold text-white hover:from-sky-400 hover:to-blue-500 transition shadow-md shadow-sky-500/20 active:scale-95">
          🔄 شروع آپدیت قیمت‌ها
        </button>
        <a href="گزارش_انبار_قیمت_به_روز.xlsx" download class="inline-flex items-center gap-2 rounded-xl bg-emerald-500/20 border border-emerald-500/30 px-3 py-2 text-xs font-bold text-emerald-300 hover:bg-emerald-500/30 transition shadow-sm">
          📥 اکسل مغایرت‌ها
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="mx-auto max-w-7xl px-4 py-6 sm:px-6 space-y-6">

    <!-- KPI Statistics (Top-3 Strategy Focused) -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
      <div class="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
        <span class="text-xs font-medium text-gray-400">تعداد کل محصولات</span>
        <div class="text-xl font-bold text-white mt-1" id="kpi-total-prods">۱۶۶</div>
        <span class="text-[11px] text-gray-500">کالای پایش‌شده</span>
      </div>

      <div class="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
        <span class="text-xs font-medium text-gray-400">موجودی فیزیکی کل</span>
        <div class="text-xl font-bold text-sky-400 mt-1" id="kpi-total-qty">۶۵۳</div>
        <span class="text-[11px] text-gray-500">عدد در انبار</span>
      </div>

      <div class="rounded-2xl border border-emerald-500/25 bg-emerald-950/20 p-4 shadow-sm backdrop-blur">
        <span class="text-xs font-medium text-emerald-300">در ۳ تای اول ترب (ایده‌آل)</span>
        <div class="text-xl font-bold text-emerald-400 mt-1" id="kpi-in-top-3">۷۷</div>
        <span class="text-[11px] text-emerald-400/80">کالای کاملاً رقابتی</span>
      </div>

      <div class="rounded-2xl border border-red-500/25 bg-red-950/20 p-4 shadow-sm backdrop-blur">
        <span class="text-xs font-medium text-red-300">❌ گران‌تر از ۳ تای اول</span>
        <div class="text-xl font-bold text-red-400 mt-1" id="kpi-higher-top-3">۳۸</div>
        <span class="text-[11px] text-red-400/80">خارج از دید خریدار ترب</span>
      </div>

      <div class="rounded-2xl border border-amber-500/25 bg-amber-950/20 p-4 shadow-sm backdrop-blur">
        <span class="text-xs font-medium text-amber-300">⚠️ ارزان‌تر از رتبه ۱</span>
        <div class="text-xl font-bold text-amber-400 mt-1" id="kpi-lower-top-1">۴</div>
        <span class="text-[11px] text-amber-400/80">ارزان‌فروشی غیرضروری</span>
      </div>

      <div class="rounded-2xl border border-white/5 bg-slate-900/60 p-4 shadow-sm backdrop-blur">
        <span class="text-xs font-medium text-gray-400">نو / استوک</span>
        <div class="text-base sm:text-lg font-bold text-white mt-1 flex items-center gap-1.5" id="kpi-new-stock">
          <span class="text-emerald-400">۸۹ نو</span>
          <span class="text-gray-600">/</span>
          <span class="text-purple-400">۷۷ استوک</span>
        </div>
        <span class="text-[11px] text-gray-500">تفکیک وضعیت کالا</span>
      </div>
    </div>

    <!-- Filters, Search & Sort -->
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 bg-slate-900/40 p-4 rounded-2xl border border-white/5">
      <!-- Tabs -->
      <div class="flex flex-wrap items-center gap-2">
        <button onclick="setTab('all')" id="tab-all" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-sky-500 text-white shadow-md shadow-sky-500/20">
          همه محصولات (۱۶۶)
        </button>

        <button onclick="setTab('alerts')" id="tab-alerts" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-red-500/10 text-red-300 border border-red-500/20 hover:bg-red-500/20 flex items-center gap-1.5">
          <span>⚠️ کلیه اخطارها</span>
          <span class="bg-red-950/60 px-1.5 py-0.5 rounded text-[10px]" id="badge-alerts">۴۲</span>
        </button>

        <button onclick="setTab('higher_than_top_3')" id="tab-higher_than_top_3" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-rose-500/10 text-rose-300 border border-rose-500/20 hover:bg-rose-500/20 flex items-center gap-1.5">
          <span>❌ گران‌تر از ۳ تای اول</span>
          <span class="bg-rose-950/60 px-1.5 py-0.5 rounded text-[10px]" id="badge-higher">۳۸</span>
        </button>

        <button onclick="setTab('lower_than_top_1')" id="tab-lower_than_top_1" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-amber-500/10 text-amber-300 border border-amber-500/20 hover:bg-amber-500/20 flex items-center gap-1.5">
          <span>⚠️ ارزان‌تر از کف</span>
          <span class="bg-amber-950/60 px-1.5 py-0.5 rounded text-[10px]" id="badge-lower">۴</span>
        </button>

        <button onclick="setTab('in_top_3')" id="tab-in_top_3" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20 flex items-center gap-1.5">
          <span>✓ در ۳ تای اول ترب</span>
          <span class="bg-emerald-950/60 px-1.5 py-0.5 rounded text-[10px]" id="badge-in-top-3">۷۷</span>
        </button>

        <button onclick="setTab('new')" id="tab-new" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-teal-500/10 text-teal-300 border border-teal-500/20 hover:bg-teal-500/20 flex items-center gap-1.5">
          <span>🟢 نو</span>
          <span class="bg-teal-950/60 px-1.5 py-0.5 rounded text-[10px]" id="badge-new">۸۹</span>
        </button>

        <button onclick="setTab('stock')" id="tab-stock" class="tab-btn rounded-xl px-3.5 py-1.5 text-xs font-bold transition bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/20 flex items-center gap-1.5">
          <span>🟣 استوک</span>
          <span class="bg-purple-950/60 px-1.5 py-0.5 rounded text-[10px]" id="badge-stock">۷۷</span>
        </button>
      </div>

      <!-- Search & Sort -->
      <div class="flex flex-col sm:flex-row items-center gap-2.5">
        <div class="relative w-full sm:w-64">
          <input
            type="text"
            id="search-input"
            oninput="handleSearch()"
            placeholder="جستجو نام کالا، کد یا یادداشت..."
            class="w-full rounded-xl border border-white/10 bg-slate-950/60 px-3.5 py-2 text-xs text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none transition"
          />
        </div>

        <select
          id="sort-select"
          onchange="handleSort()"
          class="w-full sm:w-auto rounded-xl border border-white/10 bg-slate-950/60 px-3 py-2 text-xs text-white focus:border-sky-500 focus:outline-none transition"
        >
          <option value="file_order">ترتیب فایل اکسل (پیش‌فرض)</option>
          <option value="quantity_desc">بیشترین موجودی انبار</option>
          <option value="quantity_asc">کمترین موجودی انبار</option>
          <option value="diff_desc">بیشترین اختلاف (گران‌ترین نسبت به رتبه ۳)</option>
          <option value="royal_desc">گران‌ترین قیمت رویال</option>
          <option value="royal_asc">ارزان‌ترین قیمت رویال</option>
        </select>
      </div>
    </div>

    <!-- Main Table -->
    <div class="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/60 shadow-xl backdrop-blur">
      <div class="overflow-x-auto">
        <table class="w-full text-right text-xs">
          <thead>
            <tr class="border-b border-white/10 bg-slate-950/80 text-gray-300 font-semibold select-none">
              <th class="px-3 py-3.5 text-center w-12">ردیف</th>
              <th class="px-3 py-3.5 text-center w-20">نوع</th>
              <th class="px-4 py-3.5 min-w-[220px]">نام محصول و مشخصات</th>
              <th class="px-3 py-3.5 text-center w-20">موجودی</th>
              <th class="px-3 py-3.5 text-center w-36 bg-amber-500/10 text-amber-200 border-x border-white/10">
                قیمت رویال‌دیجی
              </th>
              <th class="px-3 py-3.5 text-center w-32 bg-sky-950/20 text-sky-300">ترب ۱ (اول)</th>
              <th class="px-3 py-3.5 text-center w-32 bg-sky-950/10 text-sky-200">ترب ۲ (دوم)</th>
              <th class="px-3 py-3.5 text-center w-32 text-gray-300">ترب ۳ (سوم)</th>
              <th class="px-3 py-3.5 text-center w-32 text-pink-300">دیجی‌کالا</th>
              <th class="px-4 py-3.5 text-center w-48">وضعیت رقابت در ترب</th>
              <th class="px-3 py-3.5 text-center w-24">روند</th>
              <th class="px-3 py-3.5 text-center w-24">لینک‌ها</th>
            </tr>
          </thead>
          <tbody id="table-body" class="divide-y divide-white/5">
            <!-- Rows rendered dynamically -->
          </tbody>
        </table>
      </div>
    </div>

    <!-- Update Instructions Modal -->
    <div id="update-modal" class="fixed inset-0 z-50 hidden items-center justify-center bg-black/75 p-4 backdrop-blur-sm">
      <div class="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl space-y-4">
        <div class="flex items-center justify-between border-b border-white/10 pb-3">
          <h3 class="text-base font-bold text-white flex items-center gap-2">
            <span>🔄 شروع و مدیریت به‌روزرسانی قیمت‌ها</span>
          </h3>
          <button onclick="closeUpdateModal()" class="text-gray-400 hover:text-white">✕</button>
        </div>

        <div class="space-y-3 text-xs text-gray-300 leading-relaxed">
          <div class="rounded-xl bg-slate-950/60 p-3.5 border border-white/5 space-y-2">
            <div class="flex justify-between items-center">
              <span class="text-gray-400">استراتژی ترب:</span>
              <span class="text-emerald-400 font-bold">پایش ۳ فروشنده اول ترب (دید اصلی خریدار)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">زمان‌بندی خودکار:</span>
              <span class="text-white font-bold">هر روز ساعت ۱۰:۰۰ صبح (تهران)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">تکنیک ضد بن:</span>
              <span class="text-sky-300">تاخیر تصادفی انسانی (۲.۵ الی ۴.۵ ثانیه)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">دامنه استخراج:</span>
              <span class="text-white">رویال‌دیجی · ۳ فروشنده اول ترب (لینک اصلی) · دیجی‌کالا</span>
            </div>
          </div>

          <div class="rounded-xl bg-sky-950/25 border border-sky-500/25 p-3.5 space-y-1.5">
            <p class="font-bold text-sky-200">🚀 نحوه اجرای دستی و آنی در گیت‌هاب اکشنز:</p>
            <p class="text-gray-400 text-[11px]">
              با کلیک روی دکمه زیر وارد بخش Actions در گیت‌هاب می‌شوید و کافیست دکمه <span class="text-white font-mono bg-white/10 px-1 py-0.5 rounded">Run workflow</span> را بزنید تا کل سیستم با شرایط ضد بن به‌روزرسانی شده و سایت منتشر شود.
            </p>
          </div>
        </div>

        <div class="flex items-center justify-end gap-2.5 pt-2">
          <button onclick="closeUpdateModal()" class="rounded-xl px-4 py-2 text-xs font-medium text-gray-400 hover:text-white bg-white/5 transition">
            بستن
          </button>
          <a
            href="https://github.com/pouria-maleki/price-monitor/actions"
            target="_blank"
            rel="noopener noreferrer"
            class="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 px-4 py-2 text-xs font-bold text-white hover:from-sky-400 hover:to-blue-500 transition shadow-lg shadow-sky-500/20"
          >
            <span>ورود به تب Actions گیت‌هاب و اجرای آنی</span>
            <span>↗</span>
          </a>
        </div>
      </div>
    </div>

  </main>

  <!-- Embedded Data Fallback -->
  <script id="embedded-data" type="application/json">
__EMBEDDED_DATA__
  </script>

  <script>
    let allItems = [];
    let currentTab = 'all';
    let currentSort = 'file_order';
    let searchQuery = '';

    function formatNumber(num) {
      if (num === null || num === undefined) return 'ناموجود';
      return Number(num).toLocaleString('fa-IR');
    }

    function formatPrice(num) {
      if (num === null || num === undefined || num === 0) {
        return '<span class="text-gray-500 font-medium">ناموجود</span>';
      }
      return Number(num).toLocaleString('fa-IR') + ' ت';
    }

    function formatBillions(num) {
      if (!num) return '۰';
      const b = num / 1000000000;
      if (b >= 1) return b.toFixed(2) + ' میلیارد تومان';
      const m = num / 1000000;
      return m.toFixed(1) + ' میلیون تومان';
    }

    function createSparklineSvg(points, isDiscrepant) {
      if (!points || points.length < 2) return '';
      const min = Math.min(...points);
      const max = Math.max(...points);
      const range = (max - min) || 1;
      const w = 70;
      const h = 22;
      const pad = 2;
      const strokeColor = isDiscrepant ? '#ef4444' : '#10b981';

      const coords = points.map((p, i) => {
        const x = pad + (i / (points.length - 1)) * (w - 2 * pad);
        const y = h - pad - ((p - min) / range) * (h - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');

      return `
        <svg width="${w}" height="${h}" class="overflow-visible inline-block">
          <polyline fill="none" stroke="${strokeColor}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" points="${coords}" />
          <circle cx="${coords.split(' ').pop().split(',')[0]}" cy="${coords.split(' ').pop().split(',')[1]}" r="2.5" fill="${strokeColor}" />
        </svg>
      `;
    }

    function renderTable() {
      const tbody = document.getElementById('table-body');
      let filtered = [...allItems];

      // Tab filters
      if (currentTab === 'alerts') {
        filtered = filtered.filter(x => x.is_alert);
      } else if (currentTab === 'higher_than_top_3') {
        filtered = filtered.filter(x => x.top3_status === 'higher_than_top_3');
      } else if (currentTab === 'lower_than_top_1') {
        filtered = filtered.filter(x => x.top3_status === 'lower_than_top_1');
      } else if (currentTab === 'in_top_3') {
        filtered = filtered.filter(x => x.top3_status === 'in_top_3');
      } else if (currentTab === 'new') {
        filtered = filtered.filter(x => x.item_type === 'New');
      } else if (currentTab === 'stock') {
        filtered = filtered.filter(x => x.item_type === 'Stock');
      }

      // Search filter
      if (searchQuery.trim()) {
        const q = searchQuery.trim().toLowerCase();
        filtered = filtered.filter(x =>
          (x.name && x.name.toLowerCase().includes(q)) ||
          (x.woo_id && String(x.woo_id).includes(q)) ||
          (x.notes && x.notes.toLowerCase().includes(q)) ||
          (x.warranty && x.warranty.toLowerCase().includes(q))
        );
      }

      // Sorting - Default is exact file_order (1 to 166)
      if (currentSort === 'file_order') {
        filtered.sort((a, b) => (a.file_order || 0) - (b.file_order || 0));
      } else if (currentSort === 'quantity_desc') {
        filtered.sort((a, b) => (b.quantity || 0) - (a.quantity || 0) || (a.file_order - b.file_order));
      } else if (currentSort === 'quantity_asc') {
        filtered.sort((a, b) => (a.quantity || 0) - (b.quantity || 0) || (a.file_order - b.file_order));
      } else if (currentSort === 'diff_desc') {
        filtered.sort((a, b) => (b.diff_from_target || 0) - (a.diff_from_target || 0));
      } else if (currentSort === 'royal_desc') {
        filtered.sort((a, b) => (b.royaldigi_price || 0) - (a.royaldigi_price || 0));
      } else if (currentSort === 'royal_asc') {
        filtered.sort((a, b) => (a.royaldigi_price || 0) - (b.royaldigi_price || 0));
      }

      if (filtered.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="12" class="py-12 text-center text-gray-400">
              هیچ کالایی با فیلترهای انتخابی یافت نشد.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = filtered.map(item => {
        const isNew = item.item_type === 'New';
        const typeBadge = isNew
          ? `<span class="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[11px] font-bold text-emerald-300">🟢 نو</span>`
          : `<span class="inline-flex items-center gap-1 rounded-full bg-purple-500/15 border border-purple-500/30 px-2 py-0.5 text-[11px] font-bold text-purple-300">🟣 استوک</span>`;

        // Top 3 Status Badge
        let statusBadge = '';
        let royalCellClass = 'border-white/5 text-gray-200 border-x';
        let royalSubtitle = '';

        if (item.top3_status === 'higher_than_top_3') {
          royalCellClass = 'bg-red-500/15 border-red-500/30 text-red-300 font-bold border-x';
          royalSubtitle = `<div class="text-[10px] text-red-400 font-semibold flex items-center justify-center gap-1 mt-0.5"><span>❌ گران‌تر از ۳ تای اول</span></div>`;
          statusBadge = `
            <div class="flex flex-col items-center gap-0.5">
              <span class="inline-flex items-center gap-1 rounded-lg border border-red-500/30 bg-red-500/15 px-2 py-0.5 text-[11px] font-bold text-red-300">
                ❌ گران‌تر از ۳ تای اول
              </span>
              <span class="text-[10px] text-red-400/90 font-mono text-center leading-tight">
                ${item.top3_rank_label || ''}
              </span>
            </div>
          `;
        } else if (item.top3_status === 'lower_than_top_1') {
          royalCellClass = 'bg-amber-500/15 border-amber-500/30 text-amber-300 font-bold border-x';
          royalSubtitle = `<div class="text-[10px] text-amber-400 font-semibold flex items-center justify-center gap-1 mt-0.5"><span>⚠️ ارزان‌تر از رتبه ۱</span></div>`;
          statusBadge = `
            <div class="flex flex-col items-center gap-0.5">
              <span class="inline-flex items-center gap-1 rounded-lg border border-amber-500/30 bg-amber-500/15 px-2 py-0.5 text-[11px] font-bold text-amber-300">
                ⚠️ ارزان‌تر از رتبه ۱
              </span>
              <span class="text-[10px] text-amber-400/90 font-mono text-center leading-tight">
                ${item.top3_rank_label || ''}
              </span>
            </div>
          `;
        } else if (item.top3_status === 'in_top_3') {
          royalCellClass = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300 font-bold border-x';
          royalSubtitle = `<div class="text-[10px] text-emerald-400 font-semibold mt-0.5">✓ در ۳ تای اول ترب</div>`;
          statusBadge = `
            <div class="flex flex-col items-center gap-0.5">
              <span class="inline-flex items-center gap-1 rounded-lg border border-emerald-500/30 bg-emerald-500/15 px-2.5 py-0.5 text-[11px] font-bold text-emerald-300">
                ${item.top3_badge || '✓ در ۳ تای اول'}
              </span>
              <span class="text-[10px] text-emerald-400/80">رقابتی و فعال</span>
            </div>
          `;
        } else if (item.top3_status === 'no_royal') {
          royalSubtitle = `<div class="text-[10px] text-gray-500 mt-0.5">ناموجود در سایت</div>`;
          statusBadge = `<span class="text-gray-500 text-[11px]">ناموجود در رویال</span>`;
        } else if (item.top3_status === 'no_torob') {
          statusBadge = `<span class="text-gray-500 text-[11px]">ناموجود در ترب</span>`;
        } else {
          statusBadge = `<span class="text-gray-500 text-[11px]">—</span>`;
        }

        return `
          <tr class="hover:bg-white/[0.02] transition-colors">
            <td class="px-3 py-3 text-center font-mono text-gray-500">${item.file_order}</td>
            <td class="px-3 py-3 text-center">${typeBadge}</td>
            <td class="px-4 py-3">
              <div class="font-semibold text-gray-100 max-w-sm line-clamp-2">${item.name}</div>
              <div class="flex flex-wrap items-center gap-2 mt-1 text-[11px] text-gray-400">
                ${item.woo_id ? `<span class="font-mono bg-white/5 px-1.5 py-0.5 rounded text-gray-300">ID: ${item.woo_id}</span>` : ''}
                ${item.warranty ? `<span class="text-gray-500 line-clamp-1">${item.warranty}</span>` : ''}
                ${item.notes ? `<span class="text-amber-400/80 bg-amber-500/10 px-1.5 py-0.5 rounded text-[10px]">${item.notes}</span>` : ''}
              </div>
            </td>
            <td class="px-3 py-3 text-center">
              <span class="inline-flex rounded-lg bg-slate-800 px-2 py-1 font-mono font-bold text-gray-200">
                ${item.quantity !== null && item.quantity !== undefined ? item.quantity + ' عدد' : 'ناموجود'}
              </span>
            </td>

            <!-- RoyalDigi Price Column (Alert colored) -->
            <td class="px-3 py-3 text-center font-mono ${royalCellClass}">
              <div class="text-xs sm:text-sm">${formatPrice(item.royaldigi_price)}</div>
              ${royalSubtitle}
            </td>

            <!-- Torob 1 (Rank 1) -->
            <td class="px-3 py-3 text-center font-mono text-sky-200 bg-sky-950/10">
              <div class="text-xs font-semibold">${formatPrice(item.torob_1)}</div>
            </td>

            <!-- Torob 2 (Rank 2) -->
            <td class="px-3 py-3 text-center font-mono text-gray-300">
              <div class="text-xs">${formatPrice(item.torob_2)}</div>
            </td>

            <!-- Torob 3 (Rank 3) -->
            <td class="px-3 py-3 text-center font-mono text-gray-400">
              <div class="text-xs">${formatPrice(item.torob_3)}</div>
            </td>

            <!-- Digikala Price -->
            <td class="px-3 py-3 text-center font-mono text-pink-300">
              <div class="text-xs">${formatPrice(item.digikala_price)}</div>
            </td>

            <!-- Torob Competitive Status -->
            <td class="px-4 py-3 text-center">${statusBadge}</td>

            <!-- Sparkline Trend -->
            <td class="px-3 py-3 text-center">
              <div class="w-20 mx-auto">${createSparklineSvg(item.sparkline, item.is_alert)}</div>
            </td>

            <!-- External Links -->
            <td class="px-3 py-3 text-center">
              <div class="flex items-center justify-center gap-1.5">
                ${item.royaldigi_url ? `<a href="${item.royaldigi_url}" target="_blank" rel="noopener" title="سایت رویال‌دیجی" class="p-1 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400">👑</a>` : ''}
                ${item.torob_url ? `<a href="${item.torob_url}" target="_blank" rel="noopener" title="لینک اصلی ترب" class="p-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400">🧅</a>` : ''}
                ${item.digikala_url ? `<a href="${item.digikala_url}" target="_blank" rel="noopener" title="دیجی‌کالا" class="p-1 rounded bg-pink-500/10 hover:bg-pink-500/20 text-pink-400">🔴</a>` : ''}
              </div>
            </td>
          </tr>
        `;
      }).join('');
    }

    function setTab(tab) {
      currentTab = tab;
      document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('bg-sky-500', 'text-white', 'shadow-md', 'shadow-sky-500/20');
        if (!btn.classList.contains('border')) {
          btn.classList.add('bg-white/5', 'text-gray-300');
        }
      });
      const activeBtn = document.getElementById(`tab-${tab}`);
      if (activeBtn) {
        activeBtn.classList.remove('bg-white/5', 'text-gray-300', 'bg-red-500/10', 'bg-rose-500/10', 'bg-amber-500/10', 'bg-emerald-500/10', 'bg-teal-500/10', 'bg-purple-500/10');
        if (tab === 'alerts' || tab === 'higher_than_top_3') {
          activeBtn.classList.add('bg-red-500', 'text-white');
        } else if (tab === 'lower_than_top_1') {
          activeBtn.classList.add('bg-amber-500', 'text-white');
        } else if (tab === 'in_top_3') {
          activeBtn.classList.add('bg-emerald-500', 'text-white');
        } else if (tab === 'new') {
          activeBtn.classList.add('bg-teal-500', 'text-white');
        } else if (tab === 'stock') {
          activeBtn.classList.add('bg-purple-500', 'text-white');
        } else {
          activeBtn.classList.add('bg-sky-500', 'text-white', 'shadow-md', 'shadow-sky-500/20');
        }
      }
      renderTable();
    }

    function handleSearch() {
      searchQuery = document.getElementById('search-input').value;
      renderTable();
    }

    function handleSort() {
      currentSort = document.getElementById('sort-select').value;
      renderTable();
    }

    function openUpdateModal() {
      const m = document.getElementById('update-modal');
      m.classList.remove('hidden');
      m.classList.add('flex');
    }

    function closeUpdateModal() {
      const m = document.getElementById('update-modal');
      m.classList.add('hidden');
      m.classList.remove('flex');
    }

    async function init() {
      let data = null;
      try {
        const res = await fetch('data/products_data.json');
        if (res.ok) {
          data = await res.json();
        }
      } catch (e) {}

      if (!data) {
        try {
          const raw = document.getElementById('embedded-data').textContent;
          data = JSON.parse(raw);
        } catch (e) {}
      }

      if (data && data.items) {
        allItems = data.items;
        const meta = data.metadata || {};

        document.getElementById('kpi-total-prods').textContent = formatNumber(meta.total_products || allItems.length);
        document.getElementById('kpi-total-qty').textContent = formatNumber(meta.total_inventory_quantity || 0);
        document.getElementById('kpi-in-top-3').textContent = formatNumber(meta.in_top_3_count || 0);
        document.getElementById('kpi-higher-top-3').textContent = formatNumber(meta.higher_than_top_3_count || 0);
        document.getElementById('kpi-lower-top-1').textContent = formatNumber(meta.lower_than_top_1_count || 0);

        document.getElementById('badge-alerts').textContent = formatNumber(meta.alerts_total || 0);
        document.getElementById('badge-higher').textContent = formatNumber(meta.higher_than_top_3_count || 0);
        document.getElementById('badge-lower').textContent = formatNumber(meta.lower_than_top_1_count || 0);
        document.getElementById('badge-in-top-3').textContent = formatNumber(meta.in_top_3_count || 0);
        document.getElementById('badge-new').textContent = formatNumber(meta.new_count || 0);
        document.getElementById('badge-stock').textContent = formatNumber(meta.stock_count || 0);

        renderTable();
      }
    }

    document.addEventListener('DOMContentLoaded', init);
  </script>
</body>
</html>
"""

def generate_dashboard():
    with open(data_path, "r", encoding="utf-8") as f:
        p_str = f.read()

    dashboard_content = dashboard_template.replace("__EMBEDDED_DATA__", p_str)

    output_file = BASE_DIR / "dashboard.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(dashboard_content)
    print(f"Generated standalone dashboard.html ({len(dashboard_content):,} bytes) with all 166 products!")

    # Also copy to frontend/public/dashboard.html and frontend/dist/dashboard.html if exists
    pub_dash = BASE_DIR / "frontend" / "public" / "dashboard.html"
    pub_dash.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output_file, pub_dash)
    print(f"Copied dashboard.html to {pub_dash}")

    dist_dash = BASE_DIR / "frontend" / "dist" / "dashboard.html"
    if dist_dash.parent.exists():
        shutil.copy2(output_file, dist_dash)
        print(f"Copied dashboard.html to {dist_dash}")

if __name__ == "__main__":
    generate_dashboard()
