import axios from "axios";

// In Docker, the frontend is served statically and talks to the backend
// via this base URL (set at build time). Locally with `npm run dev`,
// Vite's default is fine as long as VITE_API_URL is set in frontend/.env.
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL, timeout: 15000 });

export async function fetchProducts({ q, category, limit = 200, offset = 0 } = {}) {
  const { data } = await client.get("/products", { params: { q, category, limit, offset } });
  return data;
}

export async function fetchProduct(id) {
  const { data } = await client.get(`/products/${id}`);
  return data;
}

export async function fetchHistory(id) {
  const { data } = await client.get(`/history/${id}`);
  return data;
}

export async function fetchShops(id) {
  const { data } = await client.get(`/shops/${id}`);
  return data;
}

export default client;
