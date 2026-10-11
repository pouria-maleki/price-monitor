import json
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
data_path = BASE_DIR / "data" / "products_data.json"

dashboard_template = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>سامانه مانیتورینگ قیمت رویال‌دیجی · پایش ۵ فروشنده اول ترب · دیجی‌کالا</title>
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
    <div class="w-full flex items-center justify-between px-3 py-2 sm:px-5">
      <div class="flex items-center gap-2.5">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 via-sky-500 to-indigo-600 text-lg font-bold shadow-lg shadow-sky-500/20">
          👑
        </div>
        <div>
          <div class="flex items-center gap-2">
            <h1 class="text-sm sm:text-base font-bold text-white">سامانه هوشمند مانیتورینگ قیمت رویال‌دیجی</h1>
            <span class="rounded-full bg-emerald-500/15 border border-emerald-500/30 px-2 py-0.5 text-[9px] font-bold text-emerald-400 hidden sm:inline-block">
              ● استراتژی رقابت ۵ رتبه اول ترب
            </span>
          </div>
          <p class="text-[11px] text-gray-400">مقایسه لحظه‌ای قیمت رویال با ۵ فروشنده اول ترب و دیجی‌کالا | آپدیت روزانه ۱۰:۰۰ صبح</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <button onclick="openUpdateModal()" class="inline-flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-sky-500 to-blue-600 px-3 py-1.5 text-xs font-bold text-white hover:from-sky-400 hover:to-blue-500 transition shadow-md shadow-sky-500/20 active:scale-95">
          🔄 شروع آپدیت قیمت‌ها
        </button>
        <a href="گزارش_انبار_قیمت_به_روز.xlsx" download class="inline-flex items-center gap-1.5 rounded-lg bg-emerald-500/20 border border-emerald-500/30 px-2.5 py-1.5 text-xs font-bold text-emerald-300 hover:bg-emerald-500/30 transition shadow-sm">
          📥 اکسل مغایرت‌ها
        </a>
      </div>
    </div>
  </header>

  <!-- Main Container -->
  <main class="w-full px-2 sm:px-4 py-3 space-y-3">

    <!-- KPI Statistics (Top-5 Strategy Focused) -->
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
      <div class="rounded-xl border border-white/5 bg-slate-900/60 p-2.5 shadow-sm backdrop-blur">
        <span class="text-[11px] font-medium text-gray-400">تعداد کل محصولات</span>
        <div class="text-lg font-bold text-white mt-0.5" id="kpi-total-prods">۱۶۶</div>
        <span class="text-[10px] text-gray-500">کالای پایش‌شده</span>
      </div>

      <div class="rounded-xl border border-white/5 bg-slate-900/60 p-2.5 shadow-sm backdrop-blur">
        <span class="text-[11px] font-medium text-gray-400">موجودی فیزیکی کل</span>
        <div class="text-lg font-bold text-sky-400 mt-0.5" id="kpi-total-qty">۶۵۳</div>
        <span class="text-[10px] text-gray-500">عدد در انبار</span>
      </div>

      <div class="rounded-xl border border-emerald-500/25 bg-emerald-950/20 p-2.5 shadow-sm backdrop-blur">
        <span class="text-[11px] font-medium text-emerald-300">در ۵ تای اول ترب</span>
        <div class="text-lg font-bold text-emerald-400 mt-0.5" id="kpi-in-top-5">۰</div>
        <span class="text-[10px] text-emerald-400/80">رقابتی و ایده‌آل</span>
      </div>

      <div class="rounded-xl border border-red-500/25 bg-red-950/20 p-2.5 shadow-sm backdrop-blur">
        <span class="text-[11px] font-medium text-red-300">❌ گران‌تر از ۵ اول</span>
        <div class="text-lg font-bold text-red-400 mt-0.5" id="kpi-higher-top-5">۰</div>
        <span class="text-[10px] text-red-400/80">خارج از ۵ رتبه</span>
      </div>

      <div class="rounded-xl border border-amber-500/25 bg-amber-950/20 p-2.5 shadow-sm backdrop-blur">
        <span class="text-[11px] font-medium text-amber-300">⚠️ ارزان‌تر از رتبه ۱</span>
        <div class="text-lg font-bold text-amber-400 mt-0.5" id="kpi-lower-top-1">۰</div>
        <span class="text-[10px] text-amber-400/80">کف قیمت / سود سوخته</span>
      </div>

      <div class="rounded-xl border border-white/5 bg-slate-900/60 p-2.5 shadow-sm backdrop-blur">
        <span class="text-[11px] font-medium text-gray-400">ناموجود رویال</span>
        <div class="text-lg font-bold text-gray-400 mt-0.5" id="kpi-no-royal">۰</div>
        <span class="text-[10px] text-gray-500">عدم موجودی/قیمت</span>
      </div>
    </div>

    <!-- Filters, Search & Sort -->
    <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-2 bg-slate-900/40 p-2 rounded-xl border border-white/5">
      <!-- Tabs -->
      <div class="flex flex-wrap items-center gap-1.5">
        <button onclick="setTab('all')" id="tab-all" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-sky-500 text-white shadow-md shadow-sky-500/20">
          همه (۱۶۶)
        </button>

        <button onclick="setTab('alerts')" id="tab-alerts" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-red-500/10 text-red-300 border border-red-500/20 hover:bg-red-500/20 flex items-center gap-1">
          <span>⚠️ اخطارها</span>
          <span class="bg-red-950/60 px-1 py-0.2 rounded text-[9px]" id="badge-alerts">۰</span>
        </button>

        <button onclick="setTab('higher_than_top_5')" id="tab-higher_than_top_5" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-rose-500/10 text-rose-300 border border-rose-500/20 hover:bg-rose-500/20 flex items-center gap-1">
          <span>❌ بالاتر از ۵</span>
          <span class="bg-rose-950/60 px-1 py-0.2 rounded text-[9px]" id="badge-higher">۰</span>
        </button>

        <button onclick="setTab('lower_than_top_1')" id="tab-lower_than_top_1" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-amber-500/10 text-amber-300 border border-amber-500/20 hover:bg-amber-500/20 flex items-center gap-1">
          <span>⚠️ زیر رتبه ۱</span>
          <span class="bg-amber-950/60 px-1 py-0.2 rounded text-[9px]" id="badge-lower">۰</span>
        </button>

        <button onclick="setTab('in_top_5')" id="tab-in_top_5" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 hover:bg-emerald-500/20 flex items-center gap-1">
          <span>✓ در ۵ اول</span>
          <span class="bg-emerald-950/60 px-1 py-0.2 rounded text-[9px]" id="badge-in-top-5">۰</span>
        </button>

        <button onclick="setTab('no_royal')" id="tab-no_royal" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-slate-700/30 text-gray-400 border border-white/5 hover:bg-white/10 flex items-center gap-1">
          <span>⚪ ناموجود</span>
          <span class="bg-slate-800 px-1 py-0.2 rounded text-[9px]" id="badge-no-royal">۰</span>
        </button>

        <button onclick="setTab('new')" id="tab-new" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-teal-500/10 text-teal-300 border border-teal-500/20 hover:bg-teal-500/20 flex items-center gap-1">
          <span>🟢 نو</span>
          <span class="bg-teal-950/60 px-1 py-0.2 rounded text-[9px]" id="badge-new">۸۹</span>
        </button>

        <button onclick="setTab('stock')" id="tab-stock" class="tab-btn rounded-lg px-2.5 py-1 text-[11px] font-bold transition bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/20 flex items-center gap-1">
          <span>🟣 استوک</span>
          <span class="bg-purple-950/60 px-1 py-0.2 rounded text-[9px]" id="badge-stock">۷۷</span>
        </button>
      </div>

      <!-- Search & Sort -->
      <div class="flex items-center gap-2">
        <div class="relative w-40 sm:w-52">
          <input
            type="text"
            id="search-input"
            oninput="handleSearch()"
            placeholder="جستجو کالا..."
            class="w-full rounded-lg border border-white/10 bg-slate-950/60 px-2 py-1 text-xs text-white placeholder-gray-500 focus:border-sky-500 focus:outline-none transition"
          />
        </div>

        <select
          id="sort-select"
          onchange="handleSort()"
          class="rounded-lg border border-white/10 bg-slate-950/60 px-2 py-1 text-xs text-white focus:border-sky-500 focus:outline-none transition"
        >
          <option value="file_order">ترتیب فایل اکسل</option>
          <option value="quantity_desc">بیشترین موجودی</option>
          <option value="quantity_asc">کمترین موجودی</option>
          <option value="diff_desc">بیشترین اختلاف قیمت</option>
          <option value="royal_desc">گران‌ترین رویال</option>
          <option value="royal_asc">ارزان‌ترین رویال</option>
        </select>
      </div>
    </div>

    <!-- Main Table (Compact, Zero horizontal scroll) -->
    <div class="overflow-x-auto rounded-xl border border-white/10 bg-slate-900/60 shadow-xl backdrop-blur">
      <table class="w-full text-right text-[11px] leading-tight">
        <thead>
          <tr class="border-b border-white/10 bg-slate-950/80 text-gray-300 font-semibold select-none text-[10px]">
            <th class="px-1 py-2 text-center w-7">#</th>
            <th class="px-1 py-2 text-center w-11">نوع</th>
            <th class="px-2 py-2 min-w-[160px] max-w-[220px]">نام محصول و مشخصات</th>
            <th class="px-1 py-2 text-center w-14">موجودی</th>
            <th class="px-1.5 py-2 text-center w-24 bg-amber-500/10 text-amber-200 border-x border-white/10">رویال‌دیجی</th>
            <th class="px-1 py-2 text-center w-20 bg-sky-950/25 text-sky-300">ترب ۱</th>
            <th class="px-1 py-2 text-center w-20 bg-sky-950/15 text-sky-200">ترب ۲</th>
            <th class="px-1 py-2 text-center w-20 text-gray-300">ترب ۳</th>
            <th class="px-1 py-2 text-center w-20 text-gray-400">ترب ۴</th>
            <th class="px-1 py-2 text-center w-20 text-gray-400">ترب ۵</th>
            <th class="px-1 py-2 text-center w-20 text-pink-300">دیجی‌کالا</th>
            <th class="px-1.5 py-2 text-center w-28">وضعیت ترب</th>
            <th class="px-1 py-2 text-center w-14">روند</th>
            <th class="px-1 py-2 text-center w-14">لینک</th>
          </tr>
        </thead>
        <tbody id="table-body" class="divide-y divide-white/5">
          <!-- Rows rendered dynamically -->
        </tbody>
      </table>
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
              <span class="text-emerald-400 font-bold">پایش ۵ فروشنده اول ترب (دید کامل خریداران)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">منبع قیمت‌های سایت ما:</span>
              <span class="text-sky-300 font-semibold">خروجی ووکامرس (wc-product-export)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">زمان‌بندی خودکار:</span>
              <span class="text-white font-bold">هر روز ساعت ۱۰:۰۰ صبح (تهران)</span>
            </div>
            <div class="flex justify-between items-center">
              <span class="text-gray-400">تکنیک ضد بن:</span>
              <span class="text-sky-300">تاخیر تصادفی انسانی (۲.۵ الی ۴.۵ ثانیه)</span>
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
      const w = 46;
      const h = 16;
      const pad = 1.5;
      const strokeColor = isDiscrepant ? '#ef4444' : '#10b981';

      const coords = points.map((p, i) => {
        const x = pad + (i / (points.length - 1)) * (w - 2 * pad);
        const y = h - pad - ((p - min) / range) * (h - 2 * pad);
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');

      return `
        <svg width="${w}" height="${h}" class="overflow-visible inline-block">
          <polyline fill="none" stroke="${strokeColor}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" points="${coords}" />
          <circle cx="${coords.split(' ').pop().split(',')[0]}" cy="${coords.split(' ').pop().split(',')[1]}" r="2" fill="${strokeColor}" />
        </svg>
      `;
    }

    function renderTable() {
      const tbody = document.getElementById('table-body');
      let filtered = [...allItems];

      // Tab filters
      if (currentTab === 'alerts') {
        filtered = filtered.filter(x => x.is_alert);
      } else if (currentTab === 'higher_than_top_5') {
        filtered = filtered.filter(x => (x.top5_status || x.top3_status) === 'higher_than_top_5' || (x.top5_status || x.top3_status) === 'higher_than_top_3');
      } else if (currentTab === 'lower_than_top_1') {
        filtered = filtered.filter(x => (x.top5_status || x.top3_status) === 'lower_than_top_1');
      } else if (currentTab === 'in_top_5') {
        filtered = filtered.filter(x => (x.top5_status || x.top3_status) === 'in_top_5' || (x.top5_status || x.top3_status) === 'in_top_3');
      } else if (currentTab === 'no_royal') {
        filtered = filtered.filter(x => (x.top5_status || x.top3_status) === 'no_royal' || !x.royaldigi_price);
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
            <td colspan="14" class="py-12 text-center text-gray-400">
              هیچ کالایی با فیلترهای انتخابی یافت نشد.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = filtered.map(item => {
        const isNew = item.item_type === 'New';
        const typeBadge = isNew
          ? `<span class="inline-block rounded bg-emerald-500/15 border border-emerald-500/30 px-1 py-0.5 text-[9px] font-bold text-emerald-300">نو</span>`
          : `<span class="inline-block rounded bg-purple-500/15 border border-purple-500/30 px-1 py-0.5 text-[9px] font-bold text-purple-300">استوک</span>`;

        // Top 5 Status Badge
        let statusBadge = '';
        let royalCellClass = 'border-white/5 text-gray-200 border-x';
        let royalSubtitle = '';
        const st = item.top5_status || item.top3_status;

        if (st === 'higher_than_top_5' || st === 'higher_than_top_3') {
          royalCellClass = 'bg-red-500/15 border-red-500/30 text-red-300 font-bold border-x';
          royalSubtitle = `<div class="text-[9px] text-red-400 font-semibold mt-0.5">❌ بالای ۵</div>`;
          statusBadge = `
            <div class="flex flex-col items-center gap-0.5">
              <span class="inline-block rounded border border-red-500/30 bg-red-500/15 px-1 py-0.5 text-[9px] font-bold text-red-300">
                ❌ بالای ۵
              </span>
              <span class="text-[8px] text-red-400/90 font-mono text-center">
                ${item.top5_rank_label || item.top3_rank_label || ''}
              </span>
            </div>
          `;
        } else if (st === 'lower_than_top_1') {
          royalCellClass = 'bg-amber-500/15 border-amber-500/30 text-amber-300 font-bold border-x';
          royalSubtitle = `<div class="text-[9px] text-amber-400 font-semibold mt-0.5">⚠️ زیر ۱</div>`;
          statusBadge = `
            <div class="flex flex-col items-center gap-0.5">
              <span class="inline-block rounded border border-amber-500/30 bg-amber-500/15 px-1 py-0.5 text-[9px] font-bold text-amber-300">
                ⚠️ زیر ۱
              </span>
              <span class="text-[8px] text-amber-400/90 font-mono text-center">
                ${item.top5_rank_label || item.top3_rank_label || ''}
              </span>
            </div>
          `;
        } else if (st === 'in_top_5' || st === 'in_top_3') {
          royalCellClass = 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300 font-bold border-x';
          royalSubtitle = `<div class="text-[9px] text-emerald-400 font-semibold mt-0.5">✓ در ۵ اول</div>`;
          statusBadge = `
            <div class="flex flex-col items-center gap-0.5">
              <span class="inline-block rounded border border-emerald-500/30 bg-emerald-500/15 px-1.5 py-0.5 text-[9px] font-bold text-emerald-300">
                ${item.top5_badge || item.top3_badge || '✓ در ۵ اول'}
              </span>
            </div>
          `;
        } else if (st === 'no_royal' || !item.royaldigi_price) {
          royalSubtitle = `<div class="text-[9px] text-gray-500 mt-0.5">ناموجود رویال</div>`;
          statusBadge = `<span class="text-gray-500 text-[9px]">ناموجود رویال</span>`;
        } else if (st === 'no_torob') {
          statusBadge = `<span class="text-gray-500 text-[9px]">ناموجود ترب</span>`;
        } else {
          statusBadge = `<span class="text-gray-500 text-[9px]">—</span>`;
        }

        return `
          <tr class="hover:bg-white/[0.02] transition-colors border-b border-white/5">
            <td class="px-1 py-1 text-center font-mono text-gray-500 text-[10px]">${item.file_order}</td>
            <td class="px-1 py-1 text-center">${typeBadge}</td>
            <td class="px-2 py-1 min-w-[160px] max-w-[220px]">
              <div class="font-semibold text-gray-100 line-clamp-2 text-[11px] leading-snug" title="${item.name}">${item.name}</div>
              <div class="flex flex-wrap items-center gap-1.5 mt-0.5 text-[9px] text-gray-400">
                ${item.woo_id ? `<span class="font-mono bg-white/5 px-1 py-0.2 rounded text-gray-300">ID: ${item.woo_id}</span>` : ''}
                ${item.warranty ? `<span class="text-gray-500 truncate max-w-[100px]">${item.warranty}</span>` : ''}
                ${item.notes ? `<span class="text-amber-400/80 bg-amber-500/10 px-1 py-0.2 rounded text-[8px]">${item.notes}</span>` : ''}
              </div>
            </td>
            <td class="px-1 py-1 text-center font-mono text-[10px] text-gray-300">
              ${item.quantity !== null && item.quantity !== undefined ? item.quantity + ' عدد' : '<span class=\"text-gray-500\">ناموجود</span>'}
            </td>

            <!-- RoyalDigi Price Column (Alert colored or explicit ناموجود) -->
            <td class="px-1.5 py-1 text-center font-mono ${royalCellClass}">
              <div class="text-[11px] font-bold">${formatPrice(item.royaldigi_price)}</div>
              ${royalSubtitle}
            </td>

            <!-- Torob 1 (Rank 1) -->
            <td class="px-1 py-1 text-center font-mono text-[11px] text-sky-200 bg-sky-950/15 font-semibold">
              ${formatPrice(item.torob_1)}
            </td>

            <!-- Torob 2 (Rank 2) -->
            <td class="px-1 py-1 text-center font-mono text-[11px] text-gray-300">
              ${formatPrice(item.torob_2)}
            </td>

            <!-- Torob 3 (Rank 3) -->
            <td class="px-1 py-1 text-center font-mono text-[11px] text-gray-400">
              ${formatPrice(item.torob_3)}
            </td>

            <!-- Torob 4 (Rank 4) -->
            <td class="px-1 py-1 text-center font-mono text-[11px] text-gray-400">
              ${formatPrice(item.torob_4)}
            </td>

            <!-- Torob 5 (Rank 5) -->
            <td class="px-1 py-1 text-center font-mono text-[11px] text-gray-400">
              ${formatPrice(item.torob_5)}
            </td>

            <!-- Digikala Price -->
            <td class="px-1 py-1 text-center font-mono text-[11px] text-pink-300">
              ${formatPrice(item.digikala_price)}
            </td>

            <!-- Torob Competitive Status -->
            <td class="px-1.5 py-1 text-center">${statusBadge}</td>

            <!-- Sparkline Trend -->
            <td class="px-1 py-1 text-center">
              <div class="w-12 mx-auto">${createSparklineSvg(item.sparkline, item.is_alert)}</div>
            </td>

            <!-- External Links -->
            <td class="px-1 py-1 text-center">
              <div class="flex items-center justify-center gap-1">
                ${item.royaldigi_url ? `<a href="${item.royaldigi_url}" target="_blank" rel="noopener" title="سایت رویال‌دیجی" class="p-0.5 rounded bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 text-xs">👑</a>` : ''}
                ${item.torob_url ? `<a href="${item.torob_url}" target="_blank" rel="noopener" title="لینک اصلی ترب" class="p-0.5 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 text-xs">🧅</a>` : ''}
                ${item.digikala_url ? `<a href="${item.digikala_url}" target="_blank" rel="noopener" title="دیجی‌کالا" class="p-0.5 rounded bg-pink-500/10 hover:bg-pink-500/20 text-pink-400 text-xs">🔴</a>` : ''}
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
        activeBtn.classList.remove('bg-white/5', 'text-gray-300', 'bg-red-500/10', 'bg-rose-500/10', 'bg-amber-500/10', 'bg-emerald-500/10', 'bg-teal-500/10', 'bg-purple-500/10', 'bg-slate-700/30');
        if (tab === 'alerts' || tab === 'higher_than_top_5') {
          activeBtn.classList.add('bg-red-500', 'text-white');
        } else if (tab === 'lower_than_top_1') {
          activeBtn.classList.add('bg-amber-500', 'text-white');
        } else if (tab === 'in_top_5') {
          activeBtn.classList.add('bg-emerald-500', 'text-white');
        } else if (tab === 'no_royal') {
          activeBtn.classList.add('bg-slate-600', 'text-white');
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
        document.getElementById('kpi-in-top-5').textContent = formatNumber(meta.in_top_5_count || meta.in_top_3_count || 0);
        document.getElementById('kpi-higher-top-5').textContent = formatNumber(meta.higher_than_top_5_count || meta.higher_than_top_3_count || 0);
        document.getElementById('kpi-lower-top-1').textContent = formatNumber(meta.lower_than_top_1_count || 0);
        document.getElementById('kpi-no-royal').textContent = formatNumber(meta.no_royal_count || 0);

        document.getElementById('badge-alerts').textContent = formatNumber(meta.alerts_total || 0);
        document.getElementById('badge-higher').textContent = formatNumber(meta.higher_than_top_5_count || meta.higher_than_top_3_count || 0);
        document.getElementById('badge-lower').textContent = formatNumber(meta.lower_than_top_1_count || 0);
        document.getElementById('badge-in-top-5').textContent = formatNumber(meta.in_top_5_count || meta.in_top_3_count || 0);
        document.getElementById('badge-no-royal').textContent = formatNumber(meta.no_royal_count || 0);
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
