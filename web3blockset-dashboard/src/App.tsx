import { HashRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import DashboardPage from "./pages/DashboardPage";
import FilterPage from "./pages/FilterPage";
import ResearchInsightsPage from "./pages/ResearchInsightsPage";

export default function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="filter" element={<FilterPage />} />
          <Route path="research" element={<ResearchInsightsPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}
