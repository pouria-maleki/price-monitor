import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import ProductsTable from "./components/ProductsTable.jsx";
import ProductDetail from "./components/ProductDetail.jsx";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<ProductsTable />} />
        <Route path="/products/:id" element={<ProductDetail />} />
      </Routes>
    </Layout>
  );
}
