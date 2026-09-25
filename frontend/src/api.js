import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const client = axios.create({ baseURL: API_URL, timeout: 15000 });

let cachedData = null;

async function loadStaticData() {
  if (cachedData) return cachedData;

  const candidates = [
    "./data/products_data.json",
    "data/products_data.json",
    "/data/products_data.json",
    "/price-monitor/data/products_data.json",
  ];

  for (const url of candidates) {
    try {
      const res = await fetch(url);
      if (res.ok) {
        const text = await res.text();
        if (text && text.trim().startsWith("{")) {
          cachedData = JSON.parse(text);
          return cachedData;
        }
      }
    } catch (e) {
      // try next candidate
    }
  }
  return null;
}

export async function fetchProducts({ q, itemType = "all", filterType = "all", sortBy = "file_order" } = {}) {
  const staticData = await loadStaticData();
  if (staticData && staticData.items) {
    let items = [...staticData.items];

    // Filter by itemType: all, New, Stock
    if (itemType && itemType !== "all") {
      items = items.filter((p) => p.item_type === itemType);
    }

    // Filter by top-3 status / alerts
    if (filterType && filterType !== "all") {
      if (filterType === "alerts") {
        items = items.filter((p) => p.is_alert);
      } else if (filterType === "higher_than_top_3") {
        items = items.filter((p) => p.top3_status === "higher_than_top_3");
      } else if (filterType === "lower_than_top_1") {
        items = items.filter((p) => p.top3_status === "lower_than_top_1");
      } else if (filterType === "in_top_3") {
        items = items.filter((p) => p.top3_status === "in_top_3");
      } else if (filterType === "discrepant") {
        items = items.filter((p) => p.is_discrepant || p.is_alert);
      } else if (filterType === "matching") {
        items = items.filter((p) => p.top3_status === "in_top_3");
      } else if (filterType === "royal_higher") {
        items = items.filter((p) => p.top3_status === "higher_than_top_3");
      } else if (filterType === "royal_lower") {
        items = items.filter((p) => p.top3_status === "lower_than_top_1");
      }
    }

    // Search query
    if (q && q.trim()) {
      const query = q.trim().toLowerCase();
      items = items.filter((p) =>
        (p.name && p.name.toLowerCase().includes(query)) ||
        (p.woo_id && String(p.woo_id).includes(query)) ||
        (p.notes && p.notes.toLowerCase().includes(query)) ||
        (p.warranty && p.warranty.toLowerCase().includes(query)) ||
        (p.grade && p.grade.toLowerCase().includes(query))
      );
    }

    // Sorting - Default is exact file order (1 to 166)
    if (sortBy === "file_order") {
      items.sort((a, b) => (a.file_order || 0) - (b.file_order || 0));
    } else if (sortBy === "quantity_desc") {
      items.sort((a, b) => (b.quantity || 0) - (a.quantity || 0) || (a.file_order - b.file_order));
    } else if (sortBy === "quantity_asc") {
      items.sort((a, b) => (a.quantity || 0) - (b.quantity || 0) || (a.file_order - b.file_order));
    } else if (sortBy === "diff_desc") {
      items.sort((a, b) => (b.diff_from_target || 0) - (a.diff_from_target || 0));
    } else if (sortBy === "royal_price_desc") {
      items.sort((a, b) => (b.royaldigi_price || 0) - (a.royaldigi_price || 0));
    } else if (sortBy === "royal_price_asc") {
      items.sort((a, b) => (a.royaldigi_price || 0) - (b.royaldigi_price || 0));
    }

    return {
      items,
      total: items.length,
      metadata: staticData.metadata || {},
    };
  }

  // Fallback to API if backend server is ever running
  try {
    const params = {};
    if (q) params.q = q;
    const res = await client.get("/api/products", { params });
    return res.data;
  } catch (err) {
    return { items: [], total: 0, metadata: {} };
  }
}

export async function fetchStats() {
  const staticData = await loadStaticData();
  if (staticData && staticData.metadata) {
    return staticData.metadata;
  }
  return {};
}

export async function fetchProduct(id) {
  const staticData = await loadStaticData();
  if (staticData && staticData.items) {
    const item = staticData.items.find(
      (p) => String(p.id) === String(id) || String(p.woo_id) === String(id) || String(p.file_order) === String(id)
    );
    if (item) return item;
  }
  return null;
}

export async function fetchHistory(id) {
  const p = await fetchProduct(id);
  if (p && p.sparkline) {
    return p.sparkline.map((val, idx) => ({
      price: val,
      created_at: new Date(Date.now() - (4 - idx) * 86400000).toISOString(),
    }));
  }
  return [];
}

export async function fetchShops(id) {
  const p = await fetchProduct(id);
  if (p) {
    const shops = [];
    shops.push({
      shop_name: "رویال‌دیجی (سایت ما)",
      price: p.royaldigi_price,
      url: p.royaldigi_url,
      is_available: !!p.royaldigi_price,
    });
    shops.push({
      shop_name: "ترب · رتبه ۱ (فروشنده اول)",
      price: p.torob_1,
      url: p.torob_url,
      is_available: !!p.torob_1,
    });
    shops.push({
      shop_name: "ترب · رتبه ۲ (فروشنده دوم)",
      price: p.torob_2,
      url: p.torob_url,
      is_available: !!p.torob_2,
    });
    shops.push({
      shop_name: "ترب · رتبه ۳ (فروشنده سوم)",
      price: p.torob_3,
      url: p.torob_url,
      is_available: !!p.torob_3,
    });
    shops.push({
      shop_name: "دیجی‌کالا",
      price: p.digikala_price,
      url: p.digikala_url,
      is_available: !!p.digikala_price,
    });
    return shops;
  }
  return [];
}
