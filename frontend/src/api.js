import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const client = axios.create({ baseURL: API_URL, timeout: 15000 });

let cachedData = null;

async function loadStaticData() {
  if (cachedData) return cachedData;
  
  // Try candidate URLs for products_data.json
  const candidates = [
    "./data/products_data.json",
    "data/products_data.json",
    "/data/products_data.json",
    "/price-monitor/data/products_data.json", // Common for GitHub Pages repo name
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

export async function fetchProducts({ q, category, status, sortBy = "default" } = {}) {
  const staticData = await loadStaticData();
  if (staticData && staticData.items) {
    let items = [...staticData.items];

    // Filter by category (new / stock)
    if (category && category !== "all") {
      items = items.filter((p) => p.category === category);
    }

    // Filter by status (increased, decreased, unchanged, out_of_stock)
    if (status && status !== "all") {
      if (status === "changed") {
        items = items.filter((p) => p.status === "increased" || p.status === "decreased");
      } else {
        items = items.filter((p) => p.status === status);
      }
    }

    // Search query
    if (q && q.trim()) {
      const query = q.trim().toLowerCase();
      items = items.filter((p) =>
        (p.name && p.name.toLowerCase().includes(query)) ||
        (p.warehouse_title && p.warehouse_title.toLowerCase().includes(query)) ||
        (p.category_fa && p.category_fa.toLowerCase().includes(query))
      );
    }

    // Sorting
    if (sortBy === "change_desc") {
      items.sort((a, b) => (b.price_change_percent || 0) - (a.price_change_percent || 0));
    } else if (sortBy === "change_asc") {
      items.sort((a, b) => (a.price_change_percent || 0) - (b.price_change_percent || 0));
    } else if (sortBy === "price_desc") {
      items.sort((a, b) => (b.best_current_price || 0) - (a.best_current_price || 0));
    } else if (sortBy === "price_asc") {
      items.sort((a, b) => (a.best_current_price || 999999999) - (b.best_current_price || 999999999));
    }

    return {
      items,
      total: items.length,
      metadata: staticData.metadata || {},
    };
  }

  // Fallback to FastAPI backend if static data is not present
  try {
    const { data } = await client.get("/products", { params: { q, category } });
    return data;
  } catch (err) {
    throw new Error("داده‌های محصولات یافت نشد.");
  }
}

export async function fetchProduct(id) {
  const staticData = await loadStaticData();
  if (staticData && staticData.items) {
    const found = staticData.items.find(
      (p) => String(p.id) === String(id) || String(p.row_index) === String(id)
    );
    if (found) return found;
  }

  const { data } = await client.get(`/products/${id}`);
  return data;
}

export async function fetchHistory(id) {
  const staticData = await loadStaticData();
  if (staticData && staticData.items) {
    const found = staticData.items.find(
      (p) => String(p.id) === String(id) || String(p.row_index) === String(id)
    );
    if (found && found.history) {
      return found.history.map((h, idx) => ({
        id: idx,
        created_at: h.timestamp,
        price: h.digikala_price || h.torob_price || 0,
        store: { name: h.digikala_price ? "دیجی‌کالا" : "ترب" },
      }));
    }
    return [];
  }

  const { data } = await client.get(`/history/${id}`);
  return data;
}

export async function fetchShops(id) {
  const staticData = await loadStaticData();
  if (staticData && staticData.items) {
    const found = staticData.items.find(
      (p) => String(p.id) === String(id) || String(p.row_index) === String(id)
    );
    if (found) {
      const shops = [];
      let sId = 1;
      if (found.current_digikala_price) {
        shops.push({
          id: sId++,
          store: { name: found.digikala_seller || "دیجی‌کالا" },
          price: found.current_digikala_price,
          is_available: found.digikala_available,
          url: found.digikala_url,
          checked_at: found.last_checked,
        });
      }
      if (found.digikala_offers) {
        found.digikala_offers.forEach((o) => {
          if (o.seller !== found.digikala_seller) {
            shops.push({
              id: sId++,
              store: { name: `دیجی‌کالا: ${o.seller}` },
              price: o.price,
              is_available: true,
              url: found.digikala_url,
              checked_at: found.last_checked,
            });
          }
        });
      }
      if (found.current_torob_price) {
        shops.push({
          id: sId++,
          store: { name: "ترب (ارزان‌ترین)" },
          price: found.current_torob_price,
          is_available: found.torob_available,
          url: found.torob_url,
          checked_at: found.last_checked,
        });
      }
      if (found.torob_offers) {
        found.torob_offers.forEach((o) => {
          shops.push({
            id: sId++,
            store: { name: `ترب: ${o.seller}` },
            price: o.price,
            is_available: true,
            url: o.url || found.torob_url,
            checked_at: found.last_checked,
          });
        });
      }
      return shops;
    }
  }

  const { data } = await client.get(`/shops/${id}`);
  return data;
}

export default client;
